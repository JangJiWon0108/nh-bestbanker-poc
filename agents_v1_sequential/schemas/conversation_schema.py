from pydantic import BaseModel, Field


class ConversationRewriteOutput(BaseModel):
    """대화 이력 요약 및 재작성 질의 스키마."""

    history_summary: str = Field(
        description="이전 대화(최근 5개 턴 기준)를 한두 문장으로 요약한 내용",
    )
    rewritten_query: str = Field(
        description="이전 대화 맥락과 현재 질문을 모두 반영해 재작성한 최종 질의",
    )

