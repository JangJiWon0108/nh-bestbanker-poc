import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = str(BASE_DIR / ".env")
ENV_FILE = os.getenv("ENV_FILE", DEFAULT_ENV_FILE)
# Cloud Run 등 컨테이너에 .env 가 없을 때는 파일을 쓰지 않고 OS 환경변수만 사용
_ENV_FILE_FOR_CONFIG = ENV_FILE if Path(ENV_FILE).is_file() else None


class Settings(BaseSettings):
    # Gooogle Gemini
    GEMINI_API_KEY : str
    LLM_TEMPERATURE : float
    GEMINI_MODEL_TYPE_CONVERSATION_REWRITE : str
    GEMINI_MODEL_TYPE_CATEGORY : str
    GEMINI_MODEL_TYPE_CALCULATION_REQUEST : str
    GEMINI_MODEL_TYPE_RETRIEVAL : str
    GEMINI_MODEL_TYPE_CODE_EXECUTION : str
    GEMINI_MODEL_TYPE_FINAL_RESPONSE : str
    
    # GCP VertexAI 
    GOOGLE_GENAI_USE_VERTEXAI : bool
    PROJECT_ID : str
    LOCATION : str
    DATA_STORE_ID : str
    ENGINE_ID : str
    DISPLAY_NAME : str
    # 로컬에서는 서비스계정 키 파일 경로를 지정할 수 있지만,
    # GCP(Agent Engine/Cloud Run 등)에서는 기본 자격증명(ADC)을 사용하는 것이 일반적이라 optional로 둔다.
    GOOGLE_APPLICATION_CREDENTIALS : str | None = None
    RELEVANCE_THRESHOLD : str
    SEMANTIC_RELEVANCE_THRESHOLD : float
    
    # Google Cloud Storage
    GCS_BUCKET_NAME : str

    # 로깅
    LOGGING_DETAILS: bool

    # env 경로 (.env 가 없으면 OS 환경변수만 사용 — Cloud Run)
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE_FOR_CONFIG,
        env_file_encoding="utf-8",
    )