#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "UserPromptSubmit",\n    "additionalContext": "stage-harness status unavailable"\n  }\n}\n'
  exit 0
fi

status_json="$("${PYTHON_BIN}" "${PLUGIN_ROOT}/scripts/harness_state.py" render-status-text --allow-missing 2>/dev/null || true)"

if [[ -z "${status_json}" ]]; then
  status_text="stage-harness status unavailable"
else
  status_text="$("${PYTHON_BIN}" - <<'PY' "${status_json}" 2>/dev/null || true
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    payload = {"ok": False}

if payload.get("ok"):
    print(payload.get("text", ""))
else:
    print("stage-harness status unavailable")
PY
)"
fi

if [[ -z "${status_text}" ]]; then
  status_text="stage-harness status unavailable"
fi

escaped_context="$("${PYTHON_BIN}" -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<<"${status_text}")"

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": ${escaped_context}
  }
}
EOF
