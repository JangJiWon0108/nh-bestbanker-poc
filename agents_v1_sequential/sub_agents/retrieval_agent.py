from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.callbacks.corrected_query_callbacks import (
    save_corrected_query_after_tool,
)
from agents_v1_sequential.callbacks.early_exit_callbacks import skip_retrieval_if_out_of_scope
from agents_v1_sequential.callbacks.logging_callbacks import (
    chain_before_agent,
    log_after_agent,
    log_after_model,
    log_after_tool,
    log_before_agent,
    log_before_model,
    log_before_tool,
)
from agents_v1_sequential.schemas.retrieval_schema import RetrievalOutput
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


if settings.USE_V1_FORMULA_MODELING_AGENT:
    # 기존 동작: needs_calculation일 때는 retrieval을 건너뛰고,
    # formula_modeling_agent가 full text를 읽는다.
    retrieval_instruction = """
당신은 문서 검색 에이전트다. 반드시 output_schema(JSON) 형식으로만 응답한다.

입력으로 이전 단계 결과를 사용한다:
- category_classification.categories
- conversation_rewrite.rewritten_query (가능하면 우선 사용)
- state.original_user_query (현재 턴 질문 원문)

규칙:
1) 검색에 사용할 기준 질의는 다음 우선순위로 선택한다.
   a) conversation_rewrite.rewritten_query가 존재하면 그 값을 사용한다.
   b) 그렇지 않으면 state.original_user_query를 사용한다.
2) categories가 ["out_of_scope"]이면 검색하지 말고 빈 retrieval_results를 반환한다.
3) calculation_requirement.calculation_requirement가 needs_calculation이면
   이 단계 검색을 수행하지 않고 빈 retrieval_results를 반환한다.
4) 그 외(no_calculation)에는 retrieve_docs_by_categories 도구를 1회 호출한다.
5) 도구 호출 파라미터:
   - search_query: 위 1)에서 선택한 기준 질의
   - categories: category_classification.categories
6) RetrievalOutput.query 필드에는 실제로 search_query에 사용한 질의를 그대로 넣는다.
7) 도구 응답을 RetrievalOutput 형식으로 그대로 매핑해 반환한다.
8) 도구를 반복 호출하지 않는다.
"""
    retrieval_tools = [retrieve_docs_by_categories]
    retrieval_description = "카테고리와 질문을 바탕으로 Vertex AI Search를 수행하는 에이전트"
else:
    # v1에서 formula_modeling_agent를 사용하지 않을 때:
    # calculation_requirement가 needs_calculation이면 카테고리별 full text를 직접 읽어서
    # retrieval_context.retrieval_results에 넣어 code_execution_agent가 바로 활용하도록 한다.
    retrieval_instruction = """
당신은 문서 검색 에이전트다. 반드시 output_schema(JSON) 형식으로만 응답한다.

입력으로 이전 단계 결과를 사용한다:
- category_classification.categories
- calculation_requirement.calculation_requirement
- conversation_rewrite.rewritten_query (가능하면 우선 사용)
- state.original_user_query (현재 턴 질문 원문)

규칙:
1) 검색에 사용할 기준 질의는 다음 우선순위로 선택한다.
   a) conversation_rewrite.rewritten_query가 존재하면 그 값을 사용한다.
   b) 그렇지 않으면 state.original_user_query를 사용한다.
2) categories가 ["out_of_scope"]이면 검색하지 말고 빈 retrieval_results를 반환한다.
3) calculation_requirement.calculation_requirement가 needs_calculation이면
   retrieve_full_text_docs_by_categories 도구를 1회 호출해 카테고리별 원문 txt 전체를 읽는다.
4) 그 외(no_calculation)에는 retrieve_docs_by_categories 도구를 1회 호출해 검색 결과 청크를 가져온다.
5) 도구 호출 공통 파라미터:
   - search_query: 위 1)에서 선택한 기준 질의
   - categories: category_classification.categories
6) RetrievalOutput.query 필드에는 실제로 search_query에 사용한 질의를 그대로 넣는다.
7) 도구 응답을 RetrievalOutput 형식으로 그대로 매핑해 반환한다.
8) 도구를 반복 호출하지 않는다.
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
    output_schema=RetrievalOutput,
    output_key="retrieval_context",
    before_agent_callback=chain_before_agent(log_before_agent, skip_retrieval_if_out_of_scope),
    after_agent_callback=log_after_agent,
    before_model_callback=log_before_model,
    after_model_callback=log_after_model,
    before_tool_callback=log_before_tool,
    after_tool_callback=chain_after_tool(save_corrected_query_after_tool, log_after_tool),
    tools=retrieval_tools,
)
