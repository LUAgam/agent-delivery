# Go Standards

> **DEPRECATED - Moved to golang/**
>
> This file has been split into modular files for better performance and selective loading.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [New Location](#new-location) | Redirect to golang/ directory |
| 2 | [Module Structure](#module-structure) | 13 modular files with 45 sections |
| 3 | [Migration Guide](#migration-guide) | WebFetch URLs and selective loading |
| 4 | [Deprecation Timeline](#deprecation-timeline) | Removal schedule |

---

## New Location

**Directory:** `dev-team/docs/standards/golang/`

**Index:** [golang/index.md](golang/index.md)

---

## Module Structure

| Module | Sections | Description |
|--------|----------|-------------|
| [index.md](golang/index.md) | - | Master TOC and routing guide |
| [core.md](golang/core.md) | 9 | Version, lib-commons, Frameworks, Configuration, DB Naming, Migrations, License Headers, MongoDB, Dependency Management |
| [bootstrap.md](golang/bootstrap.md) | 5 | Observability, Bootstrap, Graceful Shutdown, Health Checks, Connection Management |
| [security.md](golang/security.md) | 4 | Access Manager, License Manager, Secret Redaction, SQL Safety |
| [domain.md](golang/domain.md) | 5 | ToEntity/FromEntity, Error Codes, Error Handling, Exit/Fatal Rules, Function Design |
| [api-patterns.md](golang/api-patterns.md) | 6 | JSON Naming, Pagination, HTTP Status, OpenAPI/Swaggo, Handler Constructor, Input Validation |
| [quality.md](golang/quality.md) | 5 | Testing, Logging, Linting, Production Config Validation, Container Security |
| [architecture.md](golang/architecture.md) | 6 | Architecture Patterns, Directory Structure, Concurrency, Goroutine Recovery, N+1 Detection, Performance |
| [messaging.md](golang/messaging.md) | 1 | RabbitMQ Worker Pattern |
| [domain-modeling.md](golang/domain-modeling.md) | 1 | Always-Valid Domain Model (Constructor Validation Patterns) |
| [idempotency.md](golang/idempotency.md) | 1 | Idempotency Patterns |
| [multi-tenant.md](golang/multi-tenant.md) | 1 | Multi-Tenant Patterns |
| [compliance.md](golang/compliance.md) | Meta | Standards Compliance Output Format, Checklist |

**Total:** 45 sections indexed in [standards-coverage-table.md](../skills/shared-patterns/standards-coverage-table.md)

---

## Migration Guide

**For WebFetch:**
```
# Old (deprecated)
https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang.md

# New (use this)
https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/index.md
```

**For selective loading:**
1. Fetch `golang/index.md` first
2. Use the "Which File for What" table to identify required modules
3. Fetch only the modules you need

---

## Deprecation Timeline

- **Current:** Redirect notice (this file)
- **Next release:** File will be removed

**Update your references to use `golang/index.md` and specific modules.**
