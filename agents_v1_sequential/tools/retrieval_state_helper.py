"""검색 도구가 session state에 retrieval_context를 직접 반영할 때 사용한다."""

from __future__ import annotations

from typing import Any

from google.adk.tools.tool_context import ToolContext


def commit_retrieval_context_to_state(tool_context: ToolContext, response: dict[str, Any]) -> None:
    """도구 반환값과 동일한 내용을 state['retrieval_context']에 넣는다(LLM 재구성과 무관)."""
    rt = response.get("retrieval_type")
    payload: dict[str, Any] = {
        "query": str(response.get("query", "")),
        "categories": list(response.get("categories", [])),
        "retrieval_results": list(response.get("retrieval_results", [])),
        "retrieval_total_size": int(response.get("retrieval_total_size", 0)),
        "retrieval_type": rt,
    }
    tool_context.state["retrieval_context"] = payload
