from typing import Literal

from pydantic import BaseModel, Field, model_validator


CategoryLabel = Literal[
    "retail_loan",
    "corporate_loan",
    "deposit",
    "digital_banking",
    "out_of_scope",
]


class CategoryClassificationOutput(BaseModel):
    categories: list[CategoryLabel] = Field(
        description=(
            "질문이 속한 카테고리 목록. 문서 범위 밖 질문이면 반드시 "
            "['out_of_scope']만 반환한다. out_of_scope와 다른 카테고리의 동시 반환은 금지."
        )
    )
    requires_clarification: bool = Field(
        default=False,
        description=(
            "공통 섹션 질의이지만 카테고리(개인여신/기업여신/수신/디지털금융)가 "
            "질문에 없어 확인 질문이 필요한지 여부."
        ),
    )
    clarification_question: str = Field(
        default="",
        description="requires_clarification가 true일 때 사용자에게 되물을 짧은 확인 질문.",
    )

    @model_validator(mode="after")
    def validate_out_of_scope_exclusive(self) -> "CategoryClassificationOutput":
        if "out_of_scope" in self.categories and len(self.categories) != 1:
            raise ValueError("out_of_scope는 반드시 단독으로만 반환해야 합니다.")

        if self.requires_clarification:
            if not self.clarification_question.strip():
                raise ValueError("확인 질문이 필요한 경우 clarification_question을 채워야 합니다.")

        return self
