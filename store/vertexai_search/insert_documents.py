from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

# 사용자 정의 모듈 
from config.properties import Settings
from credentials.gcp_auth import get_credentials

# 환경변수
settings = Settings()

# gcs -> VertexAI Search Data Store
def insert_gcs_to_data_store(
        project_id: str,
        location: str,
        data_store_id: str,
        gcs_uri: str, 
        import_type: str,
        data_schema: str
):
    
    # 서비스 계정 인증 객체 가져오기
    credentials = get_credentials()

    # 클라이언트 생성 옵션
    client_options = (
        ClientOptions(api_endpoint=f"discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # 클라이언트 객체 생성
    client = discoveryengine.DocumentServiceClient(
        client_options=client_options,
        credentials=credentials
    )

    #  branch 리소스 경로
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch",
    )

    # 수집 타입 설정 (# INCREMENTAL: 기존 데이터에 추가 / FULL: 전체 교체)
    if import_type == "FULL":
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.FULL
    elif import_type == "INCREMENTAL":
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL

    # 수집 요청 객체 생성
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri],
            data_schema=data_schema,
        ),
        reconciliation_mode=reconciliation_mode,
    )

    # 데이터 수집 시작
    print(f"데이터 수집 시작: {gcs_uri}")
    operation = client.import_documents(
        request=request,
        timeout=300.0
    )
    
    print(f"작업 진행 중... (Operation: {operation.operation.name})")
    response = operation.result(
        timeout=600.0
    )

    #  메타데이터 확인
    metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)
    
    print("--- 수집 완료 ---")
    print(f"응답 결과: {response}")
    print(f"메타데이터: {metadata}")
    
    return response, metadata

# 사용 예시
if __name__ == "__main__":

    target_gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/metadata.jsonl"

    result, meta = insert_gcs_to_data_store(
        settings.PROJECT_ID,
        settings.LOCATION,
        settings.DATA_STORE_ID,
        gcs_uri = target_gcs_uri,
        import_type = "FULL",    # 타입 
        data_schema = "document"  # 데이터스키마 - 비정형은 content, json은  document
    )

    print(result)
    print(meta)

