from typing import Any, Literal, TypedDict

AgentPhase = Literal["listening", "reasoning", "planning", "executing", "responding", "done"]

class JarvisState(TypedDict, total=False):
    """Shared state that moves through LangGraph nodes."""
    user_input: str
    intent: str
    messages: list[dict[str, str]]
    plan: list[dict[str, str]]
    current_step: int
    tool_result: str
    response: str
    short_term_memory: list[dict[str, Any]]
    long_term_summary: str
    execution_log: list[str]
    phase: AgentPhase
