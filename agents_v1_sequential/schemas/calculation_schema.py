from typing import Literal

from pydantic import BaseModel, Field


CalculationRequirement = Literal["needs_calculation", "no_calculation"]


class CalculationRequirementOutput(BaseModel):
    calculation_requirement: CalculationRequirement = Field(
        description=(
            "질문 응답에 수식 계산이 필요한지 여부. "
            "계산이 필요하면 needs_calculation, 필요 없으면 no_calculation."
        )
    )
