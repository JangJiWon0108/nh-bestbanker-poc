from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.schemas.calculation_schema import CalculationRequirementOutput
from config.properties import Settings


settings = Settings()


calculation_requirement_agent = LlmAgent(
    name="calculation_requirement_agent",
    model=settings.GEMINI_MODEL_TYPE_CALCULATION_REQUEST,
    generate_content_config=types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE
    ),
    description="질문 답변에 수식 계산이 필요한지 분류하는 에이전트",
    instruction="""
당신은 수식 계산 필요 여부 분류 에이전트다.
반드시 JSON 객체로만 응답하고 output_schema를 준수한다.

판별 기준:
1) 사용자가 '최종 수치 결과(정확한 값)'를 얻기 위해 계산을 요구하면 needs_calculation.
   - 예: "얼마야?", "몇 점이야?", "점수/금액을 계산해줘/구해줘/산출해줘"
   - 비율/증감/합계/평균/점수 계산도 '결과값을 계산해달라'는 의도면 needs_calculation.
2) 사용자가 '계산 방법/공식/수식(일반적인 계산식)'을 설명받고 싶어 하는 요청이면 no_calculation.
   - 예: "수식 알려줘", "계산식이 어떻게 돼?", "공식이 뭐야?", "계산 방법을 설명해줘"
3) 필요한 입력값이 질문에 없더라도, 사용자가 '계산해서 값이 나오게' 원하면 needs_calculation으로 판단한다.
   (필요 조건은 이후 단계(code_execution_agent)가 부족하다고 판단할 수 있다.)
4) 직전 카테고리 분류 결과가 ["out_of_scope"]라면 반드시 no_calculation.
""",
    output_schema=CalculationRequirementOutput,
    output_key="calculation_requirement",
    tools=[],
)
