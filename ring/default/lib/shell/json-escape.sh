#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# RFC 8259 compliant JSON string escaping for Ring hooks
#
# Usage:
#   source /path/to/json-escape.sh
#   escaped=$(json_escape "string with \"quotes\" and
#   newlines")
#
# Handles: backslash, quotes, tabs, carriage returns, newlines, form feeds
# Prefers jq when available for 100% compliance; falls back to awk for portability

set -euo pipefail

# JSON escape a string per RFC 8259
# Args: $1 - string to escape
# Returns: escaped string via stdout
json_escape() {
    local input="${1:-}"

    # Empty string handling
    if [[ -z "$input" ]]; then
        return 0
    fi

    # Prefer jq for 100% RFC 8259 compliance
    if command -v jq &>/dev/null; then
        # jq -Rs reads raw input, outputs as JSON string
        # sed strips the surrounding quotes that jq adds
        printf '%s' "$input" | jq -Rs . | sed 's/^"//;s/"$//'
        return 0
    fi

    # Fallback: awk-based escaping (more portable than sed for multiline)
    # Handles all JSON control characters per RFC 8259
    printf '%s' "$input" | awk '
    BEGIN {
        ORS = ""
        first_line = 1
    }
    {
        # Print newline separator BEFORE each line except the first
        if (!first_line) {
            printf "\\n"
        }
        first_line = 0

        for (i = 1; i <= length($0); i++) {
            c = substr($0, i, 1)
            if (c == "\\") printf "\\\\"
            else if (c == "\"") printf "\\\""
            else if (c == "\t") printf "\\t"
            else if (c == "\r") printf "\\r"
            else if (c == "\b") printf "\\b"
            else if (c == "\f") printf "\\f"
            else printf "%s", c
        }
    }
    '
}

# JSON escape for use in JSON string values (adds quotes)
# Args: $1 - string to escape
# Returns: "escaped string" with surrounding quotes
json_string() {
    local escaped
    escaped=$(json_escape "${1:-}")
    printf '"%s"' "$escaped"
}

# Export for subshells
export -f json_escape 2>/dev/null || true
export -f json_string 2>/dev/null || true
