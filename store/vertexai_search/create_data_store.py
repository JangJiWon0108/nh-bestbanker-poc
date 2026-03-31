# 라이브러리
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

# 모듈
from config.properties import Settings
from credentials.gcp_auth import get_credentials

# 환경변수
settings = Settings()

# data store 생성
def create_vertexai_search_data_store(
    project_id: str,
    location: str,
    data_store_id: str,
    display_name: str
) -> str:
    
    # 서비스 계정 인증 객체 가져오기
    credentials = get_credentials()

    # 클라이언트 옵션 설정
    client_options = (
        ClientOptions(api_endpoint=f"discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # 클라이언트 객체 생성
    client = discoveryengine.DataStoreServiceClient(
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

    # Data Store 객체 생성
    data_store = discoveryengine.DataStore(
        display_name=display_name,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )

    # Data Store 생성 요청 객체 생성
    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store_id=data_store_id,
        data_store=data_store,
    )

    # Data Store 생성 
    operation = client.create_data_store(
        request=request,
        timeout=300.0
    )

    print(f"Data Store 생성 완료 : {operation.operation.name}")
    response = operation.result()

    # metadata 가져오기
    metadata = discoveryengine.CreateDataStoreMetadata(operation.metadata)

    # 결과 로깅
    print(f"response : {response}")
    print(f"metadata : {metadata}")

    return operation.operation.name


# main 
if __name__ == "__main__":
    data_store_name = create_vertexai_search_data_store(
        settings.PROJECT_ID,
        settings.LOCATION,
        settings.DATA_STORE_ID,
        settings.DISPLAY_NAME
    )
    print(f"Data Store 이름 : {data_store_name}")