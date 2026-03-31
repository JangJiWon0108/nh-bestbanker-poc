import json
from google.cloud import discoveryengine_v1beta as discoveryengine
from config.properties import Settings
from credentials.gcp_auth import get_credentials

settings = Settings()

def make_category_filterable(project_id, location, data_store_id):
    credentials = get_credentials()
    client = discoveryengine.SchemaServiceClient(credentials=credentials)
    schema_name = client.schema_path(project_id, location, data_store_id, "default_schema")

    # [수정] 속성 정의 방식을 가장 명시적인 형태로 변경
    schema_dict = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "keyPropertyValues": ["filterable", "indexable", "retrievable"],
                "indexable": True,
                "filterable": True,
                "retrievable": True
            },
            "structData": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "keyPropertyValues": ["filterable", "indexable", "retrievable"],
                        "indexable": True,
                        "filterable": True,
                        "retrievable": True
                    }
                }
            }
        }
    }

    schema = discoveryengine.Schema(
        name=schema_name,
        struct_schema=schema_dict
    )

    print(f"Updating schema (Forced Update) for {data_store_id}...")
    
    # 💡 핵심: 필드 마스크를 지정하여 강제로 해당 필드들을 덮어씌웁니다.
    # 만약 v1beta에 update_mask 인자가 있다면 사용하고, 없다면 일반 요청을 보냅니다.
    try:
        operation = client.update_schema(request={"schema": schema})
        print("Waiting for LRO operation... (약 1분 소요)")
        result = operation.result()
        print("Schema 업데이트 완료")
    except Exception as e:
        print(f"업데이트 중 오류 발생: {e}")

if __name__ == "__main__":
    make_category_filterable(settings.PROJECT_ID, settings.LOCATION, settings.DATA_STORE_ID)
    
    # 확인 로직
    client = discoveryengine.SchemaServiceClient(credentials=get_credentials())
    schema_name = client.schema_path(settings.PROJECT_ID, settings.LOCATION, settings.DATA_STORE_ID, "default_schema")
    current_schema = client.get_schema(name=schema_name)
    print("\n--- [최종 확인된 스키마 JSON] ---")
    print(discoveryengine.Schema.to_json(current_schema))