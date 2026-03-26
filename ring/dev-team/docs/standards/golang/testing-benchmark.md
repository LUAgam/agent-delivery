# Go Standards - Benchmark Testing

> **Module:** testing-benchmark.md | **Sections:** 4 | **Parent:** [index.md](index.md)

This module covers benchmark testing patterns. Benchmark tests measure performance to identify regressions and optimization opportunities.

> **Gate Reference:** This module is loaded on-demand for performance-critical code. Not part of mandatory gates.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [What Is Benchmark Testing](#what-is-benchmark-testing) | Purpose and when to use |
| 2 | [Benchmark Function Pattern](#benchmark-function-pattern-mandatory) | b.Loop() pattern (Go 1.24+) |
| 3 | [Common Patterns](#common-patterns) | Sub-benchmarks, memory, setup |
| 4 | [Running Benchmarks](#running-benchmarks) | Commands and comparison |

**Meta-sections:** [Anti-Rationalization Table](#anti-rationalization-table-benchmark-testing)

---

## What Is Benchmark Testing

Benchmark tests measure **execution time and memory allocation** to track performance.

### Key Characteristics

| Aspect | Unit Test | Benchmark Test |
|--------|-----------|----------------|
| **Purpose** | Verify correctness | Measure performance |
| **Output** | Pass/Fail | ns/op, B/op, allocs/op |
| **When to run** | Every CI | On-demand |
| **Mandatory?** | Yes | No (optional) |

### When to Use Benchmarks

| Use Benchmarks For | Don't Use Benchmarks For |
|-------------------|-------------------------|
| Hot code paths | All code |
| Algorithm optimization | Correctness verification |
| Before/after comparison | CI gating |
| Memory profiling | One-time measurements |

---

## Benchmark Function Pattern (MANDATORY for Go 1.24+)

**HARD GATE:** All benchmark tests MUST use `b.Loop()` instead of manual `for i := 0; i < b.N; i++` loops.

### Why b.Loop Is MANDATORY

| Benefit | Explanation |
|---------|-------------|
| **Cleaner syntax** | `for b.Loop()` vs `for i := 0; i < b.N; i++` |
| **Compiler optimization** | Better optimizations with `b.Loop()` |
| **Official pattern** | Go 1.24+ standard |
| **Prevents errors** | No off-by-one errors with b.N |

### Correct Pattern (REQUIRED - Go 1.24+)

```go
// ✅ CORRECT: Use b.Loop() (Go 1.24+)
func BenchmarkCreateUser(b *testing.B) {
    svc := setupService()

    for b.Loop() {
        _, err := svc.CreateUser(context.Background(), validInput)
        if err != nil {
            b.Fatal(err)
        }
    }
}
```

### FORBIDDEN Pattern (Deprecated)

```go
// ❌ FORBIDDEN: Manual for loop (deprecated in Go 1.24+)
func BenchmarkOldPattern(b *testing.B) {
    for i := 0; i < b.N; i++ {  // WRONG: use b.Loop() instead
        DoSomething()
    }
}

// ❌ FORBIDDEN: Using loop variable unnecessarily
func BenchmarkOldPattern(b *testing.B) {
    for n := 0; n < b.N; n++ {  // WRONG: n is unused
        DoSomething()
    }
}
```

### Function Naming Convention

| Pattern | Example |
|---------|---------|
| `Benchmark{Subject}` | `BenchmarkCreateUser` |
| `Benchmark{Subject}_{Variant}` | `BenchmarkCreateUser_WithValidation` |

### File Naming

```text
*_benchmark_test.go  (preferred)
*_test.go           (acceptable)
```

---

## Common Patterns

### 1. With Setup/Teardown

```go
func BenchmarkProcessOrder(b *testing.B) {
    // Setup (runs once, not measured)
    order := createTestOrder()
    svc := setupService()

    b.ResetTimer() // Start measuring from here

    for b.Loop() {
        result := svc.ProcessOrder(order)
        _ = result // Prevent compiler optimization
    }
}
```

### 2. Sub-Benchmarks

```go
func BenchmarkEncryption(b *testing.B) {
    data := []byte("test data to encrypt")

    b.Run("AES256", func(b *testing.B) {
        key := generateAESKey()
        for b.Loop() {
            Encrypt(data, key)
        }
    })

    b.Run("RSA2048", func(b *testing.B) {
        key := generateRSAKey()
        for b.Loop() {
            EncryptRSA(data, key)
        }
    })

    b.Run("ChaCha20", func(b *testing.B) {
        key := generateChaChaKey()
        for b.Loop() {
            EncryptChaCha(data, key)
        }
    })
}
```

### 3. Memory Allocation Reporting

```go
func BenchmarkAllocations(b *testing.B) {
    b.ReportAllocs() // Enable memory reporting

    for b.Loop() {
        result := CreateLargeObject()
        _ = result
    }
}
```

### 4. Parallel Benchmarks

```go
func BenchmarkParallel(b *testing.B) {
    svc := setupService()

    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            svc.DoSomething()
        }
    })
}
```

### 5. Size Variants

```go
func BenchmarkSort(b *testing.B) {
    sizes := []int{100, 1000, 10000, 100000}

    for _, size := range sizes {
        b.Run(fmt.Sprintf("size=%d", size), func(b *testing.B) {
            data := generateData(size)
            b.ResetTimer()

            for b.Loop() {
                Sort(data)
            }
        })
    }
}
```

---

## Running Benchmarks

### Basic Commands

```bash
# Run all benchmarks
go test -bench=. ./...

# Run specific benchmark
go test -bench=BenchmarkCreateUser ./internal/service

# Run with memory allocation stats
go test -bench=. -benchmem ./...

# Run for specific duration
go test -bench=. -benchtime=5s ./...

# Run with count (for statistical significance)
go test -bench=. -count=10 ./...
```

### Comparing Results

```bash
# Install benchstat
go install golang.org/x/perf/cmd/benchstat@latest

# Run baseline
go test -bench=. -count=10 ./... > baseline.txt

# Make changes, then run again
go test -bench=. -count=10 ./... > improved.txt

# Compare
benchstat baseline.txt improved.txt
```

### Example Output

```text
BenchmarkCreateUser-8         1000000    1150 ns/op    256 B/op    4 allocs/op
BenchmarkProcessOrder-8        500000    2340 ns/op    512 B/op    8 allocs/op
BenchmarkEncryption/AES256-8  2000000     750 ns/op     64 B/op    1 allocs/op
BenchmarkEncryption/RSA2048-8    5000  250000 ns/op   2048 B/op   10 allocs/op
```

### Understanding Results

| Column | Meaning |
|--------|---------|
| `-8` | GOMAXPROCS (number of CPUs) |
| `1000000` | Number of iterations |
| `1150 ns/op` | Nanoseconds per operation |
| `256 B/op` | Bytes allocated per operation |
| `4 allocs/op` | Allocations per operation |

### Detection Commands

```bash
# Find old-style benchmarks (should return 0 matches)
grep -rn "for.*<.*b\.N" --include="*_test.go" ./internal ./pkg

# Find existing benchmarks
grep -rn "func Benchmark" --include="*_test.go" ./

# Run benchmarks only
go test -bench=. -run=^$ ./...  # -run=^$ skips unit tests
```

### Migration Example

```go
// Before (Go < 1.24)
func BenchmarkOld(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Calculate()
    }
}

// After (Go 1.24+)
func BenchmarkNew(b *testing.B) {
    for b.Loop() {
        Calculate()
    }
}
```

---

## Anti-Rationalization Table (Benchmark Testing)

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "The old pattern still works" | Deprecated. Use modern Go patterns. | **Use b.Loop()** |
| "I'm used to the for loop" | Familiarity ≠ best practice. Adapt. | **Use b.Loop()** |
| "It's just benchmarks" | Standards apply to all test code. | **Use b.Loop()** |
| "We're on Go 1.23" | Upgrade to Go 1.24+ (minimum version requirement). | **Upgrade + use b.Loop()** |
| "Benchmarks aren't important" | Performance matters. Measure it. | **Add benchmarks for hot paths** |
| "We'll optimize later" | Can't optimize what you don't measure. | **Benchmark first** |

---
