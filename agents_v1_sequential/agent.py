# 라이브러리
import os

import vertexai
from google.adk.agents import SequentialAgent

# 사용자 정의 모듈
from config.custom_log import get_logger
from agents_v1_sequential.sub_agents.calculation_requirement_agent import calculation_requirement_agent
from agents_v1_sequential.sub_agents.conversation_rewrite_agent import (
    conversation_rewrite_agent,
)
from agents_v1_sequential.sub_agents.category_classifier_agent import category_classifier_agent
from agents_v1_sequential.sub_agents.code_execution_agent import code_execution_agent
from agents_v1_sequential.sub_agents.final_response_agent import final_response_agent
from agents_v1_sequential.callbacks.logging_callbacks import (
    log_after_agent,
    log_before_agent,
    origin_query_save_callback,
)
from agents_v1_sequential.sub_agents.retrieval_agent import retrieval_agent
from config.properties import Settings
from credentials.gcp_auth import get_credentials

logger = get_logger(__name__)

# 환경 변수
settings = Settings()

# Vertex AI 초기화 (인증 설정)
credentials = get_credentials()

# 환경 변수 설정 (google.genai가 Vertex AI를 사용하도록)
# - 로컬: GOOGLE_APPLICATION_CREDENTIALS가 있으면 해당 키 파일 사용
# - 클라우드: 없으면 ADC(기본 서비스계정) 사용
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'true' if settings.GOOGLE_GENAI_USE_VERTEXAI else 'false'
os.environ['GOOGLE_CLOUD_PROJECT'] = settings.PROJECT_ID
os.environ['GOOGLE_CLOUD_LOCATION'] = settings.LOCATION

# Vertex AI 초기화 (반드시 필요)
vertexai_init_kwargs = {
    "project": settings.PROJECT_ID,
    "location": settings.LOCATION,
}
if credentials is not None:
    vertexai_init_kwargs["credentials"] = credentials
vertexai.init(**vertexai_init_kwargs)

# v1 sequential 플로우에서 사용할 sub agent 목록 구성
sub_agents: list = [
    conversation_rewrite_agent,  # 이전 대화 요약 및 질의 재작성
    category_classifier_agent,
    calculation_requirement_agent,
    retrieval_agent,
]

sub_agents.extend(
    [
        code_execution_agent,
        final_response_agent,
    ]
)

# Root Agent
root_agent = SequentialAgent(
    name="classification_flow_agent",
    description="카테고리 분류부터 계산 실행 및 최종 사용자 답변까지 수행하는 순차 워크플로우 에이전트",
    before_agent_callback=origin_query_save_callback,
    after_agent_callback=log_after_agent,
    sub_agents=sub_agents,
)