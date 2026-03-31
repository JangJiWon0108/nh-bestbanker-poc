from typing import Literal

from pydantic import BaseModel, Field


ExecutionStatus = Literal[
    "executed",
    "skipped_not_required",
    "skipped_out_of_scope",
    "failed",
]


class CodeExecutionOutput(BaseModel):
    execution_status: ExecutionStatus = Field(
        description=(
            "코드 실행 결과 상태. 계산 필요가 없으면 skipped_*, "
            "실행/완료면 executed, 실패면 failed."
        )
    )
    result_value: float | None = Field(
        default=None,
        description="계산 성공 시 최종 숫자 결과. 그 외에는 null.",
    )
    result_text: str = Field(
        default="",
        description="실행 결과 요약 또는 실패/스킵 사유.",
    )
    executed_code: str = Field(
        default="",
        description="실제로 실행한 Python 코드. 미실행 시 빈 문자열.",
    )
