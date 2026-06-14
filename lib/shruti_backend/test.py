from agent_core import agent_exe_graph
from langchain.messages import HumanMessage

user_input = input("Mike testing 123")
graph_inputs = {"messages": [HumanMessage(content=user_input)],"current_batch_index": 0}
graph_config = {"configurable": {"thread_id": "voice_session_001"}}

final_state = agent_exe_graph.invoke(graph_inputs,config=graph_config)

print(final_state["messages"][-1])