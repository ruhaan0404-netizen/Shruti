from typing import TypedDict, List, Annotated, Union, Any
from pydantic import BaseModel, Field
from langchain.messages import ToolMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages

Message = Union[HumanMessage, AIMessage, ToolMessage, SystemMessage]

# Define a custom reducer function
def manage_list(existing: List[Any], new: Union[List[Any], Any, str]):
    if new == "cls": # Command clears the messages
        return []
    if not new: # If nothing to add
        return existing
    if isinstance(new, list): # If new is a list
        return existing + new
    return existing + [new] # If new is a single message

# Define a single task for a sub-agent
class Task(BaseModel):
    target_agent: str = Field(description="The agent to route to: 'Calendar', 'Email', or 'Codeforces'")
    instruction: str = Field(description="What the agent needs to do")

# Batch of tasks that can run at the same time(parallel execution)
class TaskBatch(BaseModel):
    batch_id: int
    tasks: List[Task] = Field(description="Tasks in this batch. They will run concurrently.")

# The LangGraph Agent State
class AgentState(TypedDict):
    messages: Annotated[list[Message], add_messages]
    summary:HumanMessage
    plan: TaskBatch
    current_batch_index: int
    task_results: Annotated[list[Message], manage_list]