#!/usr/bin/env bash
# Copilot wrapper that honors .agentrc.json and runs session-start and hooks
set -euo pipefail

workspace_root=$(cd "$(dirname "$0")/../../.." && pwd)
cfg="$workspace_root/.agentrc.json"

if [ ! -f "$cfg" ]; then
  echo "No .agentrc.json found at $cfg"
  exit 1
fi

start_session=$("$(sh "$workspace_root/core/run" --python)" - <<PY
import json
cfg=json.load(open('.agentrc.json'))
print(cfg.get('start_session',''))
PY
)

if [ -z "$start_session" ]; then
  echo "no start_session defined in .agentrc.json"
  exit 1
fi

echo "Running workspace session-start: $start_session"
bash "$workspace_root/$start_session"

exit 0
