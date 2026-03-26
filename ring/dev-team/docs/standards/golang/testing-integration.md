# Go Standards - Integration Testing

> **Module:** testing-integration.md | **Sections:** 10 | **Parent:** [index.md](index.md)

This module covers integration testing patterns with testcontainers for Go projects. Integration tests verify that components work correctly with real external dependencies.

> **Gate Reference:** This module is loaded by `ring:qa-analyst` at Gate 6 (Integration Testing).

---

## Table of Contents

| # | [Section Name](#anchor-link) | Description |
|---|------------------------------|-------------|
| 1 | [Test Pyramid](#test-pyramid) | Unit > Integration > E2E ratio |
| 2 | [File Naming Convention](#file-naming-convention-mandatory) | `*_integration_test.go` with build tags |
| 3 | [Function Naming Convention](#function-naming-convention-mandatory) | `TestIntegration_{Component}_{Scenario}` |
| 4 | [Build Tags](#build-tags-mandatory) | `//go:build integration` |
| 5 | [Testcontainers Patterns](#testcontainers-patterns-mandatory) | Container lifecycle management |
| 6 | [Parallel Test Prohibition](#parallel-test-prohibition-mandatory) | No `t.Parallel()` for integration tests |
| 7 | [Fixture Centralization](#fixture-centralization-mandatory) | `tests/utils/` organization |
| 8 | [Stub Centralization](#stub-centralization-mandatory) | `tests/utils/stubs/` patterns |
| 9 | [Guardrails (11 Anti-Patterns)](#guardrails-11-anti-patterns-mandatory) | What not to do |
| 10 | [Test Failure Analysis](#test-failure-analysis-no-greenwashing) | Root cause tracking |

**Meta-sections:** [Output Format](#output-format-gate-6---integration-testing) | [Anti-Rationalization Table](#anti-rationalization-table-integration-testing)

---

## Test Pyramid

### Principle: Unit > Integration > E2E

| Level | Scope | Speed | Coverage Focus | Typical Ratio |
|-------|-------|-------|----------------|---------------|
| **Unit** | Single function/class | Fast (ms) | Business logic, edge cases | 70% |
| **Integration** | Multiple components + real I/O | Medium (s) | Database, APIs, services | 20% |
| **E2E** | Full system | Slow (min) | Critical user journeys | 10% |

**Default to unit tests.** Integration tests are for verifying boundaries work correctly.

### When Integration Tests Are Warranted

| Code Type | Integration Test Needed | What to Test |
|-----------|------------------------|--------------|
| Repository/Adapter | Touches DB (PostgreSQL, MongoDB, Redis) | CRUD, query correctness, constraints |
| Encryption | Round-trip encrypt → store → retrieve → decrypt | Data integrity after persistence |
| Indexes/Constraints | Unique indexes, partial filters, foreign keys | Constraint violations |
| Message Brokers | RabbitMQ publish/consume | Message delivery, acknowledgment |
| External Services | HTTP clients, gRPC clients | Connection handling, retry logic |
| Transactions | Multi-step DB operations | Rollback behavior, isolation |
| Migrations | Schema changes | Forward/backward compatibility |

### When Integration Tests Are NOT Needed

| Code Type | Unit Test Sufficient | Reason |
|-----------|---------------------|--------|
| Pure functions | Filter builders, validators, mappers | No I/O, deterministic |
| Business logic | Use case orchestration with mocked repos | Logic testable in isolation |
| HTTP handlers | With mocked services | HTTP behavior testable without real DB |
| Model transformations | Entity to DTO conversions | No external dependencies |

---

## File Naming Convention (MANDATORY)

**HARD GATE:** All integration test files MUST follow the naming convention.

| Test Type | File Pattern | Build Tag |
|-----------|--------------|-----------|
| Unit | `*_test.go` | None |
| Integration | `*_integration_test.go` | `//go:build integration` |

### Correct Pattern

```go
// File: internal/adapters/postgres/user_integration_test.go
//go:build integration

package postgres_test

import (
    "testing"
)

func TestIntegration_UserRepository_Create(t *testing.T) {
    // ...
}
```

### FORBIDDEN Pattern

```go
// File: internal/adapters/postgres/user_test.go  // WRONG: missing _integration suffix
//go:build integration

package postgres_test

func TestUserRepository_Create(t *testing.T) {  // WRONG: missing TestIntegration_ prefix
    // Makes real DB calls but in unit test file
}
```

---

## Function Naming Convention (MANDATORY)

**HARD GATE:** All integration test functions MUST follow the naming convention.

| Test Type | Pattern | Example |
|-----------|---------|---------|
| Integration | `TestIntegration_{Component}_{Scenario}` | `TestIntegration_BalanceRepo_FindByAccount` |

### Naming Rules

| Rule | Example | Anti-Pattern |
|------|---------|--------------|
| No "Success" suffix | `TestIntegration_GetByID` (happy path) | `TestIntegration_GetByIDSuccess` (redundant) |
| Use `_Suffix` for variants | `TestIntegration_GetByID_NotFound` | `TestIntegration_GetByIDNotFound` |

---

## Build Tags (MANDATORY)

**HARD GATE:** All integration test files MUST have `//go:build integration` at the top.

### Correct Pattern

```go
//go:build integration

package handler_test

import "testing"

func TestIntegration_UserHandler_Create(t *testing.T) {
    // ...
}
```

### Running Tests

```bash
# Run only unit tests (default; excludes files built with integration tag)
go test ./...

# Run only integration tests (files with //go:build integration)
go test -tags=integration ./...

# Run all tests (unit + integration)
go test -tags=integration ./...
```

### Detection Command

```bash
# Find integration tests without build tag (should return 0)
find . -name "*_integration_test.go" -exec grep -L "//go:build integration" {} \;
```

---

## Testcontainers Patterns (MANDATORY)

**HARD GATE:** Integration tests MUST use testcontainers for external dependencies. Real production services are FORBIDDEN.

### Basic Pattern

```go
//go:build integration

package postgres_test

import (
    "context"
    "testing"

    "github.com/stretchr/testify/require"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
    "github.com/testcontainers/testcontainers-go/wait"
)

func TestIntegration_UserRepository_Create(t *testing.T) {
    ctx := context.Background()

    // Start container
    container, err := postgres.Run(ctx,
        "postgres:15-alpine",
        postgres.WithDatabase("test_db"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready to accept connections").
                WithOccurrence(2),
        ),
    )
    require.NoError(t, err)
    defer container.Terminate(ctx)

    // Get connection string
    connStr, err := container.ConnectionString(ctx, "sslmode=disable")
    require.NoError(t, err)

    // Run test against real container
    repo := NewUserRepository(connStr)
    user, err := repo.Create(ctx, &User{Name: "Test"})
    require.NoError(t, err)
    assert.NotEmpty(t, user.ID)
}
```

### Why Testcontainers Over docker-compose

| Service | docker-compose | Testcontainers |
|---------|---------------|----------------|
| Port | Fixed `:5432` (conflicts) | Dynamic (no conflicts) |
| Lifecycle | Manual start/stop | Automatic per test |
| Cleanup | Manual | Automatic via `t.Cleanup()` |
| CI | Requires docker-compose | Works with just Docker |

### Reusable Container Setup

Use `tests/utils/` for reusable container setup:

```go
// tests/utils/postgres/container.go
package pgtestutil

func SetupContainer(t *testing.T) *PostgresContainer {
    t.Helper()
    ctx := context.Background()

    container, err := postgres.Run(ctx, "postgres:15-alpine", ...)
    require.NoError(t, err)

    t.Cleanup(func() {
        container.Terminate(ctx)
    })

    return &PostgresContainer{
        Container: container,
        DB:        connectToDB(container),
    }
}
```

Usage in tests:

```go
func TestIntegration_UserRepository(t *testing.T) {
    container := pgtestutil.SetupContainer(t)  // cleanup is automatic
    repo := NewUserRepository(container.DB)
    // ...
}
```

---

## Parallel Test Prohibition (MANDATORY)

**HARD GATE:** Integration tests MUST NOT use `t.Parallel()`. Container state is shared.

### FORBIDDEN Pattern

```go
// ❌ FORBIDDEN: t.Parallel() in integration tests
func TestIntegration_UserCreate(t *testing.T) {
    t.Parallel()  // WRONG: causes race conditions with shared DB
    container := setupContainer(t)
    // ...
}
```

### Correct Pattern

```go
// ✅ CORRECT: Sequential integration tests
func TestIntegration_UserCreate(t *testing.T) {
    // No t.Parallel() - tests run sequentially
    container := setupContainer(t)
    // ...
}

func TestIntegration_UserUpdate(t *testing.T) {
    // No t.Parallel()
    container := setupContainer(t)
    // ...
}
```

### Detection Command

```bash
# Find t.Parallel() in integration tests (should return 0)
grep -rn "t\.Parallel()" --include="*_integration_test.go" .
```

### Why Parallel Is FORBIDDEN

| Issue | Impact |
|-------|--------|
| Shared database state | Tests corrupt each other's data |
| Container lifecycle | Container may terminate while other test runs |
| Non-deterministic failures | Flaky tests that pass/fail randomly |
| Debug difficulty | Cannot reproduce issues |

---

## Fixture Centralization (MANDATORY)

**HARD GATE:** All entity fixtures MUST be centralized in `tests/utils/<infra>/fixtures.go`. Local `createTest*` helpers are FORBIDDEN.

### Directory Structure

```
tests/
└── utils/
    ├── postgres/
    │   ├── container.go      # SetupContainer
    │   └── fixtures.go       # CreateTestAccount, CreateTestUser
    ├── redis/
    │   ├── container.go
    │   └── fixtures.go
    └── rabbitmq/
        ├── container.go
        └── fixtures.go
```

### Fixture Pattern

```go
// tests/utils/postgres/fixtures.go
package pgtestutil

type AccountParams struct {
    OrgID     string
    LedgerID  string
    Name      string
    Alias     string
}

func DefaultAccountParams() AccountParams {
    return AccountParams{
        OrgID:    uuid.NewString(),
        LedgerID: uuid.NewString(),
        Name:     "Test Account",
        Alias:    "@test",
    }
}

func CreateTestAccount(t *testing.T, db *sql.DB, orgID, ledgerID string, params *AccountParams) string {
    t.Helper()

    if params == nil {
        p := DefaultAccountParams()
        params = &p
    }

    id := uuid.NewString()
    _, err := db.Exec(`
        INSERT INTO accounts (id, org_id, ledger_id, name, alias)
        VALUES ($1, $2, $3, $4, $5)
    `, id, orgID, ledgerID, params.Name, params.Alias)
    require.NoError(t, err)

    return id
}
```

### Usage in Tests

```go
func TestIntegration_AccountRepository_Find(t *testing.T) {
    container := pgtestutil.SetupContainer(t)

    orgID := uuid.NewString()
    ledgerID := uuid.NewString()
    params := pgtestutil.DefaultAccountParams()
    params.Name = "Custom Name"
    accountID := pgtestutil.CreateTestAccount(t, container.DB, orgID, ledgerID, &params)

    // Test
    repo := NewAccountRepository(container.DB)
    account, err := repo.Find(ctx, accountID)
    require.NoError(t, err)
    assert.Equal(t, "Custom Name", account.Name)
}
```

### FORBIDDEN Pattern

```go
// ❌ FORBIDDEN: Local helper inside test file
func createTestAccount(name string) *mmodel.Account {
    return &mmodel.Account{Name: testutils.Ptr(name)}
}

func TestIntegration_Something(t *testing.T) {
    account := createTestAccount("test")  // WRONG: local helper
}
```

---

## Stub Centralization (MANDATORY)

**HARD GATE:** All stubs for external dependencies MUST be centralized in `tests/utils/stubs/`.

### Stubs vs Mocks

| Type | Location | Use Case |
|------|----------|----------|
| **Mocks** | `internal/mocks/` (generated) | Unit tests - verify interactions |
| **Stubs** | `tests/utils/stubs/` | Fixed behavior, dependency "just works" |

### Stub Pattern

```go
// tests/utils/stubs/ports.go
package stubs

type StubLogger struct {
    entries []LogEntry
}

func NewStubLogger() *StubLogger {
    return &StubLogger{}
}

func (l *StubLogger) Info(msg string, fields ...any) {
    l.entries = append(l.entries, LogEntry{Level: "info", Msg: msg})
}

func (l *StubLogger) Error(msg string, fields ...any) {
    l.entries = append(l.entries, LogEntry{Level: "error", Msg: msg})
}

func (l *StubLogger) GetEntries() []LogEntry {
    return l.entries
}
```

### Usage in Tests

```go
import "github.com/LerianStudio/midaz/v3/tests/utils/stubs"

func TestUseCase_CreateAccount(t *testing.T) {
    logger := stubs.NewStubLogger()
    repo := mocks.NewMockAccountRepository(ctrl)

    uc := NewCreateAccountUseCase(repo, logger)
    // ...

    // Verify logging if needed
    entries := logger.GetEntries()
    assert.Len(t, entries, 1)
}
```

---

## Guardrails (11 Anti-Patterns) (MANDATORY)

**HARD GATE:** Before completing any integration test, verify NONE of these anti-patterns exist.

| # | Anti-Pattern | Detection | Impact | Fix |
|---|--------------|-----------|--------|-----|
| 1 | **Hardcoded ports** | `grep -rn ":5432\|:6379\|:27017"` | Port conflicts in CI | Use testcontainers dynamic ports |
| 2 | **Shared database state** | Tests depend on prior test data | Flaky tests | Each test creates own data |
| 3 | **time.Sleep for sync** | `grep "time.Sleep"` | Slow, unreliable | Use wait strategies |
| 4 | **os.Setenv pollution** | `grep "os.Setenv"` | Env leaks between tests | Replace with `t.Setenv()` |
| 5 | **Global test state** | Package-level variables | State leaks | Instance per test |
| 6 | **Missing build tag** | `//go:build integration` absent | Tests run with unit tests | Always add build tag |
| 7 | **t.Parallel() usage** | `grep "t.Parallel()"` | State conflicts | Remove all `t.Parallel()` |
| 8 | **Local fixtures** | `createTest*` in test files | Duplication | Use `tests/utils/` |
| 9 | **Network-dependent tests** | Tests call external APIs | Flaky, slow | Mock or use testcontainers |
| 10 | **Missing timeout** | No `context.WithTimeout` | Tests hang forever | Always set timeout |
| 11 | **Production credentials** | Real passwords in tests | Security risk | Use test-only credentials |

### Detection Script

```bash
echo "Checking for integration test anti-patterns..."

# 1. Hardcoded ports
echo "1. Hardcoded ports:"
grep -rn ":5432\|:6379\|:27017\|:5672" --include="*_integration_test.go" . | grep -v "// allowed:" || echo "   None found"

# 2. t.Parallel() in integration tests
echo "2. t.Parallel() usage:"
grep -rn "t\.Parallel()" --include="*_integration_test.go" . || echo "   None found"

# 3. Missing build tags
echo "3. Missing build tags:"
find . -name "*_integration_test.go" -exec grep -L "//go:build integration" {} \; || echo "   None found"

# 4. time.Sleep usage
echo "4. time.Sleep usage:"
grep -rn "time\.Sleep" --include="*_integration_test.go" . || echo "   None found"

# 5. os.Setenv usage
echo "5. os.Setenv usage:"
grep -rn "os\.Setenv" --include="*_integration_test.go" . || echo "   None found"
```

---

## Test Failure Analysis (No Greenwashing)

**HARD GATE:** Never weaken tests to make them pass.

### Decision Tree

```text
Test failed -> Is the assertion correct?
              |
              +-- YES -> Is app behavior correct?
              |          |
              +-- NO (test bug) -> Fix the test, document why
                         |
                         +-- YES (wrong expectation) -> Fix test
                         +-- NO (app bug) -> Keep test RED, report bug
```

### Response to Test Failure

| Scenario | Correct Action |
|----------|----------------|
| Test is wrong | Fix test, explain the mistake |
| App has bug | **Keep test failing**, document bug |
| Environment issue | Fix environment, re-run |

### Bug Report Format (When Keeping Test RED)

```markdown
BUG IDENTIFIED (not test error):
- **Test:** TestIntegration_AccountRepository_FindByAlias
- **Expected:** Account returned when alias exists
- **Actual:** Returns nil without error
- **Root cause:** Query missing WHERE clause for org_id
-> Keeping test RED. Fix required in application code.
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Test is too strict" | Strict tests catch bugs early | **Keep the assertion** |
| "Works in production" | Production may have hidden bugs | **Trust the test** |
| "Intermittent failure" | Flaky = broken. Fix the root cause. | **Fix the test or code** |
| "Edge case won't happen" | Edge cases cause production incidents | **Keep edge case tests** |
| "Time pressure" | Shipping bugs costs more than fixing tests | **Fix before merge** |

---

## Integration Test Quality Gate (MANDATORY)

**Before marking integration tests complete:**

- [ ] All files named `*_integration_test.go`
- [ ] All files have `//go:build integration` tag
- [ ] All functions named `TestIntegration_*`
- [ ] No `t.Parallel()` in any integration test
- [ ] All containers use testcontainers (no production deps)
- [ ] All containers cleaned up via `t.Cleanup()`
- [ ] All fixtures from `tests/utils/`, no local helpers
- [ ] All stubs from `tests/utils/stubs/`, no local mocks
- [ ] No hardcoded ports, no `time.Sleep`
- [ ] Tests pass 3x consecutively (no flaky tests)

---

## Output Format (Gate 6 - Integration Testing)

```markdown
## Integration Testing Summary

| Metric | Value |
|--------|-------|
| External dependencies | X |
| Integration tests written | Y |
| Tests passed | Y |
| Tests failed | 0 |
| Flaky tests detected | 0 |

### Tests by Component

| Component | Test File | Tests | Status |
|-----------|-----------|-------|--------|
| UserRepository | user_integration_test.go | 5 | PASS |
| AccountRepository | account_integration_test.go | 8 | PASS |
| MessageQueue | queue_integration_test.go | 3 | PASS |

### Standards Compliance

| Standard | Status | Evidence |
|----------|--------|----------|
| Testcontainers used | PASS | postgres, redis containers |
| No t.Parallel() | PASS | grep returns 0 matches |
| Build tags | PASS | All files have //go:build integration |
| Fixture centralization | PASS | tests/utils/postgres/fixtures.go |
```

---

## Anti-Rationalization Table (Integration Testing)

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Unit tests cover this" | Unit tests mock dependencies | **Write integration tests** |
| "Testcontainers is slow" | Speed < correctness | **Use testcontainers** |
| "Database tests are fragile" | Fragile = poorly written | **Fix test isolation** |
| "docker-compose is easier" | Easier now, port conflicts later | **Use testcontainers** |
| "No time for integration tests" | Integration bugs cost 10x more | **Write integration tests** |
| "t.Parallel() makes tests faster" | Faster but flaky | **Remove t.Parallel()** |
| "Local helpers are convenient" | Convenience causes duplication | **Use tests/utils/** |

---
