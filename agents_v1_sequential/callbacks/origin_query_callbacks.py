"""사용자 원문 질문을 state['original_user_query']에 저장하는 전용 콜백."""

from typing import Any, Optional
import time

from google.genai import types


REQUEST_START_TS_KEY = "request_start_ts"


def _content_to_text(content: Any) -> str:
    """google.genai.types.Content에서 텍스트만 추출."""
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


def _ensure_original_user_query(ctx: Any) -> None:
    """state에 original_user_query가 없으면 가능한 키에서 채워 넣는다."""
    state = getattr(ctx, "state", None)
    if state is None or not hasattr(state, "__setitem__"):
        return
    existing = state.get("original_user_query") if hasattr(state, "get") else None
    if isinstance(existing, str) and existing.strip():
        return

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
        # 1) state 기반 후보
        state.get("user_query") if hasattr(state, "get") else None,
        state.get("query") if hasattr(state, "get") else None,
        state.get("input") if hasattr(state, "get") else None,
        state.get("question") if hasattr(state, "get") else None,
        # 2) callback context 속성 기반 후보(ADK 버전/런타임에 따라 state에 안 들어올 수 있음)
        getattr(ctx, "user_query", None),
        getattr(ctx, "query", None),
        getattr(ctx, "input", None),
        getattr(ctx, "question", None),
        getattr(ctx, "text", None),
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
    """가장 앞단에서 사용자 질문을 state['original_user_query']에 보존하는 before_agent 콜백."""
    state = getattr(callback_context, "state", None)
    if state is not None and hasattr(state, "get") and hasattr(state, "__setitem__"):
        # 사용자 입력 시점 -> 최종 응답까지 지연시간 측정용 타임스탬프를 한 번만 저장한다.
        if not state.get(REQUEST_START_TS_KEY):
            state[REQUEST_START_TS_KEY] = time.perf_counter()
    _ensure_original_user_query(callback_context)
    return None

