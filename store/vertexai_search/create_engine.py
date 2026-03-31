# 라이브러리
from typing import List
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

# 모듈
from config.properties import Settings
from credentials.gcp_auth import get_credentials

# 환경변수
settings = Settings()

# Engine 생성 메서드
def create_vertexai_search_engine(
    project_id: str, location: str, engine_id: str, data_store_ids: List[str]
) -> str:
    
    # 서비스 계정 인증 객체 가져오기
    credentials = get_credentials()

    # 클라이언트 생성 옵션
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # 클라이언트 객체 생성
    client = discoveryengine.EngineServiceClient(
        client_options=client_options,
        credentials=credentials
    )

    # 컬렉션 리로스 경로
    # e.g. projects/{project}/locations/{location}/collections/default_collection
    parent = client.collection_path(
        project=project_id,
        location=location,
        collection="default_collection",
    )

    # Engine 객체 생성
    engine = discoveryengine.Engine(
        display_name=settings.ENGINE_ID,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
        search_engine_config=discoveryengine.Engine.SearchEngineConfig(
            search_tier=discoveryengine.SearchTier.SEARCH_TIER_ENTERPRISE,
            search_add_ons=[discoveryengine.SearchAddOn.SEARCH_ADD_ON_LLM],
        ),
        data_store_ids=data_store_ids,
    )
    
    # Engine 생성 요청 객체 생성
    request = discoveryengine.CreateEngineRequest(
        parent=parent,
        engine=engine,
        engine_id=engine_id,
    )

    # Engine 생성
    operation = client.create_engine(
        request=request,
        timeout=300.0
    )

    print(f"Engine 생성 완료 :  {operation.operation.name}")
    response = operation.result(
        timeout=600.0
    )

    # metadata 가져오기
    metadata = discoveryengine.CreateEngineMetadata(operation.metadata)

    # 결과 로깅
    print(response)
    print(metadata)

    return operation.operation.name


# main 
if __name__ == "__main__":
    engine_name = create_vertexai_search_engine(
        settings.PROJECT_ID,
        settings.LOCATION,
        settings.ENGINE_ID,
        [settings.DATA_STORE_ID]
    )
    print(f"Engine 이름 : {engine_name}")