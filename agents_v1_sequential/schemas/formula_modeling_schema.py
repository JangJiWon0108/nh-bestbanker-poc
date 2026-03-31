from typing import Literal

from pydantic import BaseModel, Field


FormulaModelingStatus = Literal[
    "modeled",
    "not_required",
    "out_of_scope",
    "insufficient_data",
]


class FormulaModelingOutput(BaseModel):
    modeling_status: FormulaModelingStatus = Field(
        description=(
            "수식 모델링 상태. 계산 불필요면 not_required, "
            "도메인 외 질문이면 out_of_scope, 근거 부족이면 insufficient_data."
        )
    )
    categories: list[str] = Field(
        description="카테고리 분류 결과. out_of_scope는 단독으로만 포함되어야 한다."
    )
    formula_expression: str = Field(
        default="",
        description="계산에 사용할 수식(예: (A/B)*100). 계산 불필요 시 빈 문자열.",
    )
    variable_definitions: dict[str, str] = Field(
        default_factory=dict,
        description="수식 변수명과 의미/출처 매핑",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="수식 모델링 과정에서 둔 가정",
    )
