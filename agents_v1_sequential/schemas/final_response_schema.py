from pydantic import BaseModel, Field


class FinalResponseOutput(BaseModel):
    final_answer: str = Field(
        description="사용자에게 최종으로 전달할 답변 문장."
    )
