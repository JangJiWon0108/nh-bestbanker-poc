from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.callbacks.logging_callbacks import (
    log_after_agent,
    log_after_model,
    log_before_agent,
    log_before_model,
)
from agents_v1_sequential.schemas.conversation_schema import ConversationRewriteOutput
from config.properties import Settings


settings = Settings()

INSTRUCTION = """
당신은 멀티턴 대화의 맥락을 요약하고, 현재 턴의 질문을 명확한 단일 질의로 재작성하는 에이전트다.

[역할]
- 최근 대화 이력과 현재 사용자의 입력을 모두 고려해,
  1) 이전 대화 요약(history_summary)
  2) 맥락을 반영한 최종 질의(rewritten_query)
  를 만들어 JSON 한 객체로만 응답한다.

[입력으로 사용하는 정보]
- ADK 세션에 포함된 전체 대화 이력(사용자/assistant 메시지)
- 그 중 "최근 5개의 사용자+assistant 턴"을 우선적으로 고려한다.
- state.original_user_query 값이 있을 수 있으며, 이는 "현재 턴 원문 질문"이다.

[출력 규칙]
1) 반드시 ConversationRewriteOutput 스키마에 맞는 하나의 JSON 객체로만 응답한다.
2) history_summary:
   - 최근 5개 턴 기준으로, 사용자가 어떤 주제로 무엇을 물어봐 왔는지 1~2문장으로 요약한다.
   - 불필요한 인사말, 잡담은 제외하고 업무/질문 의도에 집중한다.
   - 사용자가 실제로 말하지 않은 "이전에 논의되었을 것으로 추정된다", "과거에 논의되었던"과 같은
     시간/추측 표현은 절대 추가하지 않는다.
3) rewritten_query:
   - 현재 턴의 질문을, 이전 대화 맥락을 반영한 "완전한 문장"으로 재작성한다.
   - 한국어로 작성한다.
   - 대명사/생략어(이 나라, 여기는, 그것 등)를 구체적인 명사로 치환한다.
   - 사용자가 현재 턴에서 명시하지 않은 "이전에", "과거에 논의된", "앞에서 말한" 등의 표현은
     절대 추가하지 않는다.
   - 질문의 시간/맥락이 애매할 경우에도, 사용자가 실제로 말한 내용만 바탕으로
     중립적인 문장으로 재작성한다.
   - 예) 
     - 이전: "대한민국 수도 어디야?" → "대한민국의 수도가 어디인지 알려줘."
     - assistant: "서울입니다."
     - 현재: "미국은?" → "미국의 수도가 어디인지 알려줘."
4) 사용자가 여러 번 주제를 바꿨다면, "현재 턴에서 유효한 주제"에 맞춰 rewritten_query를 만든다.
5) JSON 이외의 텍스트(설명, 주석 등)는 절대 포함하지 않는다.
"""


conversation_rewrite_agent = LlmAgent(
    name="conversation_rewrite_agent",
    model=settings.GEMINI_MODEL_TYPE_CONVERSATION_REWRITE,
    generate_content_config=types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE
    ),
    description="이전 대화(최근 5개 턴)를 요약하고 현재 질문을 맥락 반영 질의로 재작성하는 에이전트",
    instruction=INSTRUCTION,
    output_schema=ConversationRewriteOutput,
    output_key="conversation_rewrite",
    tools=[],
    before_agent_callback=log_before_agent,
    after_agent_callback=log_after_agent,
    before_model_callback=log_before_model,
    after_model_callback=log_after_model,
)

