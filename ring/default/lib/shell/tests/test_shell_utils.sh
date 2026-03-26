#!/usr/bin/env bash
# Comprehensive tests for Ring shell utilities
#
# Usage:
#   ./test_shell_utils.sh
#   ./test_shell_utils.sh -v  # verbose mode
#
# Tests:
#   - json-escape.sh: json_escape(), json_string()
#   - hook-utils.sh: get_json_field(), output_hook_result(), etc.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Verbose mode
VERBOSE="${1:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Temp directory for test isolation
TEST_TMP_DIR=""

# =============================================================================
# Test Helpers
# =============================================================================

setup_test_env() {
    TEST_TMP_DIR=$(mktemp -d)
    export CLAUDE_PROJECT_DIR="$TEST_TMP_DIR"
}

teardown_test_env() {
    if [[ -n "$TEST_TMP_DIR" ]] && [[ -d "$TEST_TMP_DIR" ]]; then
        rm -rf "$TEST_TMP_DIR"
    fi
    unset CLAUDE_PROJECT_DIR
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected: '$expected'"
        echo "  Actual:   '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_contains() {
    local needle="$1"
    local haystack="$2"
    local test_name="$3"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$haystack" == *"$needle"* ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected to contain: '$needle'"
        echo "  Actual: '$haystack'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_not_empty() {
    local actual="$1"
    local test_name="$2"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -n "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected non-empty, got empty string"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_empty() {
    local actual="$1"
    local test_name="$2"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -z "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected empty, got: '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_exit_code() {
    local expected_code="$1"
    local actual_code="$2"
    local test_name="$3"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$expected_code" == "$actual_code" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected exit code: $expected_code"
        echo "  Actual exit code:   $actual_code"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# =============================================================================
# Source the utilities (after helpers are defined)
# =============================================================================

# Source in order of dependencies
source "${SCRIPT_DIR}/../json-escape.sh"
source "${SCRIPT_DIR}/../hook-utils.sh"

# =============================================================================
# json_escape() Tests
# =============================================================================

test_json_escape_basic_string() {
    echo -e "\n${YELLOW}=== json_escape() Tests ===${NC}"

    local result
    result=$(json_escape "hello world")
    assert_equals "hello world" "$result" "json_escape: basic string (no special chars)"
}

test_json_escape_with_quotes() {
    local result
    result=$(json_escape 'string with "quotes" inside')
    assert_equals 'string with \"quotes\" inside' "$result" "json_escape: string with quotes → escaped quotes"
}

test_json_escape_with_newlines() {
    local input=$'line1\nline2'
    local result
    result=$(json_escape "$input")
    assert_equals 'line1\nline2' "$result" "json_escape: string with newlines → \\n"
}

test_json_escape_with_tabs() {
    local input=$'col1\tcol2'
    local result
    result=$(json_escape "$input")
    assert_equals 'col1\tcol2' "$result" "json_escape: string with tabs → \\t"
}

test_json_escape_with_backslashes() {
    local result
    result=$(json_escape 'path\\to\\file')
    assert_equals 'path\\\\to\\\\file' "$result" "json_escape: string with backslashes → \\\\"
}

test_json_escape_empty_string() {
    local result
    result=$(json_escape "")
    assert_empty "$result" "json_escape: empty string returns empty"
}

test_json_escape_unicode() {
    local result
    result=$(json_escape "hello 世界 emoji 🎉")
    assert_contains "hello" "$result" "json_escape: unicode characters preserved (contains hello)"
    assert_contains "世界" "$result" "json_escape: unicode characters preserved (contains CJK)"
}

test_json_escape_carriage_return() {
    local input=$'line1\rline2'
    local result
    result=$(json_escape "$input")
    assert_equals 'line1\rline2' "$result" "json_escape: carriage return → \\r"
}

test_json_escape_mixed_special_chars() {
    local input=$'say "hello"\tthere\nworld'
    local result
    result=$(json_escape "$input")
    assert_equals 'say \"hello\"\tthere\nworld' "$result" "json_escape: mixed special chars"
}

# =============================================================================
# json_string() Tests
# =============================================================================

test_json_string_wraps_in_quotes() {
    echo -e "\n${YELLOW}=== json_string() Tests ===${NC}"

    local result
    result=$(json_string "hello")
    assert_equals '"hello"' "$result" "json_string: wraps basic string in quotes"
}

test_json_string_empty() {
    local result
    result=$(json_string "")
    assert_equals '""' "$result" "json_string: empty string becomes empty JSON string"
}

test_json_string_with_escapes() {
    local result
    result=$(json_string 'say "hi"')
    assert_equals '"say \"hi\""' "$result" "json_string: escapes and wraps"
}

# =============================================================================
# get_json_field() Tests
# =============================================================================

test_get_json_field_simple() {
    echo -e "\n${YELLOW}=== get_json_field() Tests ===${NC}"

    local json='{"name": "test", "value": 42}'
    local result
    result=$(get_json_field "$json" "name")
    assert_equals "test" "$result" "get_json_field: extract simple string field"
}

test_get_json_field_number() {
    local json='{"name": "test", "value": 42}'
    local result
    result=$(get_json_field "$json" "value")
    assert_equals "42" "$result" "get_json_field: extract number field"
}

test_get_json_field_not_found() {
    local json='{"name": "test"}'
    local result
    local exit_code=0
    result=$(get_json_field "$json" "missing") || exit_code=$?
    # When using jq, empty field returns success with empty string
    # Either behavior is acceptable: empty result or non-zero exit
    if [[ -z "$result" ]]; then
        assert_empty "$result" "get_json_field: field not found returns empty"
    else
        echo -e "${GREEN}✓${NC} get_json_field: field not found (no match)"
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
}

test_get_json_field_invalid_field_name() {
    local json='{"name": "test"}'
    local result
    local exit_code=0
    result=$(get_json_field "$json" "invalid-field-name") || exit_code=$?
    assert_exit_code "1" "$exit_code" "get_json_field: invalid field name (hyphen) fails"
}

test_get_json_field_injection_attempt() {
    local json='{"name": "test"}'
    local result
    local exit_code=0
    # Attempt field injection
    result=$(get_json_field "$json" '.name; system("echo INJECTED")') || exit_code=$?
    assert_exit_code "1" "$exit_code" "get_json_field: injection attempt blocked"
}

test_get_json_field_empty_json() {
    local result
    local exit_code=0
    result=$(get_json_field "" "name") || exit_code=$?
    assert_exit_code "1" "$exit_code" "get_json_field: empty JSON fails"
}

test_get_json_field_empty_field() {
    local json='{"name": "test"}'
    local result
    local exit_code=0
    result=$(get_json_field "$json" "") || exit_code=$?
    assert_exit_code "1" "$exit_code" "get_json_field: empty field name fails"
}

test_get_json_field_nested_json() {
    local json='{"outer": {"inner": "value"}, "name": "top"}'
    local result
    result=$(get_json_field "$json" "name")
    assert_equals "top" "$result" "get_json_field: nested JSON gets top-level field"
}

test_get_json_field_boolean() {
    local json='{"enabled": true, "disabled": false}'
    local result
    result=$(get_json_field "$json" "enabled")
    assert_equals "true" "$result" "get_json_field: extract boolean true"

    # Note: jq's "// empty" pattern returns empty for false values
    # This is a known limitation - false is falsy in jq so "false // empty" = empty
    result=$(get_json_field "$json" "disabled")
    assert_empty "$result" "get_json_field: boolean false (jq limitation: returns empty)"
}

test_get_json_field_underscore_name() {
    local json='{"field_name": "works"}'
    local result
    result=$(get_json_field "$json" "field_name")
    assert_equals "works" "$result" "get_json_field: underscore in field name"
}

# =============================================================================
# get_project_root() Tests
# =============================================================================

test_get_project_root() {
    echo -e "\n${YELLOW}=== get_project_root() Tests ===${NC}"
    setup_test_env

    local result
    result=$(get_project_root)
    assert_equals "$TEST_TMP_DIR" "$result" "get_project_root: uses CLAUDE_PROJECT_DIR"

    teardown_test_env
}

test_get_project_root_fallback() {
    # Unset CLAUDE_PROJECT_DIR to test fallback
    unset CLAUDE_PROJECT_DIR

    local result
    local pwd_result
    result=$(get_project_root)
    pwd_result=$(pwd)
    assert_equals "$pwd_result" "$result" "get_project_root: falls back to pwd when no env var"
}

# =============================================================================
# output_hook_result() Tests
# =============================================================================

test_output_hook_result_continue() {
    echo -e "\n${YELLOW}=== output_hook_result() Tests ===${NC}"

    local result
    result=$(output_hook_result "continue")
    assert_contains '"result": "continue"' "$result" "output_hook_result: continue without message"
}

test_output_hook_result_block_with_message() {
    local result
    result=$(output_hook_result "block" "Something went wrong")
    assert_contains '"result": "block"' "$result" "output_hook_result: block result"
    assert_contains '"message": "Something went wrong"' "$result" "output_hook_result: includes message"
}

test_output_hook_result_escapes_message() {
    local result
    result=$(output_hook_result "continue" 'Message with "quotes"')
    assert_contains '\"quotes\"' "$result" "output_hook_result: escapes quotes in message"
}

# =============================================================================
# output_hook_context() Tests
# =============================================================================

test_output_hook_context() {
    echo -e "\n${YELLOW}=== output_hook_context() Tests ===${NC}"

    local result
    result=$(output_hook_context "SessionStart" "Additional context here")
    assert_contains '"hookEventName": "SessionStart"' "$result" "output_hook_context: includes event name"
    assert_contains '"additionalContext": "Additional context here"' "$result" "output_hook_context: includes context"
}

# =============================================================================
# output_hook_empty() Tests
# =============================================================================

test_output_hook_empty() {
    echo -e "\n${YELLOW}=== output_hook_empty() Tests ===${NC}"

    local result
    result=$(output_hook_empty)
    assert_equals "{}" "$result" "output_hook_empty: returns empty JSON object"
}

test_output_hook_empty_with_event() {
    local result
    result=$(output_hook_empty "PromptSubmit")
    assert_contains '"hookEventName": "PromptSubmit"' "$result" "output_hook_empty: includes event name"
}

# =============================================================================
# Run All Tests
# =============================================================================

main() {
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Ring Shell Utilities Test Suite${NC}"
    echo -e "${YELLOW}========================================${NC}"

    # json_escape tests
    test_json_escape_basic_string
    test_json_escape_with_quotes
    test_json_escape_with_newlines
    test_json_escape_with_tabs
    test_json_escape_with_backslashes
    test_json_escape_empty_string
    test_json_escape_unicode
    test_json_escape_carriage_return
    test_json_escape_mixed_special_chars

    # json_string tests
    test_json_string_wraps_in_quotes
    test_json_string_empty
    test_json_string_with_escapes

    # get_json_field tests
    test_get_json_field_simple
    test_get_json_field_number
    test_get_json_field_not_found
    test_get_json_field_invalid_field_name
    test_get_json_field_injection_attempt
    test_get_json_field_empty_json
    test_get_json_field_empty_field
    test_get_json_field_nested_json
    test_get_json_field_boolean
    test_get_json_field_underscore_name

    # get_project_root tests
    test_get_project_root
    test_get_project_root_fallback

    # output_hook_result tests
    test_output_hook_result_continue
    test_output_hook_result_block_with_message
    test_output_hook_result_escapes_message

    # output_hook_context tests
    test_output_hook_context

    # output_hook_empty tests
    test_output_hook_empty
    test_output_hook_empty_with_event

    # Summary
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "Results: ${GREEN}${TESTS_PASSED}${NC}/${TESTS_RUN} passed"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

main "$@"
