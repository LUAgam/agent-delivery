#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# Common hook utilities for Ring hooks
#
# Usage:
#   source /path/to/hook-utils.sh
#   input=$(read_hook_stdin)
#   output_hook_result "continue" "Optional message"
#
# Provides:
#   - read_hook_stdin: Read JSON from stdin (Claude Code hook input)
#   - output_hook_result: Output valid hook JSON response
#   - output_hook_context: Output hook response with additionalContext
#   - get_json_field: Extract field from JSON using jq or grep fallback
#   - get_project_root: Get project root directory

set -euo pipefail

# Determine script location and source dependencies
HOOK_UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source json-escape if not already sourced
if ! declare -f json_escape &>/dev/null; then
    # shellcheck source=json-escape.sh
    source "${HOOK_UTILS_DIR}/json-escape.sh"
fi

# Read hook input from stdin
# Returns: JSON string via stdout
read_hook_stdin() {
    local input=""
    local timeout_seconds="${1:-5}"

    # Read all stdin with timeout
    if command -v timeout &>/dev/null; then
        input=$(timeout "${timeout_seconds}" cat 2>/dev/null || true)
    else
        # macOS fallback: use read with timeout
        local line
        input=""
        while IFS= read -r -t "${timeout_seconds}" line; do
            input="${input}${line}"$'\n'
        done
        # Remove trailing newline if present
        input="${input%$'\n'}"
    fi

    printf '%s' "$input"
}

# Extract a field from JSON input
# Args: $1 - JSON string, $2 - field name (top-level only, alphanumeric/underscore only)
# Returns: field value via stdout
get_json_field() {
    local json="${1:-}"
    local field="${2:-}"

    if [[ -z "$json" ]] || [[ -z "$field" ]]; then
        return 1
    fi

    # Validate field contains only safe characters (security: prevent jq injection)
    if [[ ! "$field" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
        return 1
    fi

    # Prefer jq for reliable parsing
    if command -v jq &>/dev/null; then
        printf '%s' "$json" | jq -r ".${field} // empty" 2>/dev/null
        return 0
    fi

    # Fallback: grep-based extraction (handles strings, numbers, booleans, null)
    # Try string value first: "field": "value"
    local result
    result=$(printf '%s' "$json" | grep -oE "\"${field}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | \
        sed 's/.*:[[:space:]]*"\([^"]*\)"/\1/' | head -1)

    if [[ -n "$result" ]]; then
        printf '%s' "$result"
        return 0
    fi

    # Try non-string value: "field": value (number, boolean, null)
    result=$(printf '%s' "$json" | grep -oE "\"${field}\"[[:space:]]*:[[:space:]]*[^,}\][:space:]]+" | \
        sed 's/.*:[[:space:]]*//' | head -1)

    if [[ -n "$result" ]]; then
        printf '%s' "$result"
        return 0
    fi

    return 1
}

# Get project root directory
# Uses CLAUDE_PROJECT_DIR if set, otherwise pwd
get_project_root() {
    local project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    printf '%s' "$project_dir"
}

# Output a basic hook result
# Args: $1 - result ("continue" or "block"), $2 - message (optional)
output_hook_result() {
    local result="${1:-continue}"
    local message="${2:-}"

    if [[ -n "$message" ]]; then
        local escaped_message
        escaped_message=$(json_escape "$message")
        cat <<EOF
{
  "result": "${result}",
  "message": "${escaped_message}"
}
EOF
    else
        cat <<EOF
{
  "result": "${result}"
}
EOF
    fi
}

# Output a hook response with additionalContext
# Args: $1 - hook event name, $2 - additional context string
output_hook_context() {
    local event_name="${1:-SessionStart}"
    local context="${2:-}"

    local escaped_context
    escaped_context=$(json_escape "$context")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "${event_name}",
    "additionalContext": "${escaped_context}"
  }
}
EOF
}

# Output an empty hook response (no-op)
# Args: $1 - hook event name (optional)
output_hook_empty() {
    local event_name="${1:-}"

    if [[ -n "$event_name" ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "${event_name}"
  }
}
EOF
    else
        echo '{}'
    fi
}

# Export functions for subshells
export -f read_hook_stdin 2>/dev/null || true
export -f get_json_field 2>/dev/null || true
export -f get_project_root 2>/dev/null || true
export -f output_hook_result 2>/dev/null || true
export -f output_hook_context 2>/dev/null || true
export -f output_hook_empty 2>/dev/null || true
