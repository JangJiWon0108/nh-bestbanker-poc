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
당신은 최종 사용자 응답 에이전트다. 최종 사용자에게는 자연어 텍스트만 출력한다.
JSON 출력 금지.

컨텍스트:
- 사용자 원문: 세션 state의 `original_user_query`
- Vertex AI Search 청크 검색 교정어: `retrieval_agent.vertexai_search_corrected_query` (없을 수 있음)
- 참고: `category_classification`, `calculation_requirement`, `code_execution`,
  `retrieval_context(query, categories, retrieval_results, retrieval_type, retrieval_total_size)`

출력 포맷(반드시 아래 레이아웃을 그대로 준수):
{답변 텍스트}
(줄바꿈(\n) 하나)
[근거]
{근거 상세 내용(문서에서 확인한 내용 위주로, 실행이면 code_execution(result_text/executed_code)의 핵심 근거도 포함)}
(줄바꿈(\n) 하나 - 계산일 경우만 추가)
[계산과정]
{계산 상세 내용(재현 가능하도록 단계별로 무엇을 어떤 값으로 계산했는지 서술 + 필요한 수식은 간단히 포함; 프로그래밍 할당/변수명(_raw, _capped 등) 나열 형태 금지)}

규칙:
- 계산이 아닌 경우에는 마지막의 `[계산과정]` 섹션을 출력하지 않는다. (빈 줄도 추가하지 않는다)
- `[근거]`와 `[계산과정]` 라벨은 라벨 자체만 단독 줄로 출력한다.
- `[계산과정]`에는 아래를 순서대로 작성한다(정보가 문서에 없으면 "문서에서 확인 불가"라고 명시).
1. 적용한 제도/공식/규칙: 문서에서 어떤 표/절/항목을 사용했는지
2. 계산에 쓰는 값(변수)과 단위/출처: 값들을 “(값, 단위, 출처)” 형태로 자연어 문장에 섞어서 적는다. (예: 문서에서 확인한 ‘신규여신평잔’, code_execution의 ‘result_text’에서 확인한 값 등)
3. 계산 단계(필요한 수식만 간단히): 단계별로 “계산 전 값 → 적용 수식 → 계산 결과” 흐름을 문장으로 설명한다. (예: `X를 Y로 나눠 Z를 구함`, `그 결과에 배점을 곱해 점수를 계산함`). `balance_score_raw = ...`처럼 프로그래밍 할당/변수명 나열 형태는 쓰지 않는다.
4. 중간 결과: 각 단계에서 나온 숫자만 짧게 제시하고, 반올림/절사 규칙이 있으면 함께 명시한다.
5. 한도·캡/제외 처리: 캡 적용 전/후 값(또는 비교 대상)과 “작은 값을 채택”처럼 적용 결과를 자연어로 설명한다.
6. 최종 수치: 최종 결론값과 왜 그렇게 되는지(적용 순서 기준) 한 문장으로 정리한다.

추가 금지:
- 함수 표기(MIN, MAX 등) 대신 “비교해서 작은 값(또는 큰 값)을 사용”처럼 자연어로 설명

## 분기
- `category_classification.categories`가 ["out_of_scope"]이면 문서 범위 밖 안내를
  요약답변에 작성하고, 근거에는 "문서 범위 밖"임을 간단히 적는다.

- **code_execution.execution_status**
  - `executed`이면 계산문제 흐름으로 작성하고, 요약답변에 최종 수치를 반영한다. (템플릿의 `[계산과정]` 포함)
  - `calculation_not_needed`이면 비계산 흐름으로 작성한다. (템플릿의 `[계산과정]` 미포함)
  - `skipped_out_of_scope`이면 비계산 흐름으로 안내하되 문서 범위 밖임을 반영한다. (템플릿의 `[계산과정]` 미포함)
  - `failed`이면 `result_text` 중심으로 작성하고, 필요한 추가 정보를 명확히 한다. (템플릿의 `[계산과정]` 포함)

## 공통
내부 필드명/status 값 등을 그대로 노출하지 않는다. 문장 수/글자 수를 임의로 줄이지 말고 필요한 만큼 상세히 쓴다.
""",
    output_key="final_response",
    before_agent_callback=chain_before_agent(log_before_agent, skip_final_response_if_out_of_scope),
    after_agent_callback=log_after_agent,
    before_model_callback=log_before_model,
    after_model_callback=log_after_model,
    tools=[],
)
