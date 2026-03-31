from typing import Any

from pydantic import BaseModel, Field


class RetrievalOutput(BaseModel):
    query: str = Field(description="검색에 사용한 질의")
    categories: list[str] = Field(description="검색에 사용한 카테고리")
    retrieval_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="검색 결과 목록",
    )
    retrieval_total_size: int = Field(
        default=0,
        description="검색 결과 건수",
    )
    search_scope: str = Field(
        default="category_filtered",
        description=(
            "검색 범위(category_filtered, fallback_unfiltered, "
            "out_of_scope_skip, skipped_for_full_text_modeling)"
        ),
    )
