#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
STATE_SCRIPT="${PLUGIN_ROOT}/scripts/harness_state.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  printf '{"decision":"block","reason":"stage-harness requires python3","systemMessage":"Install python3 before using stage-harness hooks."}\n'
  exit 0
fi

input_payload="$(cat 2>/dev/null || true)"
if [[ -n "${input_payload}" ]]; then
  already_active="$("${PYTHON_BIN}" - <<'PY' "${input_payload}" 2>/dev/null || true
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    payload = {}

print("1" if payload.get("stop_hook_active") else "0")
PY
)"
  if [[ "${already_active}" == "1" ]]; then
    printf '{"decision":"continue"}\n'
    exit 0
  fi
fi

status_json="$("${PYTHON_BIN}" "${STATE_SCRIPT}" status --allow-missing 2>/dev/null || true)"
if [[ -z "${status_json}" ]]; then
  printf '{"decision":"continue"}\n'
  exit 0
fi

gate_policy="$("${PYTHON_BIN}" - <<'PY' "${status_json}" 2>/dev/null || true
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("status_error")
    raise SystemExit(0)

if not payload.get("ok"):
    print("status_error")
    raise SystemExit(0)

stage = payload.get("currentStage")
feature = payload.get("feature")
message = str(payload.get("message", ""))

if feature is None:
    if "unavailable" in message.lower():
        print("block_state")
    else:
        print("skip")
elif stage in {"CLARIFY", "SPEC", "PLAN", "EXECUTE"}:
    print("skip")
elif "unavailable" in message.lower():
    print("block_state")
else:
    print("enforce")
PY
)"

case "${gate_policy}" in
  skip)
    printf '{"decision":"continue"}\n'
    exit 0
    ;;
  block_state|status_error)
    printf '{"decision":"block","reason":"stage-harness state unavailable","systemMessage":"Repair the active stage-harness state before ending this session."}\n'
    exit 0
    ;;
esac

validation_json="$("${PYTHON_BIN}" "${STATE_SCRIPT}" validate 2>/dev/null || true)"
if [[ -z "${validation_json}" ]]; then
  printf '{"decision":"block","reason":"stage-harness validation unavailable","systemMessage":"Repair the active stage-harness validation state before ending this session."}\n'
  exit 0
fi

is_ok="$(printf '%s' "${validation_json}" | "${PYTHON_BIN}" -c 'import json,sys; data=json.load(sys.stdin); print("1" if data.get("ok") else "0")' 2>/dev/null || printf '0')"
if [[ "${is_ok}" != "1" ]]; then
  error_message="$(printf '%s' "${validation_json}" | "${PYTHON_BIN}" -c 'import json,sys; data=json.load(sys.stdin); print(data.get("error","stage-harness validation failed"))' 2>/dev/null || printf 'stage-harness validation failed')"
  "${PYTHON_BIN}" - "${error_message}" <<'PY'
import json
import sys

message = sys.argv[1]
print(json.dumps({
    "decision": "block",
    "reason": "stage-harness validation failed",
    "systemMessage": message,
}, ensure_ascii=True))
PY
  exit 0
fi

is_valid="$(printf '%s' "${validation_json}" | "${PYTHON_BIN}" -c 'import json,sys; data=json.load(sys.stdin); print("1" if data.get("valid") else "0")')"
if [[ "${is_valid}" == "1" ]]; then
  printf '{"decision":"continue"}\n'
  exit 0
fi

"${PYTHON_BIN}" - "${validation_json}" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
stage = payload.get("stage", "UNKNOWN")
missing = payload.get("missing", [])
message = f"Stage {stage} is blocked. Missing artifacts: {', '.join(missing) if missing else 'unknown'}."
print(json.dumps({
    "decision": "block",
    "reason": f"missing artifacts for {stage}",
    "systemMessage": message,
}, ensure_ascii=True))
PY
