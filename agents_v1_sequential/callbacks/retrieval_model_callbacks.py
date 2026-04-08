"""retrieval_agent 모델 출력을 retrieval_context JSON으로 통일하는 콜백."""

import json
from typing import Any

from google.genai import types


def _state(ctx: Any) -> dict:
    s = getattr(ctx, "state", None)
    if s is None:
        return {}
    try:
        return s.to_dict() if hasattr(s, "to_dict") else (s if isinstance(s, dict) else dict(s))
    except Exception:
        return {}


def _state_to_str(state_dict: dict, chunk_content_len: int = 50, max_len: int = 8000) -> str:
    """state를 JSON으로 직렬화. retrieval_results 각 청크의 content는 chunk_content_len자로 축약."""
    if not state_dict:
        return "{}"

    def _truncate_chunks(obj: Any) -> Any:
        if isinstance(obj, dict):
            if "retrieval_results" in obj:
                results = obj.get("retrieval_results", [])
                return {
                    **{k: _truncate_chunks(v) for k, v in obj.items() if k != "retrieval_results"},
                    "retrieval_results": [
                        {
                            **r,
                            "content": (c := str(r.get("content", "")))[:chunk_content_len]
                            + ("..." if len(c) > chunk_content_len else ""),
                        }
                        for r in results
                    ],
                }
            return {k: _truncate_chunks(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_truncate_chunks(x) for x in obj]
        return obj

    prepped = _truncate_chunks(state_dict)

    try:
        s = json.dumps(prepped, ensure_ascii=False, default=str, indent=2)
        return s[:max_len] + "\n... (truncated)" if len(s) > max_len else s
    except Exception:
        return str(prepped)[:max_len]


def retrieval_replace_model_output_with_retrieval_json(
    callback_context: Any, llm_response: Any
) -> Any:
    """도구로 채운 retrieval_context를 JSON 문자열로 바꿔 청크/풀텍스트 출력을 통일한다."""
    if getattr(callback_context, "agent_name", "") != "retrieval_agent":
        return None
    if getattr(llm_response, "partial", False) is True:
        return None
    content = getattr(llm_response, "content", None)
    if content is None:
        return None
    parts = getattr(content, "parts", None) or []
    if not parts:
        return None
    for p in parts:
        if getattr(p, "function_call", None) or getattr(p, "function_response", None):
            return None
    if not any(getattr(p, "text", None) for p in parts):
        return None
    state_dict = _state(callback_context)
    rc = state_dict.get("retrieval_context")
    if not isinstance(rc, dict):
        return None
    text = _state_to_str({"retrieval_context": rc})
    new_content = types.Content(parts=[types.Part(text=text)])
    return llm_response.model_copy(update={"content": new_content})
