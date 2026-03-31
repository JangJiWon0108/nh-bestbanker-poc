# 라이브러리
import os
from typing import Any

import google.auth
from google.auth.transport.requests import AuthorizedSession

from credentials.gcp_auth import get_credentials

def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None or not str(v).strip():
        return default
    try:
        return float(v)
    except Exception:
        return default


def _env_str(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None:
        return default
    v = str(v).strip()
    return v if v else default

# 문서 검색
def retrieve_vertexai_search(
    project_id: str,
    location: str,
    engine_id: str,
    search_query: str,
    categories: list[str] | None = None,
    user_pseudo_id: str | None = None,
    num_previous_chunks: int = 0,
    num_next_chunks: int = 0,
    data_store_id: str | None = None,
    relevance_threshold: str | None = None,
    semantic_relevance_threshold: float | None = None,
) -> dict[str, Any]:

    # 서비스 계정 인증 객체 가져오기
    credentials = get_credentials()
    if credentials is None:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

    # REST 호출용 인증 세션 생성
    session = AuthorizedSession(credentials)

    # 카테고리 필터 문자열 구성 (빈 리스트면 필터 생략)
    normalized_categories = categories or []
    filter_value = (
        "category: ANY("
        + ", ".join(f'"{category}"' for category in normalized_categories)
        + ")"
        if normalized_categories
        else None
    )

    payload: dict[str, Any] = {
        "query": search_query,
        "offset": 0,
        "relevanceScoreSpec": {"returnRelevanceScore": True},
        "contentSearchSpec": {
            "searchResultMode": "CHUNKS",
            "chunkSpec": {
                "numPreviousChunks": num_previous_chunks,
                "numNextChunks": num_next_chunks,
            },
        },
        "queryExpansionSpec": {"condition": "AUTO"},
        "spellCorrectionSpec": {"mode": "AUTO"},
    }

    if user_pseudo_id:
        payload["userPseudoId"] = user_pseudo_id
    if filter_value:
        payload["filter"] = filter_value

    relevance_threshold = relevance_threshold or _env_str("RELEVANCE_THRESHOLD", "LOWEST") or "LOWEST"
    semantic_relevance_threshold = (
        semantic_relevance_threshold
        if isinstance(semantic_relevance_threshold, (int, float))
        else _env_float("SEMANTIC_RELEVANCE_THRESHOLD", 0.2)
    )
    payload["relevanceFilterSpec"] = {
        "keywordSearchThreshold": {
            "relevanceThreshold": relevance_threshold
        },
        "semanticSearchThreshold": {
            "semanticRelevanceThreshold": semantic_relevance_threshold
        },
    }

    data_store_id = data_store_id or _env_str("DATA_STORE_ID")
    if data_store_id:
        payload["dataStoreSpecs"] = [
            {
                "dataStore": (
                    f"projects/{project_id}/locations/{location}"
                    "/collections/default_collection/dataStores/"
                    f"{data_store_id}"
                )
            }
        ]

    search_url = (
        "https://discoveryengine.googleapis.com/v1alpha/"
        f"projects/{project_id}/locations/{location}/collections/default_collection/"
        f"engines/{engine_id}/servingConfigs/default_search:search"
    )

    # Vertex AI Search API 호출 후 전체 응답 JSON 반환
    response = session.post(search_url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


# Main
if __name__ == "__main__":

    query = input("질문 입력 >>> ")

    response = retrieve_vertexai_search(
        project_id=os.getenv("PROJECT_ID", ""),
        location=os.getenv("LOCATION", "global"),
        engine_id=os.getenv("ENGINE_ID", ""),
        search_query=query,
        categories=[],
        user_pseudo_id="test_user_id_001",
        num_previous_chunks=0,
        num_next_chunks=0,
    )

    print(response)