from langgraph.graph import StateGraph, START, END
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from agentstate import AgentState, Task, TaskBatch
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from prompt import  SUPERVISOR_PROMPT, CALENDAR_AGENT_PROMPT, EMAIL_AGENT_PROMPT, CODEFORCES_AGENT_PROMPT, GENERAL_AGENT_PROMPT
from tools.calendar_tool import CALENDAR_TOOLS
from tools.email_tool import EMAIL_TOOLS
from tools.codeforces_tool import CODEFORCES_TOOLS
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END
from langgraph.types import Send

load_dotenv() # Load the environment variables(API keys, other parameters)

# ----------------------------------------------------- #
# Use gemini for tool calling and subagent execution
model = init_chat_model("gemini-2.5-flash",model_provider="google_genai", temperature=0.7) # Initialising the subagent model.

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
    system_prompt=GENERAL_AGENT_PROMPT
)
# ------------------------------------------------------ #
# Mend the supervisor agent using groq for speed and efficiency
supervisor_model = init_chat_model("meta-llama/llama-4-scout-17b-16e-instruct", model_provider="groq", temperature=0.7)
# Force llm to output strictly in the ExeccutionPlan format
supervisor_agent = supervisor_model.with_structured_output(TaskBatch) 

# ------------------------------------------------------ #
# Nodes of the graph
def supervisor_node(state: AgentState):
    print(f"Batch Index: {state['current_batch_index']}")
    system_msg = SystemMessage(content=SUPERVISOR_PROMPT)
    if state["current_batch_index"] == 0:
        messages_for_supervisor = [system_msg] + state["messages"]
    else:
        messages_for_supervisor = [system_msg] + state["messages"] + state.get("task_results", [])
    plan: TaskBatch = supervisor_agent.invoke(messages_for_supervisor)
    print(plan)
    if not plan.tasks:
        return {"plan": plan} 
    if plan.tasks[0].target_agent == "End":
        task_results = state.get("task_results", [])
        if task_results:
            final_response = task_results[-1]
        else:
            final_response = HumanMessage(content="No tasks were executed, workflow ended.")
        return{
            "plan": plan, 
            "messages": [final_response],
            "current_batch_index": state["current_batch_index"] + 1
        }
    else:
        return{
            "plan": plan, 
            "task_results": "cls",
            "current_batch_index": state["current_batch_index"] + 1
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
        content=f"Report from {task.target_agent} Agent:{final_agent_response}",
        name=task.target_agent
    )
    AI_command:str = AIMessage(
        content=f"Task given to {task.target_agent} Task:{task.instruction}",
        name="Supervisor Agent"
    )
    return {
        "messages": [AI_command],
        "task_results": [report_message]
    }
# ----------------------------------------------------- #
# Build the graph
graph = StateGraph(AgentState)

graph.add_node("Supervisor",supervisor_node)
graph.add_node("Worker",worker_node)
# ------------------------------------------------------ #
# Edges of the graph
graph.add_edge(START,"Supervisor")
graph.add_conditional_edges("Supervisor",router_node)
graph.add_edge("Worker","Supervisor")
# ------------------------------------------------------ #
# Compiled graph
serializer = JsonPlusSerializer(allowed_msgpack_modules='messages')
memory = MemorySaver(serde=serializer) # Saves state to RAM
agent_exe_graph = graph.compile(checkpointer=memory)