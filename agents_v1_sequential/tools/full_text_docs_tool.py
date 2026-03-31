from pathlib import Path
from typing import Any


OUT_OF_SCOPE_CATEGORY = "out_of_scope"
ALLOWED_CATEGORIES = {
    "retail_loan",
    "corporate_loan",
    "deposit",
    "digital_banking",
}
CATEGORY_FILE_MAP = {
    "retail_loan": "retail_loans.txt",
    "corporate_loan": "corporate_loans.txt",
    "deposit": "deposits.txt",
    "digital_banking": "digital_banking.txt",
}
BASE_DIR = Path(__file__).resolve().parents[2]
V2_DOCS_DIR = BASE_DIR / "file" / "agent_knowledge_base_v3"


def retrieve_full_text_docs_by_categories(
    search_query: str,
    categories: list[str],
    top_k: int = 5,
) -> dict[str, Any]:
    """카테고리에 해당하는 v2 원문 txt를 통째로 읽어 반환한다."""
    del search_query  # 시그니처 호환 목적(현재 구현에서는 사용하지 않음)

    normalized_categories = [category.strip() for category in categories if category.strip()]
    normalized_categories = [
        category for category in normalized_categories if category != OUT_OF_SCOPE_CATEGORY
    ]

    invalid_categories = [
        category for category in normalized_categories if category not in ALLOWED_CATEGORIES
    ]
    if invalid_categories:
        raise ValueError(f"유효하지 않은 카테고리입니다: {invalid_categories}")

    if not normalized_categories:
        return {
            "results": [],
            "total_size": 0,
            "search_scope": "full_text_v2_local",
            "message": "검색 가능한 카테고리가 없어 문서 읽기를 생략했습니다.",
        }

    results: list[dict[str, Any]] = []
    for category in normalized_categories:
        file_name = CATEGORY_FILE_MAP[category]
        target_file = V2_DOCS_DIR / file_name
        if not target_file.exists():
            raise FileNotFoundError(f"카테고리 문서를 찾을 수 없습니다: {target_file}")

        content = target_file.read_text(encoding="utf-8")
        results.append(
            {
                "doc_id": f"full_text_{category}",
                "content": content,
                "category": category,
                "title": file_name,
                "uri": str(target_file),
                "semantic_relevance": 1.0,
            }
        )

    return {
        "results": results[:top_k],
        "total_size": min(len(results), top_k),
        "search_scope": "full_text_v2_local",
    }
