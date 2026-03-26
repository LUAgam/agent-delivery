# Go Standards - Chaos Testing

> **Module:** testing-chaos.md | **Sections:** 5 | **Parent:** [index.md](index.md)

This module covers chaos testing patterns. Chaos tests verify system behavior under failure conditions like network partitions, latency, and connection loss.

> **Gate Reference:** This module is loaded by `ring:qa-analyst` at Gate 7 (Chaos Testing).

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [What Is Chaos Testing](#what-is-chaos-testing) | Purpose and when to use |
| 2 | [Chaos Test Pattern](#chaos-test-pattern-mandatory) | Toxiproxy dual-gate pattern |
| 3 | [Failure Scenarios](#failure-scenarios) | Connection loss, latency, partition |
| 4 | [Infrastructure Setup](#infrastructure-setup) | tests/utils/chaos/ organization |
| 5 | [Chaos Test Quality Gate](#chaos-test-quality-gate-mandatory) | Checklist before completion |

**Meta-sections:** [Anti-Rationalization Table](#anti-rationalization-table-chaos-testing)

---

## What Is Chaos Testing

Chaos testing verifies that your system **behaves correctly under failure conditions**. It intentionally injects faults to ensure graceful degradation.

### Key Differences from Other Test Types

| Aspect | Integration Test | Chaos Test |
|--------|------------------|------------|
| **Purpose** | Verify components work together | Verify components handle failures |
| **External deps** | Working dependencies | Failing dependencies |
| **What it finds** | Logic bugs | Resilience bugs |
| **When to run** | Every CI | Opt-in (CHAOS=1) |

### When to Use Chaos Testing

| Use Chaos For | Don't Use Chaos For |
|---------------|---------------------|
| Database connection loss | Unit tests |
| Redis cache failures | Pure business logic |
| Message queue disconnects | Validation testing |
| External API timeouts | Performance testing |
| Network partitions | Simple CRUD |

### What Chaos Tests Verify

1. **Graceful degradation** - System returns error, doesn't crash
2. **Recovery** - System resumes normal operation when fault is removed
3. **Timeout handling** - Operations fail fast, don't hang
4. **Circuit breaker** - Repeated failures trigger circuit breaker
5. **Retry logic** - Transient failures are retried correctly

---

## Chaos Test Pattern (MANDATORY)

**HARD GATE:** All chaos tests MUST use the dual-gate pattern with Toxiproxy.

### Dual-Gate Pattern

```go
//go:build integration

func TestIntegration_Chaos_Redis_ConnectionLoss(t *testing.T) {
    // Gate 1: Chaos tests disabled by default
    if os.Getenv("CHAOS") != "1" {
        t.Skip("Chaos tests disabled (set CHAOS=1)")
    }

    // Gate 2: Skip in short mode
    if testing.Short() {
        t.Skip("Skipping chaos test in short mode")
    }

    // Setup
    ctx := context.Background()
    redisC := redistestutil.SetupContainer(t)
    proxy := chaosutil.SetupToxiproxy(t, redisC)

    // Phase 1: Verify normal operation
    client := redis.NewClient(&redis.Options{Addr: proxy.ListenAddr()})
    err := client.Set(ctx, "key", "value", 0).Err()
    require.NoError(t, err, "normal operation should work")

    // Phase 2: Inject failure
    err = proxy.Disconnect()
    require.NoError(t, err, "disconnect should succeed")

    // Phase 3: Verify expected failure behavior
    err = client.Set(ctx, "key2", "value2", time.Second).Err()
    require.Error(t, err, "operation should fail when disconnected")

    // Phase 4: Restore connection
    err = proxy.Reconnect()
    require.NoError(t, err, "reconnect should succeed")

    // Phase 5: Verify recovery
    err = client.Set(ctx, "key3", "value3", 0).Err()
    require.NoError(t, err, "operation should work after recovery")
}
```

### Function Naming Convention

| Pattern | Example |
|---------|---------|
| `TestIntegration_Chaos_{Component}_{Scenario}` | `TestIntegration_Chaos_Redis_ConnectionLoss` |
| `TestIntegration_Chaos_{Component}_{FailureType}` | `TestIntegration_Chaos_Postgres_NetworkPartition` |

### Why Dual-Gate?

| Gate | Purpose | Benefit |
|------|---------|---------|
| `CHAOS=1` | Explicit opt-in | Chaos tests don't run accidentally in CI |
| `testing.Short()` | Skip in quick runs | Developers can skip during iteration |

---

## Failure Scenarios

### 1. Connection Loss

```go
func TestIntegration_Chaos_Postgres_ConnectionLoss(t *testing.T) {
    if os.Getenv("CHAOS") != "1" {
        t.Skip("Chaos tests disabled")
    }

    container := pgtestutil.SetupContainer(t)
    proxy := chaosutil.SetupToxiproxy(t, container)
    db := sql.Open("postgres", proxy.ConnectionString())

    // Normal operation
    _, err := db.Exec("SELECT 1")
    require.NoError(t, err)

    // Inject failure
    proxy.Disconnect()

    // Verify graceful failure
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    _, err = db.ExecContext(ctx, "SELECT 1")
    require.Error(t, err)

    // Recovery
    proxy.Reconnect()
    _, err = db.Exec("SELECT 1")
    require.NoError(t, err)
}
```

### 2. High Latency

```go
func TestIntegration_Chaos_Redis_HighLatency(t *testing.T) {
    if os.Getenv("CHAOS") != "1" {
        t.Skip("Chaos tests disabled")
    }

    redisC := redistestutil.SetupContainer(t)
    proxy := chaosutil.SetupToxiproxy(t, redisC)

    client := redis.NewClient(&redis.Options{
        Addr:        proxy.ListenAddr(),
        ReadTimeout: 100 * time.Millisecond, // Short timeout
    })

    // Inject 500ms latency
    err := proxy.AddLatency(500 * time.Millisecond)
    require.NoError(t, err)

    // Verify timeout behavior
    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()
    _, err = client.Get(ctx, "key").Result()
    require.Error(t, err, "should timeout with high latency")
}
```

### 3. Network Partition (Intermittent)

```go
func TestIntegration_Chaos_RabbitMQ_NetworkPartition(t *testing.T) {
    if os.Getenv("CHAOS") != "1" {
        t.Skip("Chaos tests disabled")
    }

    rabbitC := rabbittestutil.SetupContainer(t)
    proxy := chaosutil.SetupToxiproxy(t, rabbitC)

    publisher := NewPublisher(proxy.ConnectionString())

    // Intermittent failures (50% packet loss)
    proxy.AddPacketLoss(0.5)

    successCount := 0
    failCount := 0

    for i := 0; i < 10; i++ {
        err := publisher.Publish(ctx, "test-message")
        if err == nil {
            successCount++
        } else {
            failCount++
        }
    }

    // PROPERTY: Some messages should succeed, some should fail
    assert.Greater(t, successCount, 0, "some messages should succeed")
    assert.Greater(t, failCount, 0, "some messages should fail with packet loss")
}
```

### 4. Slow Close (Connection Drain)

```go
func TestIntegration_Chaos_Postgres_SlowClose(t *testing.T) {
    if os.Getenv("CHAOS") != "1" {
        t.Skip("Chaos tests disabled")
    }

    container := pgtestutil.SetupContainer(t)
    proxy := chaosutil.SetupToxiproxy(t, container)

    // Add slow close (simulates connection pool exhaustion)
    proxy.AddSlowClose(5 * time.Second)

    db := sql.Open("postgres", proxy.ConnectionString())
    db.SetMaxOpenConns(1)

    // First connection works
    _, err := db.Exec("SELECT 1")
    require.NoError(t, err)

    // Close takes 5 seconds, new connection should timeout
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    _, err = db.ExecContext(ctx, "SELECT 1")
    // May timeout waiting for connection
}
```

---

## Infrastructure Setup

### Directory Structure

```
tests/
└── utils/
    └── chaos/
        ├── toxiproxy.go      # Toxiproxy wrapper
        ├── postgres.go       # Postgres chaos helpers
        ├── redis.go          # Redis chaos helpers
        └── rabbitmq.go       # RabbitMQ chaos helpers
```

### Toxiproxy Wrapper

```go
// tests/utils/chaos/toxiproxy.go
package chaosutil

import (
    "testing"
    "time"

    "github.com/Shopify/toxiproxy/v2/client"
)

type ToxiproxyWrapper struct {
    proxy  *toxiproxy.Proxy
    client *toxiproxy.Client
}

func SetupToxiproxy(t *testing.T, upstream string) *ToxiproxyWrapper {
    t.Helper()

    client := toxiproxy.NewClient("localhost:8474")
    proxy, err := client.CreateProxy("test-proxy", "localhost:0", upstream)
    require.NoError(t, err)

    t.Cleanup(func() {
        proxy.Delete()
    })

    return &ToxiproxyWrapper{proxy: proxy, client: client}
}

func (w *ToxiproxyWrapper) ListenAddr() string {
    return w.proxy.Listen
}

func (w *ToxiproxyWrapper) Disconnect() error {
    return w.proxy.Disable()
}

func (w *ToxiproxyWrapper) Reconnect() error {
    return w.proxy.Enable()
}

func (w *ToxiproxyWrapper) AddLatency(latency time.Duration) error {
    _, err := w.proxy.AddToxic("latency", "latency", "", 1, toxiproxy.Attributes{
        "latency": latency.Milliseconds(),
    })
    return err
}

func (w *ToxiproxyWrapper) AddPacketLoss(probability float64) error {
    _, err := w.proxy.AddToxic("packet_loss", "timeout", "", 1, toxiproxy.Attributes{
        "timeout": 0,
    })
    return err
}
```

### Running Chaos Tests

```bash
# Start Toxiproxy container (required for chaos tests)
docker run -d --name toxiproxy -p 8474:8474 ghcr.io/shopify/toxiproxy:2.5.0

# Run chaos tests
CHAOS=1 go test -tags=integration -v ./tests/chaos/...

# Skip chaos tests (default behavior)
go test -tags=integration ./...

# Run specific chaos test
CHAOS=1 go test -tags=integration -v -run TestIntegration_Chaos_Redis ./...
```

---

## Chaos Test Quality Gate (MANDATORY)

**Before marking chaos tests complete:**

- [ ] All external dependencies (DB, cache, queue) have chaos tests
- [ ] All tests follow dual-gate pattern (`CHAOS=1` + `testing.Short()`)
- [ ] All tests follow naming convention `TestIntegration_Chaos_{Component}_{Scenario}`
- [ ] All tests verify: normal operation → failure → recovery
- [ ] Chaos infrastructure in `tests/utils/chaos/`
- [ ] Toxiproxy wrappers handle cleanup (`t.Cleanup`)
- [ ] All tests pass: `CHAOS=1 go test -tags=integration ./tests/chaos/...`
- [ ] No flaky tests (run 3x consecutively)

### Detection Commands

```bash
# Find services that should have chaos tests
grep -rn "redis\|postgres\|rabbitmq\|http.Client" internal/adapters --include="*.go" | grep -v "_test.go"

# Find existing chaos tests
grep -rn "TestIntegration_Chaos" --include="*_test.go" ./

# Run chaos tests only
CHAOS=1 go test -tags=integration -v -run Chaos ./...
```

---

## Output Format (Gate 7 - Chaos Testing)

```markdown
## Chaos Testing Summary

| Metric | Value |
|--------|-------|
| External dependencies | X |
| Chaos tests written | Y |
| Failure scenarios covered | Z |
| Tests passed | Y |
| Tests failed | 0 |

### Chaos Tests by Component

| Component | Scenario | Test Function | Status |
|-----------|----------|---------------|--------|
| PostgreSQL | Connection loss | TestIntegration_Chaos_Postgres_ConnectionLoss | PASS |
| PostgreSQL | High latency | TestIntegration_Chaos_Postgres_HighLatency | PASS |
| Redis | Connection loss | TestIntegration_Chaos_Redis_ConnectionLoss | PASS |
| RabbitMQ | Network partition | TestIntegration_Chaos_RabbitMQ_NetworkPartition | PASS |

### Standards Compliance

| Standard | Status | Evidence |
|----------|--------|----------|
| Dual-gate pattern | PASS | All tests check CHAOS env var |
| Naming convention | PASS | All use `TestIntegration_Chaos_*` |
| 5-phase structure | PASS | Normal → Inject → Verify → Restore → Recovery |
| Toxiproxy usage | PASS | tests/utils/chaos/ infrastructure |
```

---

## Anti-Rationalization Table (Chaos Testing)

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Integration tests cover failures" | Integration tests verify happy path. Chaos tests verify fault tolerance. | **Add chaos tests** |
| "Our infra is reliable" | All infrastructure fails eventually. Be prepared. | **Test failure scenarios** |
| "Chaos tests are slow" | They're opt-in (CHAOS=1). Run when needed. | **Add and run periodically** |
| "We have circuit breakers" | Circuit breakers need testing too. Chaos tests verify they work. | **Test circuit breakers** |
| "Monitoring will catch issues" | Monitoring finds problems in production. Chaos tests prevent them. | **Test before production** |
| "Too complex to set up" | Toxiproxy is one container. 20 minutes setup saves production incidents. | **Set up chaos infrastructure** |

---
