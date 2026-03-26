#!/usr/bin/env bash
# Session utilities for Ring hooks
# Provides centralized session ID handling

# Sanitize session ID for safe use in filenames
# SECURITY: Prevents path traversal via malicious session IDs
# Usage: SESSION_ID_SAFE=$(sanitize_session_id "$SESSION_ID")
sanitize_session_id() {
    local session_id="${1:-$PPID}"
    # Allow only alphanumeric, hyphens, underscores; max 64 chars
    local sanitized
    sanitized=$(printf '%s' "$session_id" | tr -cd 'a-zA-Z0-9_-' | head -c 64)
    [[ -z "$sanitized" ]] && sanitized="$PPID"
    printf '%s' "$sanitized"
}

# Get safe session ID from environment or fallback
# Usage: SESSION_ID_SAFE=$(get_safe_session_id)
get_safe_session_id() {
    sanitize_session_id "${CLAUDE_SESSION_ID:-$PPID}"
}

# Export for use in subshells
export -f sanitize_session_id 2>/dev/null || true
export -f get_safe_session_id 2>/dev/null || true
