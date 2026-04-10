#!/usr/bin/env python3
"""
로컬 .env 를 읽어 gcloud run --env-vars-file 에 넣을 YAML 을 stdout 으로 출력합니다.

Cloud Run 에는 컨테이너 안에 키 파일을 두지 않는 것이 일반적이므로
GOOGLE_APPLICATION_CREDENTIALS 는 기본적으로 제외합니다 (ADC 사용).

사용 예:
  python scripts/generate_cloud_run_env_yaml.py > /tmp/cr-env.yaml
  gcloud run services update nh-bestbanker-agent \\
    --region=asia-northeast3 \\
    --env-vars-file=/tmp/cr-env.yaml

키 파일 경로도 넣으려면:
  python scripts/generate_cloud_run_env_yaml.py --include-gcp-credentials > /tmp/cr-env.yaml

값은 JSON 호환 이스케이프로 출력해 따옴표·줄바꿈이 있어도 안전합니다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOTENV = ROOT / ".env"


def parse_dotenv(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, rest = line.partition("=")
        key = key.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            continue
        val = rest.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        out[key] = val
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate YAML for gcloud run --env-vars-file")
    ap.add_argument(
        "dotenv",
        nargs="?",
        default=str(DEFAULT_DOTENV),
        help=f"Path to .env (default: {DEFAULT_DOTENV})",
    )
    ap.add_argument(
        "--include-gcp-credentials",
        action="store_true",
        help="Include GOOGLE_APPLICATION_CREDENTIALS (usually omit on Cloud Run)",
    )
    args = ap.parse_args()
    path = Path(args.dotenv)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    data = parse_dotenv(path)
    skip = {"GOOGLE_APPLICATION_CREDENTIALS"}
    if not args.include_gcp_credentials:
        for k in skip:
            data.pop(k, None)

    # gcloud env-vars-file: flat mapping NAME: value (YAML)
    for k in sorted(data.keys()):
        v = data[k]
        sys.stdout.write(f"{k}: {json.dumps(v, ensure_ascii=False)}\n")


if __name__ == "__main__":
    main()
