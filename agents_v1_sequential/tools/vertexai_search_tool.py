from typing import Any

from config.properties import Settings
from store.vertexai_search.retrieve import retrieve_vertexai_search


settings = Settings()

OUT_OF_SCOPE_CATEGORY = "out_of_scope"
ALLOWED_CATEGORIES = {
    "retail_loan",
    "corporate_loan",
    "deposit",
    "digital_banking",
}


def retrieve_docs_by_categories(
    search_query: str,
    categories: list[str],
) -> dict[str, Any]:
    """카테고리 필터를 적용해 Vertex AI Search 결과를 반환한다."""
    normalized_categories = [category.strip() for category in categories if category.strip()]
    # out_of_scope는 문서 검색 대상이 아니므로 필터 목록에서 제거한다.
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
            "message": "검색 가능한 카테고리가 없어 검색을 생략했습니다.",
        }

    raw_response = retrieve_vertexai_search(
        project_id=settings.PROJECT_ID,
        location=settings.LOCATION,
        engine_id=settings.ENGINE_ID,
        search_query=search_query,
        categories=normalized_categories,
        user_pseudo_id="formula_modeling_agent",
        num_previous_chunks=0,
        num_next_chunks=0,
    )

    corrected_query = raw_response.get("correctedQuery")
    raw_results = raw_response.get("results", [])
    search_scope = "category_filtered"
    simplified_results: list[dict[str, Any]] = []
    for item in raw_results:
        chunk = item.get("chunk", {})
        metadata = chunk.get("documentMetadata", {})
        model_scores = item.get("modelScores", {}) if isinstance(item, dict) else {}
        rank_signals = item.get("rankSignals", {}) if isinstance(item, dict) else {}
        relevance_score = (
            (model_scores.get("relevance_score", {}) or {}).get("values")
            if isinstance(model_scores, dict)
            else None
        )
        result_category = metadata.get("structData", {}).get("category")
        # 무필터 fallback 결과가 섞여 들어오더라도 요청 카테고리와 다른 문서는 제외한다.
        if result_category not in normalized_categories:
            continue
        simplified_results.append(
            {
                "chunk_id": chunk.get("id"),
                "content": chunk.get("content"),
                "category": result_category,
                "title": metadata.get("title"),
                "uri": metadata.get("uri"),
                "semantic_relevance": chunk.get("relevanceScore"),
                # 추가 랭킹/스코어 정보 (원본 API 응답에서 발췌)
                "relevance_score": relevance_score,
                "rank_signals": rank_signals if isinstance(rank_signals, dict) else {},
                "topicality_rank": (
                    rank_signals.get("topicalityRank") if isinstance(rank_signals, dict) else None
                ),
                "default_rank": (
                    rank_signals.get("defaultRank") if isinstance(rank_signals, dict) else None
                ),
            }
        )

    response: dict[str, Any] = {
        "results": simplified_results,
        "total_size": len(simplified_results),
        "search_scope": search_scope,
    }
    if isinstance(corrected_query, str) and corrected_query.strip():
        response["corrected_query"] = corrected_query.strip()
    return response
