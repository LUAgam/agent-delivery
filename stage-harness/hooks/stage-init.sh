#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

render_fallback() {
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "stage-harness status unavailable"
  }
}
EOF
}

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  render_fallback
  exit 0
fi

status_json="$("${PYTHON_BIN}" "${PLUGIN_ROOT}/scripts/harness_state.py" render-status-text --allow-missing 2>/dev/null || true)"
if [[ -z "${status_json}" ]]; then
  render_fallback
  exit 0
fi

escaped_context="$("${PYTHON_BIN}" - <<'PY' "${status_json}" 2>/dev/null || true
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    payload = {"ok": False}

text = payload.get("text") if payload.get("ok") else "stage-harness status unavailable"
print(json.dumps(text or "stage-harness status unavailable"))
PY
)"

if [[ -z "${escaped_context}" ]]; then
  render_fallback
  exit 0
fi

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ${escaped_context}
  }
}
EOF
