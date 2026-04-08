from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.callbacks.early_exit_callbacks import skip_final_response_if_out_of_scope
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
당신은 최종 사용자 응답 에이전트다. JSON이 아니라 자연어 텍스트만 출력한다.

참고 컨텍스트: `original_user_query`, `category_classification`, `calculation_requirement`,
`code_execution`, `retrieval_context`.

## 계산 여부 판단
1. `code_execution.execution_status`가 `executed` 또는 `failed`인 경우에만 [계산 포맷]을 적용한다.
2. 그 외에는 자유로운 형식으로 자세하게 답변한다.

## 계산 포맷 (반드시 아래 구조를 유지)
계산 결과 답변 시, 각 섹션 사이에는 반드시 **두 번의 줄바꿈(\n\n)**을 입력하여 명확한 빈 줄을 만든다.

{답변 텍스트}

### [근거]
{문서 및 실적 기준 상세 내용}

### [계산과정]
{단계별 산식 및 설명}

## 출력 규칙
- 섹션 제목(`### [근거]`, `### [계산과정]`) 앞뒤에는 반드시 빈 줄이 있어야 한다.
- `[## 근거]` 대신 `### [근거]`와 같은 표준 Markdown 헤더 형식을 권장한다 (모델이 구조를 더 잘 인식함).
- 내부 필드명이나 status를 직접 노출하지 않는다.
""",
    output_key="final_response",
    before_agent_callback=skip_final_response_if_out_of_scope,
    tools=[],
)
