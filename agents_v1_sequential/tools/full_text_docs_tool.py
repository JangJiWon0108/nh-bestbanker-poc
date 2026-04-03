from pathlib import Path
from typing import Any

from google.adk.tools.tool_context import ToolContext

from agents_v1_sequential.tools.retrieval_state_helper import commit_retrieval_context_to_state


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
    tool_context: ToolContext,
    top_k: int = 5,
) -> dict[str, Any]:
    """카테고리에 해당하는 v2 원문 txt를 통째로 읽어 반환한다."""
    normalized_categories = [category.strip() for category in categories if category.strip()]
    normalized_categories = [
        category for category in normalized_categories if category != OUT_OF_SCOPE_CATEGORY
    ]

    # LLM이 가끔 ALLOWED_CATEGORIES 외 라벨을 만들 수 있어,
    # 도구 레벨에서 유효한 카테고리만 남기고 나머지는 무시한다.
    normalized_categories = [
        category for category in normalized_categories if category in ALLOWED_CATEGORIES
    ]

    if not normalized_categories:
        empty: dict[str, Any] = {
            "query": search_query,
            "categories": [],
            "retrieval_results": [],
            "retrieval_total_size": 0,
            "retrieval_type": "full_text",
        }
        commit_retrieval_context_to_state(tool_context, empty)
        return empty

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

    payload: dict[str, Any] = {
        "query": search_query,
        "categories": normalized_categories,
        "retrieval_results": results[:top_k],
        "retrieval_total_size": min(len(results), top_k),
        "retrieval_type": "full_text",
    }
    commit_retrieval_context_to_state(tool_context, payload)
    return payload
