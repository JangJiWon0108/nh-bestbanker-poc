"""
nh-bestbanker-poc 의 agents_v1_sequential.root_agent 를 Vertex AI Agent Engine 에 배포합니다.

저장소 루트에서 실행:
  uv run python agent_engine_deploy.py

사전 조건:
  - 루트의 .env (또는 ENV_FILE)에 config.properties.Settings 필드가 채워져 있어야 합니다.
  - gcloud ADC 로그인 또는 적절한 GCP 자격증명.
  - credentials/ 에 서비스 계정 JSON 이 있다면, 배포 tarball 에 포함됩니다.
    프로덕션에서는 ADC 만 쓰고 키 파일은 제외하는 것을 권장합니다.
"""
import os
import sys
from pathlib import Path

import vertexai
from vertexai import agent_engines

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 로컬 Settings / import 용 — 루트 .env 가 있으면 os.environ 에만 반영 (기존 값은 덮어쓰지 않음)
_env_file = ROOT / ".env"
if _env_file.is_file():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _, _v = _line.partition("=")
        _k, _v = _k.strip(), _v.strip()
        if _k and _k not in os.environ:
            os.environ[_k] = _v

PROJECT_ID = os.getenv("PROJECT_ID", "didimtest006")
# gcloud 사용자 자격증명(ADC)만 쓸 때 quota project 가 없으면 경고·쿼터 오류가 날 수 있음
if not os.environ.get("GOOGLE_CLOUD_QUOTA_PROJECT"):
    os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = PROJECT_ID
LOCATION = os.getenv("AGENT_ENGINE_REGION", "us-central1")
STAGING_BUCKET = os.getenv("AGENT_ENGINE_STAGING_BUCKET", "gs://nh-bestbanker-poc-bucket-jjw")

vertexai.init(project=PROJECT_ID, location=LOCATION)
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

from config.properties import Settings  # noqa: E402

_settings = Settings()
_env_vars = {
    k: ("true" if v is True else "false" if v is False else str(v))
    for k, v in _settings.model_dump().items()
    if v is not None and k != "GOOGLE_APPLICATION_CREDENTIALS"
}
_env_vars.update(
    {
        "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
    }
)

from agents_v1_sequential.agent import root_agent  # noqa: E402

app = agent_engines.AdkApp(agent=root_agent)

min_instances = int(os.getenv("AGENT_ENGINE_MIN_INSTANCES", "1"))
max_instances = int(os.getenv("AGENT_ENGINE_MAX_INSTANCES", "10"))
resource_limits = {
    "cpu": os.getenv("AGENT_ENGINE_CPU", "2"),
    "memory": os.getenv("AGENT_ENGINE_MEMORY", "4Gi"),
}
container_concurrency = int(os.getenv("AGENT_ENGINE_CONTAINER_CONCURRENCY", "9"))

# extra_packages 를 절대경로로 tar 에 넣으면 아카이브 최상위 폴더명이 어긋나
# ModuleNotFoundError 가 날 수 있음 → 루트 기준 상대경로로 묶음
# 에이전트는 repo 루트의 config, credentials, store, file(지식베이스) 에 의존함
_EXTRA_PACKAGES = [
    "agents_v1_sequential",
    "config",
    "credentials",
    "store",
    "file",
]

if __name__ == "__main__":
    _prev_cwd = os.getcwd()
    try:
        os.chdir(ROOT)
        remote_agent = client.agent_engines.create(
            agent=app,
            config={
                "requirements": "agents_v1_sequential/requirements-standalone.txt",
                "staging_bucket": STAGING_BUCKET,
                "extra_packages": _EXTRA_PACKAGES,
                "env_vars": _env_vars,
                "min_instances": min_instances,
                "max_instances": max_instances,
                "resource_limits": resource_limits,
                "container_concurrency": container_concurrency,
                "display_name": os.getenv(
                    "AGENT_ENGINE_DISPLAY_NAME", "nh_bestbanker_poc_sequential"
                ),
                "description": os.getenv(
                    "AGENT_ENGINE_DESCRIPTION",
                    "NH Best Banker POC — agents_v1_sequential (ADK)",
                ),
                "labels": {"env": os.getenv("AGENT_ENGINE_LABEL_ENV", "dev")},
                "agent_framework": "google-adk",
            },
        )
        print("Created:", getattr(remote_agent, "api_resource", remote_agent))
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        os.chdir(_prev_cwd)
