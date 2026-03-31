"""Vertex AI Search spell correction 결과를 state에 저장하는 콜백."""

from typing import Any, Optional

STATE_KEY = "vertexai_search_corrected_query"


def save_corrected_query_after_tool(
    tool: Any,
    args: dict[str, Any],
    tool_context: Any,
    tool_response: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """tool_response에 corrected_query가 있으면 state에 저장한다."""
    corrected_query = tool_response.get("corrected_query")
    state = getattr(tool_context, "state", None)
    agent_name = getattr(tool_context, "agent_name", "") or "retrieval_agent"
    if isinstance(corrected_query, str) and corrected_query.strip():
        if isinstance(state, dict):
            agent_name = agent_name.strip()
            if agent_name:
                namespace = state.get(agent_name)
                if not isinstance(namespace, dict):
                    namespace = {}
                    state[agent_name] = namespace
                namespace[STATE_KEY] = corrected_query.strip()
    return tool_response

