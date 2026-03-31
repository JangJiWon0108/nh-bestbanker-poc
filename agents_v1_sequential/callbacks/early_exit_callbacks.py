import json

from google.adk.agents.context import Context
from google.genai import types

from config.properties import Settings

OUT_OF_SCOPE = "out_of_scope"
NO_CALCULATION = "no_calculation"
NEEDS_CALCULATION = "needs_calculation"

_settings = Settings()


def _as_content(payload: dict) -> types.Content:
    return types.Content(parts=[types.Part(text=json.dumps(payload, ensure_ascii=False))])


def skip_formula_modeling_if_not_needed(callback_context: Context) -> types.Content | None:
    category_state = callback_context.state.get("category_classification", {})
    categories = category_state.get("categories", [])
    calculation_state = callback_context.state.get("calculation_requirement", {})
    requirement = calculation_state.get("calculation_requirement")

    if categories == [OUT_OF_SCOPE]:
        payload = {
            "modeling_status": OUT_OF_SCOPE,
            "categories": categories,
            "formula_expression": "",
            "variable_definitions": {},
            "assumptions": [],
        }
        callback_context.state["formula_modeling"] = payload
        return _as_content(payload)

    if requirement == NO_CALCULATION:
        payload = {
            "modeling_status": "not_required",
            "categories": categories,
            "formula_expression": "",
            "variable_definitions": {},
            "assumptions": [],
        }
        callback_context.state["formula_modeling"] = payload
        return _as_content(payload)

    return None


def skip_retrieval_if_out_of_scope(callback_context: Context) -> types.Content | None:
    category_state = callback_context.state.get("category_classification", {})
    categories = category_state.get("categories", [])
    calculation_state = callback_context.state.get("calculation_requirement", {})
    requirement = calculation_state.get("calculation_requirement")

    if categories == [OUT_OF_SCOPE]:
        original_query = callback_context.state.get("original_user_query", "") or ""
        payload = {
            "query": original_query,
            "categories": categories,
            "retrieval_results": [],
            "retrieval_total_size": 0,
            "search_scope": "out_of_scope_skip",
        }
        callback_context.state["retrieval_context"] = payload
        return _as_content(payload)

    # v1: formula_modeling_agent를 사용하는 경우에만
    # needs_calculation일 때 retrieval을 스킵하고,
    # formula_modeling 단계에서 full text를 읽도록 한다.
    if _settings.USE_V1_FORMULA_MODELING_AGENT and requirement == NEEDS_CALCULATION:
        original_query = callback_context.state.get("original_user_query", "") or ""
        payload = {
            "query": original_query,
            "categories": categories,
            "retrieval_results": [],
            "retrieval_total_size": 0,
            "search_scope": "skipped_for_full_text_modeling",
        }
        callback_context.state["retrieval_context"] = payload
        return _as_content(payload)

    return None


def skip_code_execution_if_not_needed(callback_context: Context) -> types.Content | None:
    category_state = callback_context.state.get("category_classification", {})
    categories = category_state.get("categories", [])
    calculation_state = callback_context.state.get("calculation_requirement", {})
    requirement = calculation_state.get("calculation_requirement")
    formula_state = callback_context.state.get("formula_modeling", {})
    modeling_status = formula_state.get("modeling_status")

    if categories == [OUT_OF_SCOPE]:
        payload = {
            "execution_status": "skipped_out_of_scope",
            "result_value": None,
            "result_text": "문서 범위 밖 질문으로 코드 실행을 생략했습니다.",
            "executed_code": "",
        }
        callback_context.state["code_execution"] = payload
        return _as_content(payload)

    if requirement == NO_CALCULATION or modeling_status == "not_required":
        payload = {
            "execution_status": "skipped_not_required",
            "result_value": None,
            "result_text": "수식 계산이 필요하지 않아 코드 실행을 생략했습니다.",
            "executed_code": "",
        }
        callback_context.state["code_execution"] = payload
        return _as_content(payload)

    return None


def skip_final_response_if_out_of_scope(callback_context: Context) -> types.Content | None:
    category_state = callback_context.state.get("category_classification", {})
    categories = category_state.get("categories", [])
    requires_clarification = bool(category_state.get("requires_clarification", False))
    clarification_question = str(category_state.get("clarification_question", "")).strip()
    code_execution = _normalize_code_execution_state(
        callback_context.state.get("code_execution", {})
    )
    code_execution = _normalize_failed_execution(code_execution)
    callback_context.state["code_execution"] = code_execution
    execution_status = code_execution.get("execution_status")

    if categories == [OUT_OF_SCOPE]:
        if requires_clarification and clarification_question:
            payload = {"final_answer": clarification_question}
        else:
            payload = {
                "final_answer": (
                    "질문이 현재 문서 범위를 벗어나 있습니다. "
                    "개인여신, 기업여신, 수신, 디지털금융 관련 질문으로 다시 입력해 주세요."
                )
            }
        callback_context.state["final_response"] = payload
        return _as_content(payload)

    if execution_status == "executed":
        # 계산 성공 케이스는 final_response_agent가 근거/과정을 포함해 문장을 생성하도록 넘긴다.
        return None

    if execution_status in {"skipped_not_required", "failed"}:
        return None

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
