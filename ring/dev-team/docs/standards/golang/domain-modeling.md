# Go Standards - Domain Modeling

> **Module:** domain-modeling.md | **Sections:** §1-4 | **Parent:** [index.md](index.md)

This module covers Always-Valid Domain Model patterns.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Always-Valid Domain Model](#always-valid-domain-model-mandatory) | Domain entities with invariant protection |
| 2 | [Constructor Validation Patterns](#constructor-validation-patterns-mandatory) | NewEntity/NewEntityFromDTO/ReconstructEntity conventions |
| 3 | [ToEntity/FromEntity Integration](#toentityfromentity-integration-mandatory) | Layer separation patterns |
| 4 | [Integration with HTTP Layer](#integration-with-http-layer) | DTO to domain entity conversion |

---

## Always-Valid Domain Model (MANDATORY)

**HARD GATE:** All domain entities MUST use the Always-Valid Domain Model pattern. Anemic models (structs without validation) are FORBIDDEN.

### Why This Pattern Is Mandatory

| Problem with Anemic Models | Impact |
|---------------------------|--------|
| Objects can exist in invalid state | Bugs propagate through system |
| Validation scattered across codebase | Duplication, inconsistency |
| Business rules not enforced at creation | Invalid data reaches database |
| No single source of truth for validity | Every consumer must re-validate |

### The Pattern

**Core Principle:** An entity can NEVER exist in an invalid state. Validation happens in the constructor, not later.

```go
// ✅ CORRECT: Always-Valid Domain Model
type Rule struct {
    id         uuid.UUID
    name       string
    expression string
    createdAt  time.Time
}

// Constructor MUST validate and return error if invalid
func NewRule(name, expression string) (*Rule, error) {
    // Validation at construction time
    if strings.TrimSpace(name) == "" {
        return nil, fmt.Errorf("%w: name is required", ErrInvalidInput)
    }
    if len(name) > 255 {
        return nil, fmt.Errorf("%w: name exceeds 255 characters", ErrInvalidInput)
    }
    if !isValidExpression(expression) {
        return nil, fmt.Errorf("%w: invalid expression syntax", ErrInvalidInput)
    }

    return &Rule{
        id:         uuid.New(),
        name:       strings.TrimSpace(name),
        expression: expression,
        createdAt:  time.Now(),
    }, nil
}

// Getters expose immutable data
func (r *Rule) ID() uuid.UUID   { return r.id }
func (r *Rule) Name() string    { return r.name }
func (r *Rule) Expression() string { return r.expression }
```

```go
// ❌ FORBIDDEN: Anemic Model (validation elsewhere)
type Rule struct {
    ID         uuid.UUID
    Name       string    // Can be empty - invalid!
    Expression string    // Can be invalid - no validation!
}

// ❌ FORBIDDEN: Constructor without validation
func NewRule(name, expression string) *Rule {
    return &Rule{
        ID:         uuid.New(),
        Name:       name,       // No validation!
        Expression: expression, // No validation!
    }
}
```

### Requirements

| Requirement | Description |
|-------------|-------------|
| **Constructor returns error** | `NewEntity(...) (*Entity, error)` - MUST return error if invalid |
| **Private fields** | Use lowercase field names to prevent direct assignment |
| **Getters for access** | Provide getter methods for field access |
| **No Setters** | Mutation through domain methods that validate |
| **Invariants enforced** | Business rules validated at construction |

### Mutation Pattern

When entities need to change state, use domain methods that validate:

```go
// ✅ CORRECT: Mutation with validation
func (r *Rule) UpdateExpression(newExpression string) error {
    if !isValidExpression(newExpression) {
        return fmt.Errorf("%w: invalid expression syntax", ErrInvalidInput)
    }
    r.expression = newExpression
    return nil
}

// ❌ FORBIDDEN: Direct field assignment
rule.Expression = "invalid!!!"  // Compilation error (private field)
```

### Reconstruction from Database

When loading from database, use a separate reconstruction function:

```go
// For repository use ONLY - reconstructs from trusted storage
func ReconstructRule(id uuid.UUID, name, expression string, createdAt time.Time) *Rule {
    return &Rule{
        id:         id,
        name:       name,
        expression: expression,
        createdAt:  createdAt,
    }
}
```

**Note:** `Reconstruct*` functions skip validation because data is from trusted storage (already validated at creation).

### Constructor Validation Patterns (MANDATORY)

**⛔ HARD GATE:** All domain entities MUST have validated constructors. Public struct initialization is FORBIDDEN.

#### Constructor Naming Convention

| Type | Constructor Name | Returns |
|------|------------------|---------|
| New entity | `NewEntity(...)` | `(*Entity, error)` |
| From DTO | `NewEntityFromDTO(dto)` | `(*Entity, error)` |
| Reconstruction | `ReconstructEntity(...)` | `*Entity` (no error) |

#### Detection Commands (MANDATORY)

```bash
# MANDATORY: Run before every PR that modifies domain models
# Find structs in domain packages without New* constructor
# Explicitly check that find returns files before running the loop
COUNT=$(find internal/domain pkg/mmodel -name "*.go" 2>/dev/null | wc -l)
if [ "$COUNT" -eq 0 ]; then
  echo "ERROR: No .go files found in internal/domain or pkg/mmodel. Cannot run missing-constructor check." >&2
  exit 1
fi
while IFS= read -r -d '' f; do
  structs=$(grep -E "^type [A-Z][a-zA-Z]+ struct" "$f" | awk '{print $2}')
  for s in $structs; do
    if ! grep -q "func New${s}" "$f" 2>/dev/null; then
      echo "MISSING CONSTRUCTOR: $f - $s"
    fi
  done
done < <(find internal/domain pkg/mmodel -name "*.go" -print0 2>/dev/null)

# Expected: All domain structs have New* constructor
# If missing: BLOCKER - Add constructor before proceeding
```

#### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: Direct struct initialization in service layer
func (s *Service) CreateUser(name, email string) (*domain.User, error) {
    return &domain.User{  // WRONG: Bypasses constructor validation
        ID:    uuid.New(),
        Name:  name,
        Email: email,
    }, nil
}

// ❌ FORBIDDEN: Constructor without validation
func NewUser(name, email string) *User {
    return &User{  // WRONG: No validation, no error return
        ID:    uuid.New(),
        Name:  name,
        Email: email,
    }
}

// ❌ FORBIDDEN: Public fields allowing direct assignment
type User struct {
    ID    uuid.UUID  // WRONG: Public field
    Name  string     // WRONG: Can be assigned directly
    Email string     // WRONG: No validation enforced
}
```

### ToEntity/FromEntity Integration (MANDATORY)

Domain entities MUST integrate with ToEntity/FromEntity patterns for layer separation.

```go
// internal/adapters/postgres/user_mapper.go

// FromEntity - Domain entity → Database model
func (m *UserMapper) FromEntity(entity *domain.User) *UserModel {
    return &UserModel{
        ID:        entity.ID().String(),
        Name:      entity.Name(),
        Email:     entity.Email(),
        CreatedAt: entity.CreatedAt(),
    }
}

// ToEntity - Database model → Domain entity (uses Reconstruct, not New)
// MUST validate ID before reconstruction - return error for corrupted data
func (m *UserMapper) ToEntity(model *UserModel) (*domain.User, error) {
    id, err := uuid.Parse(model.ID)
    if err != nil {
        // Database contains corrupted ID - return wrapped error
        return nil, fmt.Errorf("corrupted user id %q: %w", model.ID, err)
    }
    return domain.ReconstructUser(
        id,
        model.Name,
        model.Email,
        model.CreatedAt,
    ), nil
}
```

**See [domain.md - ToEntity/FromEntity](domain.md#data-transformation-toentityfromentity-mandatory)** for complete patterns.

---

### Integration with HTTP Layer

HTTP handlers still use DTOs with validation tags, but MUST create domain entities via constructors:

```go
// HTTP DTO - validation at boundary
type CreateRuleRequest struct {
    Name       string `json:"name" validate:"required,min=1,max=255"`
    Expression string `json:"expression" validate:"required"`
}

// Handler creates domain entity
func (h *Handler) CreateRule(c *fiber.Ctx) error {
    var req CreateRuleRequest
    if err := c.BodyParser(&req); err != nil {
        return libHTTP.WithError(c, err)
    }
    if err := h.validator.Struct(&req); err != nil {
        return libHTTP.WithError(c, err)
    }

    // Domain entity creation - additional business validation
    rule, err := domain.NewRule(req.Name, req.Expression)
    if err != nil {
        return libHTTP.WithError(c, err)
    }

    // ...
}
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Validation at boundary is enough" | Boundary validation is for input format. Domain validation is for business rules. | **Use both: DTO validation + constructor validation** |
| "Adds boilerplate" | Invalid objects cause more work debugging than constructors. | **Write the constructor. It's an investment.** |
| "We trust our code" | Every consumer must remember to validate. Humans forget. | **Enforce at construction. Forget-proof.** |
| "Performance overhead" | Validation once at creation vs checking everywhere. | **Single validation is MORE efficient** |
| "Existing code doesn't do this" | Technical debt. Refactor when touching the code. | **New code MUST follow. Refactor gradually.** |
| "Simple struct is fine for DTOs" | DTOs are fine as anemic. Domain entities are NOT. | **Distinguish DTO from Domain Entity** |

### Checklist

- [ ] All domain entities in `/internal/domain` or `/pkg/mmodel` use `NewXxx` constructors
- [ ] Constructors return `(*Entity, error)` - never bare pointer
- [ ] Fields are private (lowercase)
- [ ] Getters provided for field access
- [ ] Mutation through validated methods only
- [ ] Reconstruct functions for database loading
- [ ] No direct struct initialization outside constructors

---

