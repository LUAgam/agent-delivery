# Go Standards - Fuzz Testing

> **Module:** testing-fuzz.md | **Sections:** 5 | **Parent:** [index.md](index.md)

This module covers native Go fuzz testing patterns. Fuzz tests automatically generate random inputs to find bugs that manual testing misses.

> **Gate Reference:** This module is loaded by `ring:qa-analyst` at Gate 4 (Fuzz Testing).

---

## Table of Contents

| # | [Section Name](#anchor-link) | Description |
|---|------------------------------|-------------|
| 1 | [What Is Fuzz Testing](#what-is-fuzz-testing) | Purpose and when to use |
| 2 | [Fuzz Function Pattern](#fuzz-function-pattern-mandatory) | Go 1.18+ native fuzz syntax |
| 3 | [Seed Corpus](#seed-corpus-mandatory) | Initial test cases for fuzzer |
| 4 | [Input Types](#input-types) | Supported fuzz input types |
| 5 | [Fuzz Test Quality Gate](#fuzz-test-quality-gate-mandatory) | Checklist before completion |

**Meta-sections:** [Output Format (Gate 4 - Fuzz Testing)](#output-format-gate-4---fuzz-testing), [Anti-Rationalization Table](#anti-rationalization-table-fuzz-testing)

---

## What Is Fuzz Testing

Fuzz testing automatically generates **millions of random inputs** to find bugs that manual testing misses.

### Key Differences from Unit Tests

| Aspect | Unit Test | Fuzz Test |
|--------|-----------|-----------|
| **Who defines inputs?** | You (manual) | Fuzzer (automatic) |
| **Number of cases** | 5-20 cases | Millions |
| **What it finds** | Known bugs | Unknown bugs |
| **Speed** | Fast | Varies (can run for hours) |
| **Where to use** | All code | Input validation, parsing |

### When to Use Fuzz Testing

| Use Fuzz For | Don't Use Fuzz For |
|--------------|-------------------|
| Input validation functions | Business logic with mocks |
| Parsers (JSON, XML, custom) | Database operations |
| Serialization/deserialization | External API calls |
| String manipulation | Slow operations |
| Security-sensitive code | UI components |

### What Fuzz Tests Verify

```go
// PROPERTY: No panic, no 5xx errors
// The fuzzer tries to crash your code with random inputs
result, err := ValidateInput(randomInput)
// If no panic occurs, the test passes
```

---

## Fuzz Function Pattern (MANDATORY)

**HARD GATE:** All fuzz tests MUST use Go 1.18+ native fuzz syntax (`*testing.F`).

### Required Pattern

```go
func FuzzCreateOrganization_LegalName(f *testing.F) {
    // Step 1: Seed corpus with edge cases
    f.Add("Acme, Inc.")                // valid
    f.Add("")                          // empty
    f.Add("日本語")                     // unicode
    f.Add("<script>alert(1)</script>") // XSS attempt
    f.Add(strings.Repeat("x", 1000))   // long string

    // Step 2: Define fuzz function
    f.Fuzz(func(t *testing.T, name string) {
        // Step 3: Bound input to prevent resource exhaustion
        if len(name) > 512 {
            name = name[:512]
        }

        // Step 4: Call function under test
        // PROPERTY: No panic, returns error gracefully
        result, err := ValidateOrganizationName(name)

        // Step 5: Verify properties (not specific values)
        if err == nil {
            assert.NotEmpty(t, result)
        }
        // No panic = test passes
    })
}
```

### Function Naming Convention

| Pattern | Example |
|---------|---------|
| `Fuzz{Subject}_{Field}` | `FuzzCreateOrganization_LegalName` |
| `Fuzz{Function}_{Input}` | `FuzzParseJSON_Payload` |
| `Fuzz{Validator}_{Field}` | `FuzzValidateEmail_Address` |

### File Naming

```text
*_test.go (unit test file, not integration)

Examples:
- validator_test.go
- parser_test.go
- serializer_test.go
```

**Note:** Fuzz tests are unit-level tests. They run without containers and must be fast.

---

## Seed Corpus (MANDATORY)

**HARD GATE:** All fuzz tests MUST include seed corpus with edge cases. Empty seed corpus is FORBIDDEN.

### Seed Corpus Categories

| Category | Examples | Purpose |
|----------|----------|---------|
| Valid inputs | `"Acme, Inc."`, `"user@example.com"` | Ensure valid inputs work |
| Empty/nil | `""`, `nil` | Edge case handling |
| Boundary | `strings.Repeat("x", MaxLength)` | Length limits |
| Unicode | `"日本語"`, `"🎉"`, `"α β γ"` | Encoding handling |
| Invalid formats | `"{ invalid json }"` | Error handling |
| Security payloads | `"<script>"`, `"' OR 1=1"` | Security testing |
| Boundary numbers | `"9223372036854775807"` (max int64) | Overflow testing |

### Correct Pattern

```go
func FuzzValidateEmail(f *testing.F) {
    // ✅ CORRECT: Comprehensive seed corpus
    f.Add("user@example.com")           // valid
    f.Add("test.user+tag@domain.org")   // valid with special chars
    f.Add("")                           // empty
    f.Add("invalid")                    // no @
    f.Add("@domain.com")                // no local part
    f.Add("user@")                      // no domain
    f.Add("user@.com")                  // invalid domain
    f.Add("user@domain..com")           // double dot
    f.Add(strings.Repeat("a", 255) + "@test.com") // max length
    f.Add("user@日本語.com")             // unicode domain
    f.Add("' OR 1=1 --@evil.com")       // SQL injection attempt

    f.Fuzz(func(t *testing.T, email string) {
        // ...
    })
}
```

### FORBIDDEN Pattern

```go
// ❌ FORBIDDEN: Empty seed corpus
func FuzzValidateEmail(f *testing.F) {
    f.Fuzz(func(t *testing.T, email string) {
        ValidateEmail(email)  // WRONG: No seeds
    })
}

// ❌ FORBIDDEN: Only valid inputs
func FuzzValidateEmail(f *testing.F) {
    f.Add("user@example.com")  // WRONG: Only one seed
    f.Fuzz(func(t *testing.T, email string) {
        ValidateEmail(email)
    })
}
```

---

## Input Types

### Supported Primitive Types

| Type | Use For |
|------|---------|
| `string` | Text input, names, emails |
| `[]byte` | Binary data, files, JSON |
| `bool` | Flags, toggles |

### Supported Numeric Types

| Type | Use For |
|------|---------|
| `int`, `int8`, `int16`, `int32`, `int64` | Integers |
| `uint`, `uint8`, `uint16`, `uint32`, `uint64` | Unsigned integers |
| `float32`, `float64` | Floating-point numbers |

### Complex Types via JSON

For complex types, use `[]byte` and JSON unmarshaling:

```go
func FuzzCreateUser(f *testing.F) {
    // Seed with valid JSON
    f.Add([]byte(`{"name":"John","age":30}`))
    f.Add([]byte(`{}`))                    // empty object
    f.Add([]byte(`{"name":""}`))           // empty name
    f.Add([]byte(`{"age":-1}`))            // negative age
    f.Add([]byte(`not json`))              // invalid JSON

    f.Fuzz(func(t *testing.T, data []byte) {
        var input CreateUserInput
        if json.Unmarshal(data, &input) != nil {
            return // Skip invalid JSON - not a bug in our code
        }

        // Test with valid struct
        result, err := CreateUser(input)
        if err == nil {
            assert.NotEmpty(t, result.ID)
        }
        // No panic = pass
    })
}
```

### Multiple Input Parameters

```go
func FuzzTransferMoney(f *testing.F) {
    f.Add("USD", int64(100))
    f.Add("EUR", int64(0))
    f.Add("BRL", int64(-1))
    f.Add("", int64(1000000))

    f.Fuzz(func(t *testing.T, currency string, amount int64) {
        // Test with multiple random inputs
        result, err := Transfer(currency, amount)
        if err == nil {
            assert.True(t, result.Amount >= 0)
        }
    })
}
```

---

## Fuzz Test Quality Gate (MANDATORY)

**Before marking fuzz tests complete:**

- [ ] All input validation functions have fuzz tests
- [ ] All parsers have fuzz tests
- [ ] All fuzz functions follow naming convention `Fuzz{Subject}_{Field}`
- [ ] All fuzz tests have seed corpus with 5+ seeds
- [ ] Seed corpus includes: valid, empty, boundary, unicode, security payloads
- [ ] Input length bounded to prevent resource exhaustion
- [ ] Fuzz tests run without panic: `go test -fuzz=. -fuzztime=30s`
- [ ] No flaky failures

### Running Fuzz Tests

```bash
# Run all fuzz tests for 30 seconds each
go test -fuzz=. -fuzztime=30s ./...

# Run specific fuzz test
go test -fuzz=FuzzValidateEmail -fuzztime=1m ./internal/validator

# Run fuzz tests until failure
go test -fuzz=. ./internal/validator

# Check for crashes in testdata/fuzz/
ls -la testdata/fuzz/
```

### Detection Command

```bash
# Find functions that should have fuzz tests
grep -rn "func Validate\|func Parse\|func Unmarshal" --include="*.go" ./internal | grep -v "_test.go"

# Find existing fuzz tests
grep -rn "func Fuzz" --include="*_test.go" ./internal
```

---

## Output Format (Gate 4 - Fuzz Testing)

```markdown
## Fuzz Testing Summary

| Metric | Value |
|--------|-------|
| Validation functions | X |
| Fuzz tests written | Y |
| Seed corpus per test | 5+ |
| Fuzz duration | 30s per test |
| Crashes found | 0 |

### Fuzz Tests by Function

| Function | Fuzz Test | Seeds | Duration | Status |
|----------|-----------|-------|----------|--------|
| ValidateEmail | FuzzValidateEmail | 10 | 30s | PASS |
| ParseJSON | FuzzParseJSON_Payload | 8 | 30s | PASS |
| ValidateCPF | FuzzValidateCPF | 12 | 30s | PASS |

### Standards Compliance

| Standard | Status | Evidence |
|----------|--------|----------|
| Naming convention | PASS | All use `Fuzz{Subject}_{Field}` |
| Seed corpus | PASS | Minimum 5 seeds per test |
| Input bounding | PASS | Length limits in all tests |
```

---

## Anti-Rationalization Table (Fuzz Testing)

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Unit tests cover validation" | Unit tests use YOUR inputs. Fuzz finds what you didn't think of. | **Add fuzz tests** |
| "Fuzz testing is slow" | 30 seconds finds bugs that save hours of debugging. | **Run fuzz tests** |
| "Our input is controlled" | Attackers don't respect your assumptions. | **Fuzz all user input** |
| "We validate at API layer" | Defense in depth. Fuzz internal validators too. | **Fuzz all validators** |
| "One seed is enough" | One seed = limited coverage. More seeds = more bugs found. | **Add 5+ seeds** |
| "No time for fuzz tests" | Fuzz tests catch security issues that cost 100x more to fix later. | **Write fuzz tests** |

---
