"""ADK agent/model/tool 전체 플로우 로깅을 위한 공통 콜백."""

import json
from typing import Any, Optional

from google.genai import types

from config.custom_log import get_logger
from config.properties import Settings

logger = get_logger(__name__)
settings = Settings()


def _to_str(obj: Any, max_len: int = 1500) -> str:
    """객체를 문자열로 변환 (최대 max_len자)."""
    if obj is None:
        return "null"
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
        return s[:max_len] + "..." if len(s) > max_len else s
    except Exception:
        return str(obj)[:max_len]


def _model_name(obj: Any) -> str:
    """LLM 모델명 추출."""
    if obj is None:
        return "N/A"
    m = getattr(obj, "model", None) or (obj.get("model") if isinstance(obj, dict) else None)
    if m is not None:
        return str(m)
    cfg = getattr(obj, "config", None)
    m = getattr(cfg, "model", None) if cfg else None
    return str(m) if m else "N/A"


def _state(ctx: Any) -> dict:
    """Context에서 state dict 추출."""
    s = getattr(ctx, "state", None)
    if s is None:
        return {}
    try:
        return s.to_dict() if hasattr(s, "to_dict") else (s if isinstance(s, dict) else dict(s))
    except Exception:
        return {}


def _ensure_original_user_query(ctx: Any) -> None:
    """state에 original_user_query가 없으면 가능한 키에서 채워 넣는다."""
    state = getattr(ctx, "state", None)
    if state is None or not hasattr(state, "__setitem__"):
        return
    existing = state.get("original_user_query") if hasattr(state, "get") else None
    if isinstance(existing, str) and existing.strip():
        return

    def _content_to_text(content: Any) -> str:
        if content is None:
            return ""
        parts = getattr(content, "parts", None)
        if not parts:
            return ""
        texts: list[str] = []
        for part in parts:
            text = getattr(part, "text", None)
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
        return "\n".join(texts).strip()

    # ADK 1.27+: 이번 invocation을 시작한 사용자 입력은 ctx.user_content에 존재
    from_user_content = _content_to_text(getattr(ctx, "user_content", None))
    if from_user_content:
        state["original_user_query"] = from_user_content
        agent_name = str(getattr(ctx, "agent_name", "") or "").strip()
        if agent_name:
            namespace = state.get(agent_name) if hasattr(state, "get") else None
            if not isinstance(namespace, dict):
                namespace = {}
                state[agent_name] = namespace
            namespace["original_user_query"] = from_user_content
        return

    candidates = [
        state.get("user_query") if hasattr(state, "get") else None,
        state.get("query") if hasattr(state, "get") else None,
        state.get("input") if hasattr(state, "get") else None,
        state.get("question") if hasattr(state, "get") else None,
    ]
    for cand in candidates:
        if isinstance(cand, str) and cand.strip():
            value = cand.strip()
            state["original_user_query"] = value
            agent_name = str(getattr(ctx, "agent_name", "") or "").strip()
            if agent_name:
                namespace = state.get(agent_name) if hasattr(state, "get") else None
                if not isinstance(namespace, dict):
                    namespace = {}
                    state[agent_name] = namespace
                namespace["original_user_query"] = value
            break


def origin_query_save_callback(callback_context: Any) -> Optional[types.Content]:
    """가장 앞단에서 사용자 질문을 state['original_user_query']에 보존하는 콜백."""
    _ensure_original_user_query(callback_context)
    return None

def _state_to_str(state_dict: dict, chunk_content_len: int = 50, max_len: int = 8000) -> str:
    """state를 보기 쉬운 JSON 형태로 변환. retrieval_results 각 청크의 content는 chunk_content_len자로 축약."""
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


def log_before_agent(callback_context: Any) -> Optional[types.Content]:
    _ensure_original_user_query(callback_context)
    agent_name = getattr(callback_context, "agent_name", "unknown")
    invocation_id = getattr(callback_context, "invocation_id", None)
    state_dict = _state(callback_context)
    logger.info(
        "[CALLBACK] BEFORE_AGENT | agent=%s | invocation_id=%s | state=%s",
        agent_name,
        invocation_id,
        _state_to_str(state_dict),
    )
    return None


def log_after_agent(callback_context: Any) -> Optional[types.Content]:
    agent_name = getattr(callback_context, "agent_name", "unknown")
    invocation_id = getattr(callback_context, "invocation_id", None)
    state_dict = _state(callback_context)
    logger.info(
        "[CALLBACK] AFTER_AGENT | agent=%s | invocation_id=%s | state=%s",
        agent_name,
        invocation_id,
        _state_to_str(state_dict),
    )
    return None


def log_before_model(callback_context: Any, llm_request: Any) -> Optional[Any]:
    agent_name = getattr(callback_context, "agent_name", "unknown")
    model_name = _model_name(llm_request)
    invocation_id = getattr(callback_context, "invocation_id", None)
    state_dict = _state(callback_context)
    if settings.LOGGING_DETAILS:
        logger.info(
            "[CALLBACK] BEFORE_MODEL | agent=%s | model=%s | invocation_id=%s | state=%s | request=%s",
            agent_name,
            model_name,
            invocation_id,
            _state_to_str(state_dict),
            _to_str(llm_request),
        )
    else:
        logger.info(
            "[CALLBACK] BEFORE_MODEL | agent=%s | model=%s | invocation_id=%s | state=%s",
            agent_name,
            model_name,
            invocation_id,
            _state_to_str(state_dict),
        )
    return None


def log_after_model(callback_context: Any, llm_response: Any) -> Optional[Any]:
    agent_name = getattr(callback_context, "agent_name", "unknown")
    model_name = _model_name(llm_response)
    invocation_id = getattr(callback_context, "invocation_id", None)
    state_dict = _state(callback_context)
    if settings.LOGGING_DETAILS:
        logger.info(
            "[CALLBACK] AFTER_MODEL | agent=%s | model=%s | invocation_id=%s | state=%s | output=%s",
            agent_name,
            model_name,
            invocation_id,
            _state_to_str(state_dict),
            _to_str(llm_response),
        )
    else:
        logger.info(
            "[CALLBACK] AFTER_MODEL | agent=%s | model=%s | invocation_id=%s | state=%s",
            agent_name,
            model_name,
            invocation_id,
            _state_to_str(state_dict),
        )
    return None


def log_before_tool(
    tool: Any,
    args: dict[str, Any],
    tool_context: Any,
) -> Optional[dict[str, Any]]:
    tool_name = getattr(tool, "name", str(tool))
    agent_name = getattr(tool_context, "agent_name", "unknown")
    model_name = _model_name(tool_context)
    state_dict = _state(tool_context)
    if settings.LOGGING_DETAILS:
        logger.info(
            "[CALLBACK] BEFORE_TOOL | agent=%s | model=%s | tool=%s | state=%s | args=%s",
            agent_name,
            model_name,
            tool_name,
            _state_to_str(state_dict),
            _to_str(args),
        )
    else:
        logger.info(
            "[CALLBACK] BEFORE_TOOL | agent=%s | model=%s | tool=%s | state=%s",
            agent_name,
            model_name,
            tool_name,
            _state_to_str(state_dict),
        )
    return None


def log_after_tool(
    tool: Any,
    args: dict[str, Any],
    tool_context: Any,
    tool_response: dict[str, Any],
) -> Optional[dict[str, Any]]:
    tool_name = getattr(tool, "name", str(tool))
    agent_name = getattr(tool_context, "agent_name", "unknown")
    model_name = _model_name(tool_context)
    state_dict = _state(tool_context)
    if settings.LOGGING_DETAILS:
        logger.info(
            "[CALLBACK] AFTER_TOOL | agent=%s | model=%s | tool=%s | state=%s | output=%s",
            agent_name,
            model_name,
            tool_name,
            _state_to_str(state_dict),
            _to_str(tool_response),
        )
    else:
        logger.info(
            "[CALLBACK] AFTER_TOOL | agent=%s | model=%s | tool=%s | state=%s",
            agent_name,
            model_name,
            tool_name,
            _state_to_str(state_dict),
        )
    return None


def chain_before_agent(
    logging_cb: Any,
    existing_cb: Any,
) -> Any:
    def chained(callback_context: Any) -> Optional[types.Content]:
        logging_cb(callback_context)
        if existing_cb:
            return existing_cb(callback_context)
        return None

    return chained


