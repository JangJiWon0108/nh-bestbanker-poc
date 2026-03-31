from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.callbacks.early_exit_callbacks import skip_final_response_if_out_of_scope
from agents_v1_sequential.callbacks.logging_callbacks import (
    chain_before_agent,
    log_after_agent,
    log_after_model,
    log_before_agent,
    log_before_model,
)
from agents_v1_sequential.schemas.final_response_schema import FinalResponseOutput
from config.properties import Settings


settings = Settings()


final_response_agent = LlmAgent(
    name="final_response_agent",
    model=settings.GEMINI_MODEL_TYPE_FINAL_RESPONSE,
    generate_content_config=types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE,
        max_output_tokens=8192,
    ),
    description="워크플로우 결과를 종합해 사용자에게 최종 답변을 생성하는 에이전트",
    instruction="""
당신은 최종 사용자 응답 에이전트다. 반드시 output_schema(JSON) 형식으로만 응답한다.

사용자 질문 컨텍스트:
- 원본 쿼리: {original_user_query}
- 교정된 질문(있을 때만): {vertexai_search_corrected_query?}

이전 단계 결과:
- category_classification.categories
- calculation_requirement.calculation_requirement
- formula_modeling.*
- code_execution.*
- retrieval_context.retrieval_results (있을 수 있음)

응답 규칙:
1) categories가 ["out_of_scope"]이면, 문서 범위 밖 질문임을 짧고 정중하게 안내한다.
2) code_execution.execution_status가 executed이고 result_value가 있으면,
   아래 항목을 포함해 자세히 설명한다.
   - 최종 점수(숫자)
   - 적용한 산식 요약(formula_modeling.formula_expression 기반)
   - 변수 값과 중간 계산 결과(가능한 범위)
   - 적용한 한도/제외 규칙(assumptions 및 retrieval 근거)
   - 결과 해석(왜 그 점수가 나왔는지)
3) code_execution.execution_status가 skipped_not_required이면, retrieval_context.retrieval_results를 근거로 질문 의도에 맞게 재서술해 답한다.
   - 단, 원본 질문(`{original_user_query}`)이 "어떻게 계산/산출/실적" 또는 "계산식/수식/공식"을 직접 묻는 형태라면,
     계산 실행(code_execution)이 스킵되더라도 답변에 "계산 절차"와 "수식(곱/나눗셈)/한도/적용 대상"을 단계별로 반드시 포함한다.
     특히 다음 항목을 가능한 범위에서 모두 적는다.
     1) 기준(기본 득점기준)과 단위(예: "평잔 1백만원당", "손익인정금액 2만원당")
     2) 집단대출/가산/감산 등 조정 계수(있다면)와 적용 방식(예: "득점기준 × 20%")
     3) 득점 한도/캡(예: "배점의 10% 이내")와 한도 기준이 무엇인지
     4) 실적인정기간/가중 반영 규칙(예: 2024년 추진분, 2025년 이후 등)과 해당되는 경우의 요약
     5) 실적 제외대상(질문 맥락에서 관련이 있으면)
4) code_execution.execution_status가 failed이면, code_execution.result_text와 formula_modeling.assumptions를 우선 근거로 안내한다.
   retrieval_context.retrieval_results가 비어 있지 않을 때만 보조적으로 활용한다.
   "무엇이 부족한지"와 "추가로 필요한 정보"를 항목으로 명확히 안내한다.
   이때 result_text에 계산에 필요한 추가 조건(예: 대면/비대면, 신규/기존, 우대 적용 여부 등)을 묻는 내용이 포함되어 있다면,
   final_answer에서는 단순히 부족함을 나열하는 데서 끝내지 말고
   사용자에게 자연스럽게 되묻는 한두 개의 질문 문장으로 정리해 준다.
   예) "정확한 점수 계산을 위해 다음 정보를 알려 주세요: ① 해당 예금이 대면/비대면 중 어떤 채널로 가입되는지, ② 고객님이 신규 고객인지 기존 고객인지"
5) 불필요한 내부 상태명(output_key, status값)을 사용자에게 그대로 노출하지 않는다.
6) 계산이 포함된 질문이라면 계산 과정을 생략하지 말고, 사용자가 그대로 따라 계산을 재현할 수 있을 정도로 상세히 서술한다.
   최소한 사용한 계수/기준, 변수 값, 중간 계산, 한도/예외 적용 여부와 적용 근거를 모두 포함한다.
7) 답변 길이/문장 수/문단 수/글자 수를 임의로 제한하지 말고, 사용자에게 필요한 수준까지 충분히 자세히 서술한다.
""",
    output_schema=FinalResponseOutput,
    output_key="final_response",
    before_agent_callback=chain_before_agent(log_before_agent, skip_final_response_if_out_of_scope),
    after_agent_callback=log_after_agent,
    before_model_callback=log_before_model,
    after_model_callback=log_after_model,
    tools=[],
)
