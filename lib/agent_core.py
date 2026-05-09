import os
from tools import calendar_tool as cl
from tools import email_tool as em
from tools import web_scraping as wb
from typing import TypedDict, Annotated, Sequence
from langchain_google_genai import ChatGoogleGenerativeAI as genai
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

load_dotenv()

cal_tools = cl.Calendar_tools
e_tools = em.Email_tools
wb_tools = wb.Web_tools

Tools = [*cal_tools,*e_tools,*wb_tools]

llm = genai(
        api_key=os.getenv("GENAI_API_KEY"),
        model="gemini-2.5-flash",
        temperature=0
        )
llm_with_tools = llm.bind_tools(Tools)

class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage], add_messages]

# _____NODES_____ #
def ask_anything(state:AgentState)->AgentState:
    if not state["messages"]:
        user = HumanMessage(content=input("How can I help you, Sir?"))
    else:
        user = HumanMessage(content=input())
    state['messages'].append(user)
    return state

def reason_plan(state:AgentState)->AgentState:
    global llm_with_tools
    system_prompt=SystemMessage(
        content=("System: You are an Agentic AI modal with calendar management, email management and web scrapping capabilities."
        "You are task is to listen, reason, plan and execute all the tasks assigned by the user."
        "Also you have great reasoning capabilities like when asked about an annual event where no information about the start and"
        " the end dates are given, you assume start date as now and the end date as the date one year after today."
        "You can answer all the questions on your own which do not require tool calling."
        "When asked to compose an email message or draft, create the body of the email using email_content_cretion function."
        "Once the body content of the email is generaated, use other functions to save or send the draft."
        "After completing a task out of all the tasks assigned to you, address the user."
        f"The current date and time is {datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()}")
    )
    all_messages = [system_prompt,*state['messages']]
    response = llm_with_tools.invoke(all_messages)
    state['messages'].append(response)
    return state

tool_node = ToolNode(tools=Tools)

def should_continue(state:AgentState):
    """Determine if we have more work to do or should end the conversation."""
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        print(last_message.text)
        return "end"
    else:
        return "continue"

# _____GRAPH STRUCTURE______ #
graph = StateGraph(AgentState)
graph.add_node("senses",ask_anything)
graph.add_node("brain",reason_plan)
graph.add_node("tools",tool_node)
graph.set_entry_point("senses")
graph.add_edge("senses","brain")
graph.add_conditional_edges(
    "brain",
    should_continue,
    {
        "continue": "tools",
        "end": "senses"
    }
)
graph.add_edge("tools","brain")
app = graph.compile()


# ______LOOP_ENGINE______ #
state = {"messages":[]}

for full_state in app.stream(state, stream_mode="values"):
    print(f"Total messages so far: {len(full_state['messages'])}")