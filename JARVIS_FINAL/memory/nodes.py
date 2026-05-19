from __future__ import annotations
import sys
import os
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from load_dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .memory import (
    append_execution_log,
    build_context_for_reasoning,
    summarize_long_term_memory,
    update_short_term_memory,
)
from .state import JarvisState

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.vision import vision_tool_controller

load_dotenv()

# --- 1. LLM Setup ---
class Step(BaseModel):
    action: str = Field(description="The tool to use: 'capture_screen', 'capture_webcam', 'open_app_or_site', or 'answer_directly'")
    target: str = Field(description="The specific target. CRITICAL: If action is 'answer_directly', the target MUST be the user's exact original request string.")

class Plan(BaseModel):
    steps: list[Step] = Field(description="The sequence of steps needed to fulfill the user's request.")

llm = ChatGroq(
    model="llama-3.1-8b-instant", 
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

planner_llm = llm.with_structured_output(Plan)

# --- 2. Tool Execution ---
def _real_tool_executor(action: str, target: str, state: JarvisState) -> str:
    """
    Real tool runner integrating vision capabilities and live LLM responses.
    """
    if action == "capture_screen":
        return vision_tool_controller("screen")
        
    elif action == "capture_webcam":
        return vision_tool_controller("webcam")
        
    elif action == "open_app_or_site":
        return f"Simulated opening of: {target}"
        
    elif action == "answer_directly":
        try:
            messages = [
                SystemMessage(
                    content=(
                        "You are Jarvis, a sleek and highly sophisticated AI assistant. "
                        "Provide a direct, natural, and conversational answer to the user's request. "
                        "CRITICAL RULE: Do NOT include formal introductory fluff, greetings, or phrases like "
                        "'Hello, I am Jarvis', 'Good day, sir', or 'How can I help you' unless explicitly asked. "
                        "Just fulfill the request directly."
                    )
                )
            ]
            for msg in state.get("messages", []):
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            if not messages or messages[-1].content != target:
                messages.append(HumanMessage(content=target))
            chat_completion = llm.invoke(messages)
            return chat_completion.content    
        except Exception as e:
            return f"Error generating answer: {e}"
        
    return f"Executed action='{action}' on target='{target}'"
# --- 3. Graph Nodes ---
def reason_node(state: JarvisState) -> JarvisState:
    """Gathers context before planning."""
    state["phase"] = "reasoning"
    context = build_context_for_reasoning(state)
    append_execution_log(state, "[reasoning] Context gathered.")
    return state

def plan_node(state: JarvisState) -> JarvisState:
    state["phase"] = "planning"
    user_input = state.get("user_input", "")
    state["tool_result"] = ""
    memory_context = build_context_for_reasoning(state)
    system_prompt = f"""You are Jarvis, a highly intelligent AI assistant. 
    
    CONVERSATIONAL HISTORY & CONTEXT:
    {memory_context}
    
    Analyze this new user request: '{user_input}'
    
    Choose the correct action based on these strict rules:
    - If the user explicitly asks you to look at their screen or read something on their monitor, use 'capture_screen'.
    - If the user asks you to look at them via camera, use 'capture_webcam'.
    - If the user asks you to open a website or application, use 'open_app_or_site'.
    - For ALL OTHER general questions, math, logic, poems, or chatting, you MUST use 'answer_directly'.
    
    CRITICAL: For 'answer_directly', set the target to the exact request: '{user_input}'.
    """
    
    try:
        generated_plan = planner_llm.invoke(system_prompt)
        
        final_steps = []
        for step in generated_plan.steps:
            step_dict = step.model_dump()
            if step_dict["action"] == "answer_directly":
                step_dict["target"] = user_input
            final_steps.append(step_dict)
            
        state["plan"] = final_steps
        
    except Exception as e:
        print(f"Planning Execution Error: {e}")
        state["plan"] = [{"action": "answer_directly", "target": user_input}]

    state["current_step"] = 0
    append_execution_log(state, f"[planning] Created {len(state['plan'])} steps.")
    return state


def execute_node(state: JarvisState) -> JarvisState:
    state["phase"] = "executing"
    plan = state.get("plan", [])
    current = state.get("current_step", 0)

    if current >= len(plan):
        state["tool_result"] = state.get("tool_result", "No steps left to execute.")
        append_execution_log(state, "[executing] no-op, plan already completed")
        return state

    step = plan[current]
    result = _real_tool_executor(step["action"], step["target"], state)
    
    existing_result = state.get("tool_result", "")
    if existing_result:
        state["tool_result"] = existing_result + "\n" + result
    else:
        state["tool_result"] = result
        
    state["current_step"] = current + 1

    append_execution_log(state, f"[executing] step={current}/{len(plan)} result={result[:50]}...")
    update_short_term_memory(state, {"type": "execution", "content": result})
    return state

def respond_node(state: JarvisState) -> JarvisState:
    state["phase"] = "responding"
    result = state.get("tool_result", "No result generated.")
    plan = state.get("plan", [])
    
    primary_action = plan[0]["action"] if plan else "answer_directly"

    if primary_action in ["capture_screen", "capture_webcam"]:
        state["response"] = f"Here is what I see: {result}"
    elif primary_action == "answer_directly":
        state["response"] = f"{result}"
    else:
        state["response"] = f"Completed action. Result: {result}"

    messages = list(state.get("messages", []))
    if state.get("user_input"):
        messages.append({"role": "user", "content": state["user_input"]})
    messages.append({"role": "assistant", "content": state["response"]})
    state["messages"] = messages

    update_short_term_memory(state, {"type": "response", "content": state["response"]})
    summarize_long_term_memory(state)
    append_execution_log(state, "[responding] response generated and memory updated")
    state["phase"] = "done"
    return state