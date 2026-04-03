from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.callbacks.corrected_query_callbacks import (
    save_corrected_query_after_tool,
)
from agents_v1_sequential.callbacks.early_exit_callbacks import skip_retrieval_if_out_of_scope
from agents_v1_sequential.callbacks.logging_callbacks import (
    chain_after_model,
    chain_before_agent,
    log_after_agent,
    log_after_model,
    log_after_tool,
    retrieval_replace_model_output_with_retrieval_json,
    log_before_agent,
    log_before_model,
    log_before_tool,
)
from agents_v1_sequential.tools.full_text_docs_tool import retrieve_full_text_docs_by_categories
from agents_v1_sequential.tools.vertexai_search_tool import retrieve_docs_by_categories
from config.properties import Settings


settings = Settings()


def chain_after_tool(save_cb: Any, logging_cb: Any) -> Any:
    def chained(
        tool: Any,
        args: dict[str, Any],
        tool_context: Any,
        tool_response: dict[str, Any],
    ) -> dict[str, Any] | None:
        save_cb(tool, args, tool_context, tool_response)
        return logging_cb(tool, args, tool_context, tool_response)

    return chained


retrieval_instruction = """
당신은 문서 검색 에이전트다. 검색 결과는 도구가 session state에 기록한다.
도구를 1회 호출한 뒤 답변을 써도 되지만, 사용자에게 보이는 최종 텍스트는 시스템이
retrieval_context를 JSON(로그와 동일 축약)으로 통일해 넣는다. 청크 검색·full text 모두 동일하다.

입력으로 이전 단계 결과를 사용한다:
- category_classification.categories
- calculation_requirement.calculation_requirement
- conversation_rewrite.rewritten_query (가능하면 우선 사용)
- state.original_user_query (현재 턴 질문 원문)

규칙:
1) 검색에 사용할 기준 질의는 다음 우선순위로 선택한다.
   a) conversation_rewrite.rewritten_query가 존재하면 그 값을 사용한다.
   b) 그렇지 않으면 state.original_user_query를 사용한다.
2) categories가 ["out_of_scope"]이면 검색 도구를 호출하지 않는다(이전 단계에서 처리됨).
3) calculation_requirement.calculation_requirement가 needs_calculation이면
   retrieve_full_text_docs_by_categories 도구를 1회 호출해 카테고리별 원문 txt 전체를 읽는다.
4) 그 외(no_calculation)에는 retrieve_docs_by_categories 도구를 1회 호출해 검색 결과 청크를 가져온다.
5) 도구 호출 공통 파라미터:
   - search_query: 위 1)에서 선택한 기준 질의
   - categories: category_classification.categories
6) 도구를 반복 호출하지 않는다.
"""

retrieval_tools = [retrieve_full_text_docs_by_categories, retrieve_docs_by_categories]
retrieval_description = "카테고리와 질문을 바탕으로 full text 또는 Vertex AI Search를 수행하는 에이전트"


retrieval_agent = LlmAgent(
    name="retrieval_agent",
    model=settings.GEMINI_MODEL_TYPE_RETRIEVAL,
    generate_content_config=types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE
    ),
    description=retrieval_description,
    instruction=retrieval_instruction,
    before_agent_callback=chain_before_agent(log_before_agent, skip_retrieval_if_out_of_scope),
    after_agent_callback=log_after_agent,
    before_model_callback=log_before_model,
    after_model_callback=chain_after_model(
        log_after_model,
        retrieval_replace_model_output_with_retrieval_json,
    ),
    before_tool_callback=log_before_tool,
    after_tool_callback=chain_after_tool(save_corrected_query_after_tool, log_after_tool),
    tools=retrieval_tools,
)
