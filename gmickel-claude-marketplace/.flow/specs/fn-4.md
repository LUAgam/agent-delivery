# fn-4 LLM-powered context builder for Codex reviews

## Overview

Currently `gather_context_hints()` uses pure Python (regex symbol extraction + local reference finding). Consider replacing with an LLM-powered context builder using a cheaper model.

## Scope

- Add new function `gather_context_with_llm()`
- Use `gpt-5.2-codex` (medium reasoning) for context gathering
- Keep `gpt-5.2` (high reasoning) for actual review
- New env var: `FLOW_CODEX_CONTEXT_MODEL` (default: gpt-5.2-codex)
- Two Codex calls per review: context first, review second

## Approach

1. First call (cheap): "Given these changed files, what related files should the reviewer see?"
2. Second call (expensive): Actual Carmack-level review with gathered context

## Quick commands

- `plugins/flow-next/scripts/smoke_test.sh`

## Acceptance

- [ ] New env var `FLOW_CODEX_CONTEXT_MODEL` works
- [ ] Context gathering uses cheaper model
- [ ] Review still uses `FLOW_CODEX_MODEL` (high reasoning)
- [ ] Backwards compatible (single model still works)

## References

- Current impl: `flowctl.py:gather_context_hints()` (lines 492-534)
- Codex exec: `flowctl.py:run_codex_exec()` (lines 568+)
