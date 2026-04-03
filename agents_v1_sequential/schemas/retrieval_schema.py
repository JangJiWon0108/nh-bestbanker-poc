from typing import Any, Literal

from pydantic import BaseModel, Field

RetrievalType = Literal["full_text", "chunk"]


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
    retrieval_type: RetrievalType | None = Field(
        default=None,
        description=(
            "full_text: 카테고리별 로컬 원문 전체(full text 도구), "
            "chunk: Vertex AI Search 청크 검색. 검색을 하지 않은 경우 null."
        ),
    )
