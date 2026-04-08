from google.adk.agents.llm_agent import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor
from google.genai import types

from agents_v1_sequential.callbacks.early_exit_callbacks import skip_code_execution_if_not_needed
from config.properties import Settings


settings = Settings()


code_execution_agent = LlmAgent(
    name="code_execution_agent",
    model=settings.GEMINI_MODEL_TYPE_CODE_EXECUTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE
    ),
    description="full text 문서를 바탕으로 Python 코드를 실행해 계산 결과를 산출하는 에이전트",
    code_executor=BuiltInCodeExecutor(),
    instruction="""
당신은 계산 실행 에이전트다. 반드시 JSON 객체 하나만 반환한다.

이전 단계 결과를 활용한다:
- category_classification.categories
- calculation_requirement.calculation_requirement
- retrieval_context.retrieval_results (needs_calculation인 경우 full text 원문 목록)
- retrieval_context.retrieval_type

규칙:
0) 계산에 필요한 핵심 조건(예: 대면/비대면, 신규/기존 고객, 우대 적용 여부 등)을
   사용자 질문, 이전 에이전트 출력, 제도 문서 어디에서도 명확히 알 수 없다면
   해당 조건을 임의로 가정하지 말고 execution_status=failed로 반환한다.
   이때 result_text에는 "어떤 조건이 추가로 필요하며, 사용자가 무엇을 알려줘야 하는지"를
   한국어로 구체적으로 서술한다. 이러한 조건이 해소되기 전에는 계산을 수행하지 않는다.
1) categories가 ["out_of_scope"]이면 execution_status는 skipped_out_of_scope로 반환한다.
2) calculation_requirement가 no_calculation이면 execution_status는 calculation_not_needed로 반환한다.
3) calculation_requirement가 needs_calculation이고 retrieval_context.retrieval_type이 "full_text"인 경우에는
   retrieval_context.retrieval_results에 포함된 full text 원문만을 근거로 계산 규칙을 해석해
   Python 코드를 작성/실행한다. 문서에 없는 규칙이나 계수는 임의로 가정하지 않는다.
   제도 문서의 표에 명시된 '평잔 1백만원당 ○점' 등의 계수는 표에 적힌 값 그대로 사용하고,
   0.02를 0.026과 같이 임의의 보정·추정으로 변경하지 않는다.
   질문 내용, 이전 단계 결과, full text 어디에도 대면/비대면, 신규/기존, 우대 적용 여부 등이
   명시되어 있지 않다면 해당 상태를 추측해서 채우지 않는다.
   기본 예금 점수와 '핵심예금 기반확대' 등 추가 점수가 동시에 존재하는 경우,
   동일한 예금 잔액에 대해 계수를 두 번 곱하지 말고, 문서에 정의된 구조(기본점수 + 추가점수, 한도 포함)를 그대로 따른다.
4) 실행 코드는 변수 선언 -> 계산 -> 최종 결과를 float 출력 순서로 작성한다.
   코드 문자열을 작성할 때 역슬래시 이스케이프("\\n")를 넣지 말고 실제 줄바꿈을 사용한다.
5) 코드 실행 결과에 Traceback, SyntaxError, OUTCOME_FAILED 등 실패 신호가 있으면
   execution_status=failed로 반환하고 result_value는 null로 둔다.
6) 실행 성공 시에만 execution_status=executed, result_value에 숫자 결과를 채운다.
7) 정보 부족/오류 시 execution_status=failed, result_text에 원인을 남긴다.
   문서에서 확인한 부족 항목이 있으면 result_text에 핵심 부족 항목을 요약해 포함한다.
8) 코드 미실행인 경우 executed_code는 빈 문자열로 둔다.
9) executed_code에는 "실제로 실행한 Python 코드"만 넣는다.
    Outcome/Output/Traceback 같은 실행 로그 문자열은 executed_code에 포함하지 않는다.
10) 최종 응답은 아래 키를 가진 JSON 객체 1개만 반환한다.
    - execution_status
    - result_value
    - result_text
    - executed_code
""",
    output_key="code_execution",
    before_agent_callback=skip_code_execution_if_not_needed,
)
