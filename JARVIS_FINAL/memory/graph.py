from .nodes import execute_node, plan_node, reason_node, respond_node
from .state import JarvisState
from langgraph.graph import END, START, StateGraph

def _should_continue_executing(state: JarvisState) -> str:
    plan = state.get("plan", [])
    step = state.get("current_step", 0)
    return "execute_more" if step < len(plan) else "respond"

def _build_with_langgraph():

    graph = StateGraph(JarvisState)
    graph.add_node("reason", reason_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("respond", respond_node)

    graph.add_edge(START, "reason")
    graph.add_edge("reason", "plan")
    graph.add_edge("plan", "execute")
    graph.add_conditional_edges(
        "execute",
        _should_continue_executing,
        {
            "execute_more": "execute",
            "respond": "respond",
        },
    )
    graph.add_edge("respond", END)
    return graph.compile()

class _FallbackCompiledGraph:
    """Minimal local executor used only when LangGraph is unavailable."""
    def invoke(self, state: JarvisState) -> JarvisState:
        state = reason_node(state)
        state = plan_node(state)
        while True:
            state = execute_node(state)
            if _should_continue_executing(state) == "respond":
                break
        state = respond_node(state)
        return state

def build_graph():
    try:
        return _build_with_langgraph()
    except Exception as e:
        print(f"Failed to build LangGraph ({e}), falling back to local executor.")
        return _FallbackCompiledGraph()
