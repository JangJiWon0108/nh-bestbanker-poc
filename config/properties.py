import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = str(BASE_DIR / ".env")
ENV_FILE = os.getenv("ENV_FILE", DEFAULT_ENV_FILE)

class Settings(BaseSettings):
    # Gooogle Gemini
    GEMINI_API_KEY : str
    LLM_TEMPERATURE : float
    GEMINI_MODEL_TYPE_CONVERSATION_REWRITE : str
    GEMINI_MODEL_TYPE_CATEGORY : str
    GEMINI_MODEL_TYPE_CONVERSATION_REWRITE : str
    GEMINI_MODEL_TYPE_CALCULATION_REQUEST : str
    GEMINI_MODEL_TYPE_RETRIEVAL : str
    GEMINI_MODEL_TYPE_FORMULA : str
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

    # v1 에이전트 동작 옵션
    # True  : v1 sequential 플로우에서 formula_modeling_agent를 사용
    # False : formula_modeling_agent 단계를 건너뛰고 바로 code_execution_agent로 이동
    USE_V1_FORMULA_MODELING_AGENT: bool

    # env 경로
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")