#!/usr/bin/env bash
# Runs once when the codespace is created. The same steps as on a laptop: uv sync, then .env.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "📦 Installing Python 3.12 and every package (uv sync)…"
uv sync

if [ -f .env ]; then
  echo "🔑 .env already exists. Leaving it as it is."
else
  # .env from .env.example, with the keys from your Codespaces secrets when you set them.
  uv run --no-sync python - <<'PY'
import os
import re
from pathlib import Path

text = Path(".env.example").read_text()
filled = []
for name in ("AGENCY_CUP_URL", "TEAM_KEY", "NVIDIA_API_KEY"):
    value = os.environ.get(name, "").strip()
    if value:
        text = re.sub(rf"^{name}=.*$", lambda _: f"{name}={value}", text, flags=re.M)
        filled.append(name)
Path(".env").write_text(text)
missing = [n for n in ("TEAM_KEY", "NVIDIA_API_KEY") if n not in filled]
print(f"🔑 Created .env{' with ' + ', '.join(filled) if filled else ''}.")
if missing:
    print(f"   Open .env and paste your {' and '.join(missing)}.")
PY
fi

echo "✅ Ready. Next: uv run python check_setup.py, then open start_here.ipynb (kernel: .venv)."
