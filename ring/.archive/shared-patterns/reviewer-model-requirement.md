# Reviewer Agent Dispatch

**Version:** 2.0.0
**Applies to:** All reviewer agents (ring:code-reviewer, ring:business-logic-reviewer, ring:security-reviewer, ring:test-reviewer, ring:nil-safety-reviewer)

---

## Orchestrator Requirement

When calling ANY reviewer agent, dispatch via Task tool:

```python
Task(subagent_type="ring:{reviewer-name}", ...)
```

### Why Specialized Reviewers Are Required

| Review Capability | Why Specialized Agents |
|------------------|----------------------|
| **Complex code tracing** | Tracing data flows across components, following function calls, understanding state changes |
| **Pattern recognition** | Identifying subtle design patterns, anti-patterns, and inconsistencies |
| **Mental execution** | Walking through code with concrete scenarios to verify correctness |
| **Context integration** | Understanding full file context, adjacent functions, ripple effects |
| **Security analysis** | Identifying attack vectors, OWASP vulnerabilities, cryptographic weaknesses |
| **Business logic verification** | Tracing business rules, edge cases, state machine transitions |

**Domain-Specific Rationale:**

- **Code Reviewer:** Requires tracing algorithmic flow, context propagation, and codebase consistency patterns
- **Business Logic Reviewer:** Requires mental execution analysis with concrete scenarios and full file context
- **Security Reviewer:** Requires deep vulnerability detection, OWASP Top 10 coverage, and cryptographic evaluation
- **Test Reviewer:** Requires analyzing test quality, coverage gaps, and test anti-patterns
- **Nil-Safety Reviewer:** Requires tracing nil propagation through call chains and identifying risk patterns
