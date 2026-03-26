# Go Standards - Property-Based Testing

> **Module:** testing-property.md | **Sections:** 5 | **Parent:** [index.md](index.md)

This module covers property-based testing patterns. Property-based tests verify that **invariants always hold** across many generated inputs.

> **Gate Reference:** This module is loaded by `ring:qa-analyst` at Gate 5 (Property-Based Testing).

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [What Is Property-Based Testing](#what-is-property-based-testing) | Purpose and when to use |
| 2 | [Property Function Pattern](#property-function-pattern-mandatory) | testing/quick.Check syntax |
| 3 | [Common Properties](#common-properties) | Invariants to test |
| 4 | [Integration vs Unit Properties](#integration-vs-unit-properties) | When to use each |
| 5 | [Property Test Quality Gate](#property-test-quality-gate-mandatory) | Checklist before completion |

**Meta-sections:** [Anti-Rationalization Table](#anti-rationalization-table-property-testing)

---

## What Is Property-Based Testing

Property-based testing verifies that **invariant properties always hold** across hundreds of automatically generated inputs.

### Key Differences from Other Test Types

| Aspect | Unit Test | Fuzz Test | Property-Based Test |
|--------|-----------|-----------|---------------------|
| **What you define** | Input + Expected output | Seed corpus | Property (invariant) |
| **What it verifies** | Specific case works | No crash | Property always true |
| **Number of inputs** | 5-20 | Millions | Hundreds |
| **Speed** | Fast | Varies | Fast |

### Examples of Properties

| Domain | Property |
|--------|----------|
| Math | `a + b == b + a` (commutativity) |
| Money | `amount.Add(other).Value >= 0` (non-negative result) |
| Validation | `Validate(x) returns error OR x is valid` (no false positives) |
| Serialization | `Unmarshal(Marshal(x)) == x` (roundtrip) |
| Jitter | `FullJitter(duration) >= 0` (always non-negative) |

### When to Use Property-Based vs Table-Driven

| Use Property-Based When | Use Table-Driven When |
|-------------------------|----------------------|
| Testing invariants across many inputs | Testing specific known scenarios |
| Verifying "never panics" guarantees | Testing error messages |
| Mathematical properties | Testing specific edge cases |
| Input validation exhaustiveness | Documenting expected behavior |

---

## Property Function Pattern (MANDATORY)

**HARD GATE:** All property-based tests MUST use `testing/quick.Check`.

### Required Pattern

```go
import "testing/quick"

func TestProperty_FullJitter_AlwaysPositive(t *testing.T) {
    property := func(duration time.Duration) bool {
        // PROPERTY: Jitter is always non-negative
        return FullJitter(duration) >= 0
    }

    err := quick.Check(property, nil)
    require.NoError(t, err)
}
```

### Function Naming Convention

| Level | Pattern | Example |
|-------|---------|---------|
| Unit | `TestProperty_{Subject}_{Property}` | `TestProperty_Money_AdditionCommutative` |
| Integration | `TestIntegration_Property_{Subject}_{Property}` | `TestIntegration_Property_Account_UniqueAlias` |

### Configuration Options

```go
func TestProperty_WithConfig(t *testing.T) {
    config := &quick.Config{
        MaxCount: 1000,  // Number of iterations (default: 100)
    }

    property := func(x int) bool {
        return SomeProperty(x)
    }

    err := quick.Check(property, config)
    require.NoError(t, err)
}
```

---

## Common Properties

### 1. Commutativity

```go
func TestProperty_Money_AdditionCommutative(t *testing.T) {
    property := func(a, b int64) bool {
        m1 := NewMoney(a, "USD")
        m2 := NewMoney(b, "USD")
        // a + b == b + a
        return m1.Add(m2).Equals(m2.Add(m1))
    }

    require.NoError(t, quick.Check(property, nil))
}
```

### 2. Roundtrip (Marshal/Unmarshal)

```go
func TestProperty_User_JSONRoundtrip(t *testing.T) {
    property := func(name string, age uint8) bool {
        original := User{Name: name, Age: int(age)}

        data, err := json.Marshal(original)
        if err != nil {
            return true // Skip invalid inputs
        }

        var decoded User
        if json.Unmarshal(data, &decoded) != nil {
            return true
        }

        // PROPERTY: Unmarshal(Marshal(x)) == x
        return original.Name == decoded.Name && original.Age == decoded.Age
    }

    require.NoError(t, quick.Check(property, nil))
}
```

### 3. Idempotency

```go
func TestProperty_Normalize_Idempotent(t *testing.T) {
    property := func(input string) bool {
        once := Normalize(input)
        twice := Normalize(once)
        // PROPERTY: f(f(x)) == f(x)
        return once == twice
    }

    require.NoError(t, quick.Check(property, nil))
}
```

### 4. Non-Negative Results

```go
func TestProperty_Jitter_AlwaysPositive(t *testing.T) {
    property := func(duration int64) bool {
        d := time.Duration(duration)
        // PROPERTY: Result is always non-negative
        return FullJitter(d) >= 0
    }

    require.NoError(t, quick.Check(property, nil))
}
```

### 5. Validation Consistency

```go
func TestProperty_Organization_FieldLengths(t *testing.T) {
    property := func(name, code string) bool {
        // Skip unrealistic inputs
        if len(name) > 256 || len(code) > 10 {
            return true
        }

        org, err := NewOrganization(name, code)
        if err != nil {
            // PROPERTY: Invalid inputs return error (don't panic)
            return true
        }

        // PROPERTY: Valid organizations have non-empty ID
        return org.ID != ""
    }

    require.NoError(t, quick.Check(property, nil))
}
```

### 6. Invariant Preservation

```go
func TestProperty_Account_BalanceNeverNegative(t *testing.T) {
    property := func(initialBalance, debitAmount int64) bool {
        if initialBalance < 0 || debitAmount < 0 {
            return true // Skip negative inputs
        }

        account := NewAccount(initialBalance)
        err := account.Debit(debitAmount)

        // PROPERTY: Balance is never negative after debit
        if err == nil {
            return account.Balance() >= 0
        }
        return true // Error is acceptable for insufficient funds
    }

    require.NoError(t, quick.Check(property, nil))
}
```

---

## Integration vs Unit Properties

### Unit-Level Properties (Gate 5)

Test pure functions without external dependencies:

```go
// File: internal/domain/money_test.go
func TestProperty_Money_AdditionCommutative(t *testing.T) {
    // No database, no external calls
    property := func(a, b int64) bool {
        return NewMoney(a, "USD").Add(NewMoney(b, "USD")).Equals(
               NewMoney(b, "USD").Add(NewMoney(a, "USD")))
    }
    require.NoError(t, quick.Check(property, nil))
}
```

### Integration-Level Properties (Gate 6)

Test properties that require database or external systems:

```go
// File: internal/adapters/postgres/account_integration_test.go
//go:build integration

func TestIntegration_Property_Account_DuplicateAlias(t *testing.T) {
    container := pgtestutil.SetupContainer(t)
    repo := NewAccountRepository(container.DB)

    property := func(alias string) bool {
        if len(alias) > 100 || alias == "" {
            return true // Skip invalid aliases
        }

        ctx := context.Background()
        orgID := uuid.NewString()

        // Create first account
        _, err1 := repo.Create(ctx, &Account{OrgID: orgID, Alias: alias})
        if err1 != nil {
            return true // Skip if first creation fails
        }

        // PROPERTY: Duplicate alias in same org returns error
        _, err2 := repo.Create(ctx, &Account{OrgID: orgID, Alias: alias})
        return errors.Is(err2, ErrDuplicateAlias)
    }

    require.NoError(t, quick.Check(property, nil))
}
```

---

## Property Test Quality Gate (MANDATORY)

**Before marking property tests complete:**

- [ ] All domain invariants have property tests
- [ ] All mathematical operations tested for commutativity/associativity where applicable
- [ ] All serialization tested for roundtrip property
- [ ] All normalization functions tested for idempotency
- [ ] All tests follow naming convention `TestProperty_{Subject}_{Property}`
- [ ] All tests pass: `go test ./... -run Property`
- [ ] No flaky tests (run 3x consecutively)

### Detection Commands

```bash
# Find domain entities that should have property tests
grep -rn "type.*struct" internal/domain --include="*.go" | grep -v "_test.go"

# Find existing property tests
grep -rn "TestProperty_\|quick.Check" --include="*_test.go" ./internal

# Run property tests only
go test ./... -run Property -v
```

---

## Output Format (Gate 5 - Property-Based Testing)

```markdown
## Property-Based Testing Summary

| Metric | Value |
|--------|-------|
| Domain entities | X |
| Properties tested | Y |
| Iterations per property | 100 |
| Properties passed | Y |
| Properties failed | 0 |

### Properties by Domain

| Domain | Property | Test Function | Status |
|--------|----------|---------------|--------|
| Money | Addition commutative | TestProperty_Money_AdditionCommutative | PASS |
| Money | JSON roundtrip | TestProperty_Money_JSONRoundtrip | PASS |
| Jitter | Always positive | TestProperty_Jitter_AlwaysPositive | PASS |
| Account | Balance never negative | TestProperty_Account_BalanceNeverNegative | PASS |

### Standards Compliance

| Standard | Status | Evidence |
|----------|--------|----------|
| Naming convention | PASS | All use `TestProperty_{Subject}_{Property}` |
| quick.Check usage | PASS | All tests use testing/quick |
| Invariant coverage | PASS | All domain invariants tested |
```

---

## Anti-Rationalization Table (Property Testing)

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Unit tests cover the logic" | Unit tests verify specific cases. Properties verify invariants across ALL inputs. | **Add property tests** |
| "Too abstract to test" | If there's no invariant, the code has no contract. Define the property. | **Define and test properties** |
| "Fuzz tests are enough" | Fuzz tests find crashes. Property tests verify correctness. | **Add both** |
| "Takes too long to write" | 10 lines of property test catch bugs that 100 unit tests miss. | **Write property tests** |
| "Our domain is simple" | Simple domains have simple properties. Still need tests. | **Test simple properties** |
| "Only math needs properties" | Validation, serialization, normalization ALL have properties. | **Identify and test properties** |

---
