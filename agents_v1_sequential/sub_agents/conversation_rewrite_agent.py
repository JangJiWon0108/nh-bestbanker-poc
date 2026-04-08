from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.callbacks.origin_query_callbacks import (
    chain_before_agent,
    origin_query_save_callback,
)
from agents_v1_sequential.callbacks.early_exit_callbacks import (
    skip_conversation_rewrite_if_unneeded,
)
from agents_v1_sequential.schemas.conversation_schema import ConversationRewriteOutput
from config.properties import Settings


settings = Settings()

INSTRUCTION = """
당신은 멀티턴 대화의 맥락을 요약하고, 현재 턴의 질문을 명확한 단일 질의로 재작성하는 에이전트다.

[입력으로 사용하는 정보]
- ADK 세션의 대화 이력(사용자/assistant 메시지). 최근 5개 사용자+assistant 턴을 우선한다.
- state.original_user_query: 현재 턴 사용자 입력 원문.

[첫 사용자 턴 — 반드시 이렇게]
- 세션 이력에서 assistant(에이전트) 응답이 한 번도 없으면 "첫 사용자 턴"이다.
- 첫 사용자 턴이면:
  - history_summary는 반드시 빈 문자열 "" 이다. (요약할 이전 대화가 없음. 인사/상황 추측 문장을 쓰지 않는다.)
  - rewritten_query는 state.original_user_query와 동일하게 둔다. (앞뒤 공백만 제거 가능. 문장 재작성·말투 변경·부연 설명 금지.)
- 첫 턴이 아닌 경우에만 아래 멀티턴 규칙을 적용한다.

[멀티턴 — history_summary]
- 최근 5개 턴 기준으로 사용자가 어떤 주제로 무엇을 물어봤는지 1~2문장으로 요약한다.
- 업무/질문 의도 위주로 쓰고, 사용자가 말하지 않은 추측·과거 논의 표현은 넣지 않는다.

[멀티턴 — rewritten_query]
- 이전 맥락을 반영해 완전한 문장으로 재작성한다. 한국어.
- 대명사/생략을 구체 명사로 치환한다.
- 예: 이전 "대한민국 수도 어디야?" → assistant "서울입니다." 이후 현재 "미국은?" → "미국의 수도가 어디인지 알려줘."
- 현재 턴에서 유효한 주제에 맞춘다.

[공통]
- 반드시 ConversationRewriteOutput 스키마의 JSON 객체 하나만 출력한다.
- JSON 밖 설명·주석 금지.
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
    before_agent_callback=chain_before_agent(
        origin_query_save_callback, skip_conversation_rewrite_if_unneeded
    ),
)
