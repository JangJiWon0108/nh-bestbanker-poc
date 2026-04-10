"""
Cloud Run / 로컬에서 ADK 웹 UI로 에이전트를 제공합니다.

에이전트 앱 이름: agents_v1_sequential (agents_v1_sequential/agent.py 의 root_agent)

로컬 실행 예:
  uv run uvicorn cloud_run_server:app --host 127.0.0.1 --port 8080

Cloud Run은 PORT 환경변수를 주입하므로:
  uvicorn cloud_run_server:app --host 0.0.0.0 --port $PORT

배포 예 (저장소 루트에서):
  gcloud run deploy nh-bestbanker-agent --source . --region REGION --project PROJECT_ID \\
    --allow-unauthenticated \\
    --set-env-vars=\"GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=...,GOOGLE_CLOUD_LOCATION=...,GEMINI_API_KEY=...,...\"

config.properties.Settings 에 필요한 변수는 Cloud Run 서비스 환경변수로 모두 넣어야 합니다
(.env 파일은 컨테이너에 없을 수 있음).
"""
from __future__ import annotations

import os
from pathlib import Path

# ADK가 agents_dir 기준으로 경로·.env를 해석하므로 작업 디렉터리를 레포 루트로 고정
_ROOT = Path(__file__).resolve().parent
os.chdir(_ROOT)

from google.adk.cli.fast_api import get_fast_api_app

_port = int(os.environ.get("PORT", "8080"))

app = get_fast_api_app(
    agents_dir=str(_ROOT),
    web=True,
    host="0.0.0.0",
    port=_port,
    trace_to_cloud=os.environ.get("ADK_TRACE_TO_CLOUD", "").lower()
    in ("1", "true", "yes"),
)
