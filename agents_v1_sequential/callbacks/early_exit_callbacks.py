import json
import time

from google.adk.agents.context import Context
from google.genai import types

from config.custom_log import get_logger

OUT_OF_SCOPE = "out_of_scope"
NO_CALCULATION = "no_calculation"

logger = get_logger(__name__)
REQUEST_START_TS_KEY = "request_start_ts"


def _extract_conversation_messages(callback_context: Context) -> list:
    """
    ADK 런타임이 노출하는 대화 히스토리(메시지 리스트)를 최대한 찾아내기 위한 유틸.
    (환경/버전마다 속성명이 다를 수 있어 방어적으로 여러 후보를 확인합니다.)
    """

    # 1) callback_context 직접 속성 후보
    for attr in (
        "conversation_history",
        "chat_history",
        "messages",
        "history",
        "turns",
    ):
        v = getattr(callback_context, attr, None)
        if isinstance(v, list):
            return v

    # 2) adk_session 아래 후보
    adk_session = getattr(callback_context, "adk_session", None)
    if adk_session is not None:
        for attr in ("history", "messages", "conversation_history", "chat_history"):
            v = getattr(adk_session, attr, None)
            if isinstance(v, list):
                return v

    # 3) state 내부 후보
    state = getattr(callback_context, "state", None)
    if isinstance(state, dict):
        for key in ("conversation_history", "chat_history", "messages", "history"):
            v = state.get(key)
            if isinstance(v, list):
                return v

    return []


def _count_user_and_assistant(messages: list) -> tuple[int, int]:
    user_count = 0
    assistant_count = 0

    for m in messages:
        role = None
        if isinstance(m, dict):
            role = m.get("role") or m.get("speaker") or m.get("author")
        else:
            role = getattr(m, "role", None) or getattr(m, "speaker", None)
            if role is None:
                role = getattr(m, "author", None)

        if not isinstance(role, str):
            continue

        r = role.strip().lower()
        if r in {"user", "human"}:
            user_count += 1
        elif r in {"assistant", "model", "ai", "bot"}:
            assistant_count += 1

    return user_count, assistant_count


def _as_content(payload: dict) -> types.Content:
    return types.Content(parts=[types.Part(text=json.dumps(payload, ensure_ascii=False))])


def _as_text(text: str) -> types.Content:
    return types.Content(parts=[types.Part(text=text)])


def skip_retrieval_if_out_of_scope(callback_context: Context) -> types.Content | None:
    category_state = callback_context.state.get("category_classification", {})
    categories = category_state.get("categories", [])

    if categories == [OUT_OF_SCOPE]:
        original_query = callback_context.state.get("original_user_query", "") or ""
        payload = {
            "query": original_query,
            "categories": categories,
            "retrieval_results": [],
            "retrieval_total_size": 0,
            "retrieval_type": None,
        }
        callback_context.state["retrieval_context"] = payload
        return _as_content(payload)

    return None


def skip_code_execution_if_not_needed(callback_context: Context) -> types.Content | None:
    category_state = callback_context.state.get("category_classification", {})
    categories = category_state.get("categories", [])
    calculation_state = callback_context.state.get("calculation_requirement", {})
    requirement = calculation_state.get("calculation_requirement")

    if categories == [OUT_OF_SCOPE]:
        payload = {
            "execution_status": "skipped_out_of_scope",
            "result_value": None,
            "result_text": "문서 범위 밖 질문으로 코드 실행을 생략했습니다.",
            "executed_code": "",
        }
        callback_context.state["code_execution"] = payload
        return _as_content(payload)

    if requirement == NO_CALCULATION:
        payload = {
            "execution_status": "calculation_not_needed",
            "result_value": None,
            "result_text": "계산(수식 계산)이 필요하지 않아 코드 실행을 하지 않았습니다.",
            "executed_code": "",
        }
        callback_context.state["code_execution"] = payload
        return _as_content(payload)

    return None


def skip_final_response_if_out_of_scope(callback_context: Context) -> types.Content | None:
    category_state = callback_context.state.get("category_classification", {})
    categories = category_state.get("categories", [])
    clarification_needed = bool(category_state.get("clarification_needed", False))
    clarification_needed_question = str(
        category_state.get("clarification_needed_question", "")
    ).strip()
    code_execution = _normalize_code_execution_state(
        callback_context.state.get("code_execution", {})
    )
    code_execution = _normalize_failed_execution(code_execution)
    callback_context.state["code_execution"] = code_execution
    execution_status = code_execution.get("execution_status")

    if categories == [OUT_OF_SCOPE]:
        if clarification_needed and clarification_needed_question:
            message = clarification_needed_question
        else:
            message = (
                "질문이 현재 문서 범위를 벗어나 있습니다. "
                "개인여신, 기업여신, 수신, 디지털금융 관련 질문으로 다시 입력해 주세요."
            )

        # final_response_agent는 plain text만 반환하도록 변경되었으므로 out_of_scope 시에도
        # JSON 래핑 없이 문자열로 state에 저장한다.
        callback_context.state["final_response"] = message

        # final_response_agent 모델 호출이 스킵되는 경우가 있어, 여기서 타이밍을 보정해 로깅한다.
        state = getattr(callback_context, "state", None)
        if state is not None and hasattr(state, "get"):
            start_ts = state.get(REQUEST_START_TS_KEY)
            if isinstance(start_ts, (int, float)):
                elapsed = time.perf_counter() - start_ts
                logger.info("[JANGJIWON-TIME] user_to_final_response=%.3f초", elapsed)
        return _as_text(message)

    if execution_status == "executed":
        # 계산 성공 케이스는 final_response_agent가 근거/과정을 포함해 문장을 생성하도록 넘긴다.
        return None

    if execution_status in {"calculation_not_needed", "failed"}:
        return None

    return None


def skip_conversation_rewrite_if_unneeded(
    callback_context: Context,
) -> types.Content | None:
    """
    conversation_rewrite_agent는 비용/지연이 있으므로, 가능한 경우에만 스킵합니다.

    기존 구현은 특정 키워드(예: "점수", "계산", "대면" 등)를 기준으로 스킵해서
    멀티턴에서 "요약(history_summary)"이 비는 문제가 있었습니다.

    이제는 "대화 히스토리(이전 user/assistant 존재 여부)"로만 판단합니다.
    """
    state = getattr(callback_context, "state", None)
    if state is None or not hasattr(state, "get"):
        return None

    original_query = state.get("original_user_query", "") or ""
    if not isinstance(original_query, str) or not original_query.strip():
        return None

    q = original_query.strip()

    messages = _extract_conversation_messages(callback_context)
    if not messages:
        # 히스토리를 알 수 없는 런타임이면 스킵하지 않습니다(정확도 우선).
        return None

    user_count, assistant_count = _count_user_and_assistant(messages)
    recognized_turns = user_count + assistant_count
    if recognized_turns == 0:
        # role/speaker를 인식하지 못한 경우에는 스킵 판단을 할 수 없으므로 rewrite 진행.
        return None

    # "첫 사용자 턴"으로 보이는 경우에만 스킵:
    # - assistant 응답이 아직 한 번도 없었고
    # - 사용자 턴이 1개 이하인 경우
    # 이 상황에서는 conversation_rewrite_agent의 프롬프트 규칙상
    # history_summary를 ""로 두는 것이 정상입니다.
    if assistant_count == 0 and user_count <= 1:
        payload = {"history_summary": "", "rewritten_query": q}
        state["conversation_rewrite"] = payload
        return _as_content(payload)

    # 그 외에는 멀티턴 요약이 필요할 수 있으므로 rewrite 호출을 진행합니다.
    return None


def _normalize_code_execution_state(raw_value: object) -> dict:
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return {}


def _normalize_failed_execution(code_execution: dict) -> dict:
    status = code_execution.get("execution_status")
    if status != "executed":
        return code_execution

    result_text = str(code_execution.get("result_text", ""))
    executed_code = str(code_execution.get("executed_code", ""))
    failure_markers = ("OUTCOME_FAILED", "Traceback", "SyntaxError", "Exception")

    if any(marker in result_text for marker in failure_markers) or any(
        marker in executed_code for marker in failure_markers
    ):
        code_execution["execution_status"] = "failed"
        code_execution["result_value"] = None
        if not result_text:
            code_execution["result_text"] = (
                "코드 실행 로그에서 실패 신호(Traceback/OUTCOME_FAILED)를 확인했습니다."
            )

    return code_execution
