#!/usr/bin/env bash
# Neutral session-start entrypoint

set -euo pipefail

workspace_root=$(cd "$(dirname "$0")/../../.." && pwd)

printf '== AGENTS.md ==\n'
sed -n '1,120p' "$workspace_root/AGENTS.md"
