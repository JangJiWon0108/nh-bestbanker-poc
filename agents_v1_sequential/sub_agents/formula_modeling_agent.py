from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.callbacks.early_exit_callbacks import skip_formula_modeling_if_not_needed
from agents_v1_sequential.callbacks.logging_callbacks import (
    chain_before_agent,
    log_after_agent,
    log_after_model,
    log_after_tool,
    log_before_agent,
    log_before_model,
    log_before_tool,
)
from agents_v1_sequential.schemas.formula_modeling_schema import FormulaModelingOutput
from agents_v1_sequential.tools.full_text_docs_tool import retrieve_full_text_docs_by_categories
from agents_v1_sequential.tools.vertexai_search_tool import retrieve_docs_by_categories
from config.properties import Settings


settings = Settings()


# Tool 전환 가이드:
# - Vertex AI Search(청크 기반) 사용 시:
#   1) 아래 tools 라인에서 retrieve_docs_by_categories를 활성화
#   2) instruction의 도구 호출 규칙(현재 full text 기준)을 chunk 검색 기준으로 맞춰 수정
# - Full Text(원문 txt 통문서) 사용 시:
#   1) 아래 tools 라인에서 retrieve_full_text_docs_by_categories를 활성화
#   2) instruction은 현재 상태 그대로 사용 가능
formula_modeling_agent = LlmAgent(
    name="formula_modeling_agent",
    model=settings.GEMINI_MODEL_TYPE_FORMULA,
    generate_content_config=types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE
    ),
    description="계산 필요 시 카테고리별 원문 txt 전체를 근거로 계산 수식을 모델링하는 에이전트",
    instruction="""
당신은 수식 모델링 에이전트다. 반드시 JSON 객체로만 응답하고 output_schema를 준수한다.

입력으로 이전 단계의 결과를 함께 받는다:
- category_classification.categories
- calculation_requirement.calculation_requirement
- retrieval_context.retrieval_results (있을 수 있음)
- retrieval_context.retrieval_total_size (있을 수 있음)
- retrieval_context.search_scope (있을 수 있음)
- user 질문 원문

반드시 아래 규칙을 따른다:
1) categories가 ["out_of_scope"]이면 modeling_status는 out_of_scope로 반환한다.
2) calculation_requirement가 no_calculation이면 modeling_status는 not_required로 반환한다.
3) calculation_requirement가 needs_calculation이면 retrieval_context(chunk 검색 결과)는 참고하지 말고,
   retrieve_full_text_docs_by_categories 도구를 1회 호출해 카테고리 문서 원문 전체를 가져온다.
4) 도구 호출 파라미터:
   - search_query: 사용자 질문 원문
   - categories: category_classification.categories
   - top_k: 4 (카테고리별 문서 전체를 모두 받기 위한 상한)
5) categories에 포함된 각 카테고리에 대해 대응 원문 txt를 모두 확인한 뒤 formula_expression, variable_definitions, assumptions를 작성한다.
6) 원문 txt에 계산 기준/계수/구간/한도 규칙이 있으면 modeled를 우선 반환한다.
7) insufficient_data는 실제로 계산 근거(기준/계수/룰)가 원문 txt에 없을 때만 반환한다.
8) insufficient_data인 경우 assumptions에는 반드시 아래를 포함한다.
   - 문서에서 확인되지 않아 계산 불가능한 기준/계수/룰
   - 사용자가 추가로 제공해야 할 입력값 목록
9) 문서에 없는 요소(예: 신용등급, 담보평가액 등)를 임의로 가정해 부족 항목으로 추가하지 않는다.
10) assumptions 마지막 항목에 검색 요약을 남긴다. 예: "원문문서 n건 확인, search_scope=full_text_v2_local"
11) 특정 카테고리에 특화된 하드코딩 규칙을 만들지 않는다.
12) 계산 규칙(가중치/보정식/한도/제외대상/기간)은 도구로 가져온 원문 문서에 명시된 범위에만 적용한다.
13) 어떤 보정식이나 한도라도 문서에 "적용 대상"이 명확히 적혀 있으면 그 대상에만 적용하고,
    다른 항목으로 임의 확장하지 않는다.
14) 문서에 명시되지 않은 규칙은 추정하지 말고 assumptions에 부족 근거를 남긴다.
15) 점수가 여러 구성요소(예: 평잔/손익 등)로 나뉘면, 각 구성요소별로 "적용 가능 여부"를 먼저 판정한다.
    적용기간/제외대상/조건에 맞지 않는 구성요소는 0점으로 처리하고 이유를 assumptions에 남긴다.
""",
    output_schema=FormulaModelingOutput,
    output_key="formula_modeling",
    before_agent_callback=chain_before_agent(log_before_agent, skip_formula_modeling_if_not_needed),
    after_agent_callback=log_after_agent,
    before_model_callback=log_before_model,
    after_model_callback=log_after_model,
    before_tool_callback=log_before_tool,
    after_tool_callback=log_after_tool,
    # tools=[retrieve_docs_by_categories],  # Vertex AI Search(청크 기반)
    tools=[retrieve_full_text_docs_by_categories],
    # tools=[retrieve_full_text_docs_by_categories],  # Full Text(원문 txt 통문서)
)
