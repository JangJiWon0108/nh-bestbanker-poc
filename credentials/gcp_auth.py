from __future__ import annotations

import os
from pathlib import Path

from google.oauth2 import service_account

def get_credentials():

    # 우선순위:
    # 1) 표준 환경변수 GOOGLE_APPLICATION_CREDENTIALS (로컬에서 주로 사용)
    # 2) (레거시) config.properties.Settings에서 읽기
    auth_json_file_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not auth_json_file_path:
        try:
            from config.properties import Settings  # 레거시 호환

            auth_json_file_path = Settings().GOOGLE_APPLICATION_CREDENTIALS
        except Exception:
            auth_json_file_path = None
    
    # GCP 런타임(Agent Engine/Cloud Run/GCE 등)에서는 기본 자격증명(ADC)을 사용하므로
    # 키 파일 경로가 없으면 None을 반환해 google SDK들이 ADC를 사용하도록 한다.
    if not auth_json_file_path:
        return None

    try:
        key_path = Path(auth_json_file_path)
        if not key_path.exists():
            raise FileNotFoundError(
                f"서비스 계정 키 파일을 찾을 수 없습니다: {auth_json_file_path}"
            )
        credentials = service_account.Credentials.from_service_account_file(
            auth_json_file_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform'] 
        )
        return credentials
    except Exception as e:
        print(f"인증 객체 생성 중 오류 발생: {e}")
        raise 