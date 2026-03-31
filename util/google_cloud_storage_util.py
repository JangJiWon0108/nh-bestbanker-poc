from google.cloud import storage
from credentials.gcp_auth import get_credentials
from config.properties import Settings
import os

# 환경 변수
settings = Settings()

# 클라이언트 객체 생성
gcs_client = storage.Client(
    credentials = get_credentials(),
    project = settings.PROJECT_ID
)

# 버킷 생성 
def create_bucket(bucket_name):
    try:
        bucket = gcs_client.bucket(bucket_name)
        
        # 버킷이 이미 존재하는지 확인
        if bucket.exists():
            print(f"정보: 버킷 '{bucket_name}'이 이미 존재합니다.")
            return bucket
        
        new_bucket = gcs_client.create_bucket(
            bucket, 
            location=settings.LOCATION
        )
        print(f"성공: 버킷 '{new_bucket.name}'이 생성되었습니다.")
        return new_bucket
    except Exception as e:
        print(f"버킷 생성 중 오류 발생: {e}")
        return None

# 데이터 업로드
def upload_blob(bucket_name, source_file_path, destination_blob_name):
    try:
        bucket = gcs_client.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        print(f"성공: {source_file_path} -> {destination_blob_name} 업로드 완료.")
    except Exception as e:
        print(f"버킷에 데이터 업로드 중 오류 발생: {e}")

# 버킷의 데이터 목록 가져오기
def get_objects(bucket_name, verbose=True):
    try:
        blobs = list(gcs_client.list_blobs(bucket_name))  # list()로 변환하여 재사용 가능하게
        
        if verbose:
            print(f"버킷 '{bucket_name}'의 객체 목록:")
            if not blobs:
                print(" - 버킷 내에 파일이 없습니다.")
            else:
                for blob in blobs:
                    print(f" - {blob.name} (크기: {blob.size} bytes)")
        
        return blobs
    except Exception as e:
        print(f"목록 확인 중 오류 발생: {e}")
        return []

# 특정 파일 삭제
def delete_object(bucket_name, blob_name):
    try:
        bucket = gcs_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        print(f"성공: 파일 '{blob_name}'이 삭제되었습니다.")

    except Exception as e:
        print(f"파일 삭제 중 오류 발생: {e}")

# 버킷 삭제
def delete_bucket(bucket_name, force_delete = False):
    try:
        bucket = gcs_client.get_bucket(bucket_name)
        bucket.delete(force=force_delete)
        print(f"성공: 버킷 '{bucket_name}'이 삭제되었습니다.")
    except Exception as e:
        print(f"버킷 삭제 중 오류 발생: {e}")


# 직접 실행 가능
if __name__ == "__main__":
    # 업로드할 파일들 경로
    base_path = "file/agent_knowledge_base"
    upload_file_list = [
        os.path.join(base_path, "corporate_loans.txt"),
        os.path.join(base_path, "deposits.txt"),
        os.path.join(base_path, "digital_banking.txt"),
        os.path.join(base_path, "retail_loans.txt"),
        os.path.join(base_path, "metadata.jsonl"),
    ]
    
    # 파일 존재 여부 확인
    for file_path in upload_file_list:
        if not os.path.exists(file_path):
            print(f"경고: 파일을 찾을 수 없습니다 - {file_path}")
            exit(1)
    
    # 버킷 생성 (이미 존재하면 무시)
    create_bucket(settings.GCS_BUCKET_NAME)
    
    # 데이터 업로드
    for file_path in upload_file_list:
        upload_blob(
            settings.GCS_BUCKET_NAME,
            file_path,
            os.path.basename(file_path)
        )
    
    # 버킷 내용 확인
    print("\n업로드된 파일 목록:")
    blobs = get_objects(settings.GCS_BUCKET_NAME, verbose=True)
