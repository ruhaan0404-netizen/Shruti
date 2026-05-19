from __future__ import annotations
from typing import Any
from .state import JarvisState

MAX_SHORT_TERM_ITEMS = 8

def append_execution_log(state: JarvisState, message: str) -> None:
    execution_log = list(state.get("execution_log", []))
    execution_log.append(message)
    state["execution_log"] = execution_log

def update_short_term_memory(state: JarvisState, item: dict[str, Any]) -> None:
    memory = list(state.get("short_term_memory", []))
    memory.append(item)
    state["short_term_memory"] = memory[-MAX_SHORT_TERM_ITEMS:]

def summarize_long_term_memory(state: JarvisState) -> None:
    """
    Lightweight summary builder.
    In production, this can be replaced with an LLM summarizer.
    """
    memory = state.get("short_term_memory", [])
    if not memory:
        state["long_term_summary"] = "No long-term context yet."
        return

    latest_actions = [f"- {m.get('type', 'event')}: {m.get('content', '')}" for m in memory[-3:]]
    state["long_term_summary"] = "Recent important context:\n" + "\n".join(latest_actions)

def build_context_for_reasoning(state: JarvisState) -> str:
    recent_user_turns = [
        entry["content"]
        for entry in state.get("messages", [])
        if entry.get("role") == "user"
    ][-3:]

    long_term = state.get("long_term_summary", "No long-term context yet.")
    recent = " | ".join(recent_user_turns) if recent_user_turns else "No recent user turns."
    return f"Recent user turns: {recent}\nMemory summary: {long_term}"
