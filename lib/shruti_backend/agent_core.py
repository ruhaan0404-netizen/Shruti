from langgraph.graph import StateGraph, START, END
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from agentstate import AgentState, Task, TaskBatch
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langchain.messages import RemoveMessage
from prompt import SUPERVISOR_PROMPT, CALENDAR_AGENT_PROMPT, EMAIL_AGENT_PROMPT, CODEFORCES_AGENT_PROMPT, GENERAL_AGENT_PROMPT,SUMMARY_AGENT_PROMPT
from tools.calendar_tool import CALENDAR_TOOLS
from tools.email_tool import EMAIL_TOOLS
from tools.codeforces_tool import CODEFORCES_TOOLS
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send

load_dotenv() # Load the environment variables(API keys, other parameters)

@tool
def tell_the_user(response:str):
    """This function helps you address the user.Pass your reply as the argument response to the user."""
    from interact import speak_response
    import asyncio
    asyncio.run(speak_response(response))
    return "Successfully addressed the user."

@tool
def ask_the_user(question: str) -> str:
    """
    Call this tool when you are missing critical information to draft an email 
    (e.g., recipient email address, subject line, or specific content details).
    """
    import asyncio
    import io
    import numpy as np
    from scipy.io import wavfile
    import interact 

    # 1. Update UI and Speak (Synchronous wrapper)
    try:
        if interact.MAIN_LOOP:
            asyncio.run_coroutine_threadsafe(
                interact.broadcast_state("asking_user", question, draft_text=""), 
                interact.MAIN_LOOP
            )
        asyncio.run(interact.speak_response(question))
    except Exception as e:
        print(f"⚠️ UI/Speech Error: {e}")

    # 2. Listen via Microphone
    print(f"\n[Agent]: {question}")
    interact.listen()
    # 3. Process Audio with Whisper
    if interact.audio_buffer:
        final_audio = np.concatenate(interact.audio_buffer, axis=0).flatten()
        virtual_file = io.BytesIO()
        wavfile.write(virtual_file, interact.SAMPLE_RATE, final_audio)
        virtual_file.seek(0)
        try:
            transcription = interact.client.audio.transcriptions.create(
                file=("audio.wav", virtual_file.read()), 
                model="whisper-large-v3",
                response_format="text",
                temperature=0.0
            )
            return transcription.strip()
        except Exception as e:
            return f"System Error: User spoke, but transcription failed ({e}). Ask them to repeat."
            
    return "System Error: No audio detected. Please ask the user again."


# ----------------------------------------------------- #
# Use gemini for tool calling and subagent execution
model = init_chat_model("meta-llama/llama-4-scout-17b-16e-instruct", model_provider="groq", temperature=0.7) # Initialising the subagent model.

# One subagent model handles multiple tasks concurrently
calendar_agent = create_agent(
    model,
    tools=CALENDAR_TOOLS,
    system_prompt=CALENDAR_AGENT_PROMPT,
)

email_agent = create_agent(
    model,
    tools=EMAIL_TOOLS,
    system_prompt=EMAIL_AGENT_PROMPT,
)

codeforces_agent = create_agent(
    model,
    tools=CODEFORCES_TOOLS,
    system_prompt=CODEFORCES_AGENT_PROMPT
)

general_agent = create_agent(
    model,
    tools=[tell_the_user,ask_the_user],
    system_prompt=GENERAL_AGENT_PROMPT
)

summary_agent = create_agent(
    model,
    system_prompt=SUMMARY_AGENT_PROMPT
)
# ------------------------------------------------------ #
# Mend the supervisor agent using groq for speed and efficiency
supervisor_model = init_chat_model("openai/gpt-oss-120b", model_provider="groq", temperature=0.7)
# Force llm to output strictly in the ExeccutionPlan format
supervisor_agent = supervisor_model.with_structured_output(TaskBatch) 
# ------------------------------------------------------ #
# Nodes of the graph
def prune_node(state: AgentState):
    if len(state["messages"])>10:
        old_messages = state["messages"][:-10]
        sum_msg = [state["summary"]]+old_messages
        response = summary_agent.invoke({"messages":sum_msg})
        sum = response["messages"][-1].content
        summary = HumanMessage(content=f"Here's a summary of the previous chats:-\n{sum}")
        delete_instructions = [RemoveMessage(id=msg.id) for msg in old_messages]
        return {
            "summary":summary,
            "messages": delete_instructions}
    else:
        return {"summary":HumanMessage(content="No previous chats.")}

def supervisor_node(state: AgentState):
    current_index = state.get("current_batch_index", 0)
    print(f"Batch Index: {current_index}")
    memory_directive = (
        "CRITICAL DIRECTIVE: Read the message history carefully. "
        "If a worker agent just reported that they successfully completed a task "
        "(e.g., 'Draft created successfully'), DO NOT assign that exact task again. "
        "If the user's overall goal is met, your next target_agent MUST be 'End'."
    )
    system_msg = SystemMessage(content=SUPERVISOR_PROMPT + memory_directive)
    summary = state["summary"]
    messages_for_supervisor = [system_msg,summary] + state["messages"]

    print(state["messages"])

    plan: TaskBatch = supervisor_agent.invoke(messages_for_supervisor)
    print(f"Supervisor Plan: {plan}")
    if not plan or not plan.tasks or plan.tasks[0].target_agent == "End":
        task_results = state.get("task_results", [])
        final_response = task_results[-1] if task_results else HumanMessage(content="Workflow ended.")
        return {
            "plan": plan, 
            "messages": [final_response],
            "task_results": [], 
            "current_batch_index": current_index + 1
        }
    else:
        return {
            "plan": plan, 
            "task_results": [], 
            "current_batch_index": current_index + 1
        }

def router_node(state: AgentState):
    plan = state.get("plan")
    if not plan or not plan.tasks or plan.tasks[0].target_agent == "End":
        return END
    return [Send("Worker", task) for task in plan.tasks]

def worker_node(task: Task):
    if task.target_agent == "Calendar":
        result = calendar_agent.invoke({"messages": [("user", task.instruction)]})
    elif task.target_agent == "Email":
        result = email_agent.invoke({"messages": [("user", task.instruction)]})
    elif task.target_agent == "Codeforces":
        result = codeforces_agent.invoke({"messages": [("user", task.instruction)]})
    else:
        result = general_agent.invoke({"messages": [("user", task.instruction)]})
    final_agent_response = result['messages'][-1].content
    report_message = HumanMessage(
        content=f"Report from {task.target_agent} Agent: {final_agent_response}",
        name=task.target_agent
    )
    AI_command = AIMessage(
        content=f"Task given to {task.target_agent} Task: {task.instruction}",
        name="Supervisor"
    )
    
    return {
        # Appending both to 'messages' gives the supervisor permanent memory of the action
        "messages": [AI_command, report_message],
        "task_results": [report_message]
    }
# ----------------------------------------------------- #
# Build the graph
graph = StateGraph(AgentState)

graph.add_node("Supervisor",supervisor_node)
graph.add_node("Worker",worker_node)
graph.add_node("Summarizer",prune_node)
# ------------------------------------------------------ #
# Edges of the graph
graph.add_edge(START,"Summarizer")
graph.add_edge("Summarizer","Supervisor")
graph.add_conditional_edges("Supervisor",router_node)
graph.add_edge("Worker","Summarizer")
# ------------------------------------------------------ #
# Compiled graph
serializer = JsonPlusSerializer(allowed_msgpack_modules='messages')
memory = MemorySaver(serde=serializer) # Saves state to RAM
agent_exe_graph = graph.compile(checkpointer=memory)