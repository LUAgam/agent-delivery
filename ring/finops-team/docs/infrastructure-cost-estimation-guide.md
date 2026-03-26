# Infrastructure Cost Estimation: Complete Guide

This document is the **single source of truth** for infrastructure cost estimation. The skill and agent reference this guide for pricing tables, sizing rules, and calculation formulas.

**Version:** 7.0.0 - Consolidated as single source of truth (skill and agent reference this guide)

> **Referenced by:**
> - `finops-team/skills/infrastructure-cost-estimation/SKILL.md` (orchestrator)
> - `finops-team/agents/infrastructure-cost-estimator.md` (calculator)

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Inputs](#inputs)
   - [Environment Selection](#environment-selection)
   - [Component Sharing Model](#component-sharing-model-critical-input)
   - [Dynamic Helm Chart Data](#dynamic-helm-chart-data-from-lerianhelmstudio)
   - [Networking Architecture](#networking-architecture)
3. [Outputs](#outputs)
4. [Calculation Rationale](#calculation-rationale)
5. [Pricing Reference](#pricing-reference)
6. [Workflow Summary](#workflow-summary)
7. [Key Design Decisions](#key-design-decisions)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      SKILL (Orchestrator)                        │
│                ring:infrastructure-cost-estimation               │
│                                                                  │
│  Role: Collect ALL data before dispatching agent                 │
│  Principle: "Skill asks, Agent calculates"                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Passes complete data
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT (Calculator)                          │
│                ring:infrastructure-cost-estimator                │
│                                                                  │
│  Role: Calculate costs, never ask questions                      │
│  Principle: "Pure calculation, no interaction"                   │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Component | Responsibility | Benefit |
|-----------|---------------|---------|
| **Skill** | Collects data, interacts with user | Consistent data gathering |
| **Agent** | Pure calculation | Deterministic, testable |

The separation ensures:
- All data is collected BEFORE calculation begins
- Agent never blocks waiting for user input
- Calculations are reproducible with same inputs

---

## Inputs

### Required Inputs (Skill Collects)

| Input | Type | Description | Example |
|-------|------|-------------|---------|
| **Repo Path** | string | Application repository with docker-compose.yml | `/workspace/midaz` |
| **TPS** | number | Expected transactions per second | `100` |
| **Total Customers** | number | Customers sharing the platform | `5` |
| **Component Sharing Model** | object | Per-component SHARED vs DEDICATED | See below |
| **Billing Unit** | string | What unit to charge customers | `transaction` |
| **Price per Unit** | number | Customer-facing price | `R$ 0.10` |
| **Expected Volume** | number | Monthly volume of billing units | `1,000,000` |

### Optional Inputs

| Input | Type | Description | Default |
|-------|------|-------------|---------|
| **Helm Charts Path** | string | Local path to LerianStudio/helm repo | Fetches via WebFetch |
| **Database Config** | object | Multi-AZ, read replicas | Auto-calculated from TPS |
| **Estimated Storage** | number | Storage in GB | Calculated from TPS |

### Environment Selection

**Ask which environments need cost estimation:**

| Environment | Region | Configuration | Use Case |
|-------------|--------|---------------|----------|
| **Homolog** | us-east-2 (Ohio) | Single-AZ, 1 replica, ~35% cheaper | Testing, staging |
| **Production** | sa-east-1 (São Paulo) | Multi-AZ, 3 replicas, full HA | Live traffic |

**Key Differences:**

| Aspect | Homolog | Production |
|--------|---------|------------|
| **Region** | us-east-2 (Ohio) | sa-east-1 (São Paulo) |
| **Pricing** | ~35% cheaper | Full price |
| **Pod Replicas** | 1 per service (no HA) | 3 per service (HA) |
| **Database** | Single-AZ, 0 replicas | Multi-AZ + Read Replicas |
| **NAT Gateways** | 1 (single AZ) | 3 (one per AZ) |
| **Purpose** | Testing only | Live customer traffic |

**Combined Cost:** Customer typically pays for both environments (Homolog + Production).

### Component Sharing Model (Critical Input)

The sharing model determines how costs are attributed to each customer:

```
| Component      | Sharing        | Customers | Cost Attribution          |
|----------------|----------------|-----------|---------------------------|
| VPC            | SHARED/DEDICATED | 5       | Depends on isolation needs|
| EKS Cluster    | SHARED         | 5         | Total ÷ 5 = per customer  |
| EKS Nodes      | SHARED         | 5         | Total ÷ 5 = per customer  |
| PostgreSQL     | DEDICATED      | 1         | Full cost to customer     |
| Valkey         | SHARED         | 5         | Total ÷ 5 = per customer  |
| DocumentDB     | SHARED         | 5         | Total ÷ 5 = per customer  |
| RabbitMQ       | SHARED         | 5         | Total ÷ 5 = per customer  |
| ALB            | SHARED         | 5         | Total ÷ 5 = per customer  |
| NAT Gateway    | ALWAYS SHARED  | ALL       | Total ÷ ALL customers     |
```

### Sharing Model Definitions

| Model | Infrastructure | Isolation | Example |
|-------|---------------|-----------|---------|
| **SHARED** | Same instance, schema-based multi-tenancy | Logical (schemas/prefixes) | One RDS, each customer has own schema (`customer_001.*`) |
| **DEDICATED** | Fully isolated instance | Physical (no other customers) | Customer gets their own RDS instance |
| **ALWAYS SHARED** | Platform-level resource | Cannot be dedicated | NAT Gateways are shared across all customers |

### How Sharing Works in Practice

| Component | SHARED Isolation | DEDICATED Isolation |
|-----------|------------------|---------------------|
| VPC | Subnets + Security Groups per customer | Separate VPC per customer |
| PostgreSQL | Schema per customer (`cust_001.*`) | Separate RDS instance |
| DocumentDB | Database per customer | Separate cluster |
| Valkey | Key prefix per customer (`cust001:*`) | Separate ElastiCache cluster |
| RabbitMQ | VHost per customer | Separate Amazon MQ broker |
| EKS | Namespace per customer | Separate node group or cluster |

### Networking Architecture

#### NAT Gateway Rules (CRITICAL)

**NAT Gateways are ALWAYS SHARED** - they are platform-level resources that cannot be dedicated per customer.

| Environment | NAT Gateways | Configuration | Why |
|-------------|--------------|---------------|-----|
| **Homolog** | 1 | Single AZ | Testing only, no HA needed |
| **Production** | 3 | One per AZ (3 AZs) | High availability, AZ failure tolerance |

**Cost Calculation:**

```
Homolog:
  NAT Gateway cost = 1 × R$ 174 = R$ 174
  Per customer = R$ 174 ÷ total_customers

Production:
  NAT Gateway cost = 3 × R$ 205 = R$ 615
  Per customer = R$ 615 ÷ total_customers
```

**Why 3 NAT Gateways in Production?**
- Each AZ needs its own NAT Gateway for HA
- If one AZ fails, other AZs continue to function
- Avoids cross-AZ data transfer costs for outbound traffic

#### VPC Sharing Model

| Model | Description | Use Case | Cost Impact |
|-------|-------------|----------|-------------|
| **VPC SHARED** | Single VPC for all customers | Cost-effective, standard isolation | 1 VPC cost ÷ customers |
| **VPC DEDICATED** | Separate VPC per customer | Strict network isolation, compliance | Full VPC cost to customer |

**DEDICATED VPC includes:**
- Dedicated subnets (public + private per AZ)
- Dedicated route tables
- Dedicated security groups
- Dedicated VPC endpoints (if required)

#### Data Transfer Costs (TPS-Based)

Data transfer costs are calculated based on TPS:

```
Assumptions:
- Average request size: 5 KB
- Average response size: 10 KB
- Total per transaction: 15 KB

Monthly data volume:
  Data (GB) = TPS × 86,400 sec × 30 days × 15 KB ÷ 1,000,000

Example (100 TPS):
  Data = 100 × 86,400 × 30 × 15 ÷ 1,000,000 = 3,888 GB ≈ 3.9 TB
```

| Data Transfer Type | Cost | Notes |
|--------------------|------|-------|
| **NAT Gateway Processing** | R$ 0.045/GB | All outbound traffic |
| **Data Out to Internet** | R$ 0.50/GB (first 10TB) | Egress to internet |
| **Inter-AZ Transfer** | R$ 0.01/GB | Cross-AZ within VPC |
| **ALB Data Processing** | R$ 0.008/GB | Request/response processing |

**Example (100 TPS = 3,888 GB/month):**
```
NAT Processing: 3,888 × 0.045 = R$ 175
Internet Egress: 778 × 0.50 = R$ 389 (20% of traffic)
Inter-AZ: 1,166 × 0.01 = R$ 12 (30% of traffic)
ALB Processing: 3,888 × 0.008 = R$ 31
─────────────────────────────────────
Total Data Transfer: R$ 607/month
```

### Dynamic Helm Chart Data (from LerianStudio/helm)

**CRITICAL: Data is read at runtime, NOT hardcoded.**

The skill reads actual CPU/memory values from LerianStudio/helm repository at runtime, ensuring:
- Always current values (no stale data)
- Smaller prompt size
- Single source of truth

**Data Source:** `git@github.com:LerianStudio/helm.git`

**Files Read at Runtime:**

| Chart | Path | Services |
|-------|------|----------|
| **Midaz Core** | `charts/midaz/values.yaml` | onboarding, transaction, ledger, crm |
| **Reporter** | `charts/reporter/values.yaml` | manager, worker, frontend |
| **Access Manager** | `charts/plugin-access-manager/values.yaml` | identity, auth |

**How to Read:**

1. **If local clone exists:** Use `Read` tool on values.yaml files
2. **If no local clone:** Use `WebFetch` from GitHub raw URLs:
   ```
   https://raw.githubusercontent.com/LerianStudio/helm/main/charts/midaz/values.yaml
   https://raw.githubusercontent.com/LerianStudio/helm/main/charts/reporter/values.yaml
   https://raw.githubusercontent.com/LerianStudio/helm/main/charts/plugin-access-manager/values.yaml
   ```

**What to Extract per Service:**

```yaml
# For each service, extract:
resources:
  requests:
    cpu: ???m      # CPU request in millicores
    memory: ???Mi  # Memory request
autoscaling:
  minReplicas: ?   # Minimum replicas
  maxReplicas: ?   # Maximum replicas
```

**Fallback:** If specific plugin/service not found, use Midaz core setup as baseline.

---

## Outputs

The agent produces a structured markdown report with **10 required sections** (v5.0):

### 1. Discovered Services

Maps docker-compose services to AWS equivalents:

```
| Docker Service | AWS Mapping      | Category |
|----------------|------------------|----------|
| postgres       | RDS PostgreSQL   | Database |
| mongodb        | DocumentDB       | Database |
| valkey/redis   | ElastiCache      | Cache    |
| rabbitmq       | Amazon MQ        | Queue    |
| app containers | EKS Pods         | Compute  |
```

**Source:** Parsed from `docker-compose.yml` in the provided repository path.

### 2. Compute Resources (from LerianStudio/helm)

Shows actual CPU/memory per service read at runtime from LerianStudio/helm:

```
| Service     | CPU Request | Memory  | Source            | Homolog (1 rep) | Prod (3 rep) |
|-------------|-------------|---------|-------------------|-----------------|--------------|
| onboarding  | [actual]    | [actual]| midaz/values.yaml | 1 pod           | 3 pods       |
| transaction | [actual]    | [actual]| midaz/values.yaml | 1 pod           | 3 pods       |
| ledger      | [actual]    | [actual]| midaz/values.yaml | 1 pod           | 3 pods       |
| identity    | [actual]    | [actual]| access-manager    | 1 pod           | 3 pods       |
| auth        | [actual]    | [actual]| access-manager    | 1 pod           | 3 pods       |
| manager     | [actual]    | [actual]| reporter          | 1 pod           | 3 pods       |
| worker      | [actual]    | [actual]| reporter          | 1 pod           | 3 pods       |
| frontend    | [actual]    | [actual]| reporter          | 1 pod           | 3 pods       |
```

**Infrastructure Components (from LerianStudio/helm values.yaml):**

```
| Component  | Source            | CPU Request | Memory Request |
|------------|-------------------|-------------|----------------|
| PostgreSQL | midaz/values.yaml | [actual]    | [actual]       |
| MongoDB    | midaz/values.yaml | [actual]    | [actual]       |
| RabbitMQ   | midaz/values.yaml | [actual]    | [actual]       |
| Valkey     | midaz/values.yaml | [actual]    | [actual]       |
```

**Note:** Values shown as `[actual]` are read at runtime from LerianStudio/helm.

**EKS Node Sizing (calculated from actual values):**

```
| Environment | Services  | Infra     | Total     | +20% Headroom | Nodes Required    |
|-------------|-----------|-----------|-----------|---------------|-------------------|
| Homolog     | 4.5 vCPU  | 2.5 vCPU  | 7.0 vCPU  | 8.4 vCPU      | 3x c6i.xlarge     |
| Production  | 13.5 vCPU | 2.5 vCPU  | 16.0 vCPU | 19.2 vCPU     | 6x c6i.xlarge     |
```

### 3. Homolog Environment Costs (New in v5.0)

Dedicated section for homolog/staging environment (us-east-2 Ohio):

```
Configuration: Single-AZ, 1 replica per service, no HA

| Component        | Instance       | Sharing   | Total Cost | Cost/Customer |
|------------------|----------------|-----------|------------|---------------|
| EKS Control Plane| -              | SHARED    | R$ 265     | R$ [÷cust]    |
| EKS Nodes        | Nx c6i.xlarge  | SHARED    | R$ [calc]  | R$ [÷cust]    |
| PostgreSQL       | db.m7g.large   | DEDICATED | R$ 632     | R$ 632        |
| NAT Gateway      | 1 (single AZ)  | ALWAYS    | R$ 174     | R$ [÷total]   |
| **HOMOLOG TOTAL**| -              | -         | **R$ X,XXX** | **R$ X,XXX** |
```

### 4. Production Environment Costs (New in v5.0)

Dedicated section for production environment (sa-east-1 São Paulo):

```
Configuration: Multi-AZ, 3 replicas per service, full HA

| Component        | Instance       | Sharing   | Total Cost | Cost/Customer |
|------------------|----------------|-----------|------------|---------------|
| EKS Control Plane| -              | SHARED    | R$ 365     | R$ [÷cust]    |
| EKS Nodes        | Nx c6i.xlarge  | SHARED    | R$ [calc]  | R$ [÷cust]    |
| PostgreSQL       | db.m7g.large   | DEDICATED | R$ 1,490   | R$ 1,490      |
| NAT Gateway      | 3 (one per AZ) | ALWAYS    | R$ 615     | R$ [÷total]   |
| **PROD TOTAL**   | -              | -         | **R$ X,XXX** | **R$ X,XXX** |
```

### 5. Environment Comparison (New in v5.0)

Side-by-side comparison of environments:

```
| Metric            | Homolog    | Production | Difference |
|-------------------|------------|------------|------------|
| Region            | us-east-2  | sa-east-1  | -          |
| HA Config         | Single-AZ  | Multi-AZ   | HA required|
| NAT Gateways      | 1          | 3          | +2 for HA  |
| EKS Nodes         | N          | M          | +X         |
| Total Cost        | R$ X,XXX   | R$ X,XXX   | +XX%       |
| Cost/Customer     | R$ X,XXX   | R$ X,XXX   | +XX%       |
| **Combined/Cust** | -          | -          | **R$ X,XXX** |
```

### 6. Infrastructure Components (Consolidated)

Detailed per-component breakdown with sharing attribution (combined view):

```
| Component  | Instance      | Sharing   | Customers | Prod Cost  | Homolog Cost | Cost/Customer |
|------------|---------------|-----------|-----------|------------|--------------|---------------|
| PostgreSQL | db.m7g.large  | DEDICATED | 1         | R$ 1,490   | R$ 632       | R$ 2,122      |
| Valkey     | cache.m7g.lg  | SHARED    | 5         | R$ 650     | R$ 562       | R$ 242        |
| EKS Nodes  | Nx c6i.xlarge | SHARED    | 5         | R$ [calc]  | R$ [calc]    | R$ [calc]     |
```

### 7. Cost by Category

Groups costs for analysis and identifies cost drivers:

```
| Category   | Shared Cost | Dedicated Cost | Total/Customer | % of Total |
|------------|-------------|----------------|----------------|------------|
| Compute    | R$ 414      | R$ 0           | R$ 414         | 16%        |
| Database   | R$ 185      | R$ 1,490       | R$ 1,675       | 67%        |
| Cache      | R$ 130      | R$ 0           | R$ 130         | 5%         |
| Queue      | R$ 212      | R$ 0           | R$ 212         | 8%         |
| Network    | R$ 77       | R$ 0           | R$ 77          | 3%         |
```

### 8. Shared vs Dedicated Summary

Clear separation of cost types:

```
┌─────────────────────────────────────────┐
│ Shared Infrastructure:    R$ 1,018     │
│ Dedicated Infrastructure: R$ 1,490     │
│─────────────────────────────────────────│
│ Total per Customer:       R$ 2,508     │
└─────────────────────────────────────────┘
```

### 9. TPS Capacity Analysis

Validates infrastructure can handle the load:

```
| Metric                  | Value      |
|-------------------------|------------|
| Customer TPS Need       | 100 TPS    |
| Max Capacity (with auth)| 2,030 TPS  |
| Recommended Limit (80%) | 1,624 TPS  |
| Capacity Utilization    | 6.2%       |
| Status                  | ✅ OK      |
```

### 10. Profitability Analysis (Combined Environments)

Revenue vs cost calculation using combined environment costs:

```
| Environment      | Infrastructure | +25% Overhead | Fully-Loaded |
|------------------|----------------|---------------|--------------|
| Homolog          | R$ X,XXX       | R$ XXX        | R$ X,XXX     |
| Production       | R$ X,XXX       | R$ XXX        | R$ X,XXX     |
| **Combined**     | **R$ X,XXX**   | **R$ XXX**    | **R$ X,XXX** |

| Metric           | Value              |
|------------------|--------------------|
| Monthly Revenue  | R$ 100,000         |
| Combined Cost    | R$ X,XXX           |
| Gross Profit     | R$ XX,XXX          |
| Gross Margin     | XX.X%              |
| Break-Even Volume| X,XXX transactions |
```

**Note:** Combined cost = Homolog + Production (customer pays for both environments).

### 11. Summary

Key metrics and actionable recommendations including:
- Environment costs breakdown (Homolog vs Production)
- Combined infrastructure cost per customer
- Profitability status and break-even analysis
- Environment-specific recommendations

---

## Calculation Rationale

### Service Discovery Logic

The agent maps Docker services to AWS equivalents:

```
docker-compose.yml → AWS Service Mapping

postgres/postgresql  →  RDS PostgreSQL
mongo/mongodb       →  DocumentDB
redis/valkey        →  ElastiCache Valkey
rabbitmq            →  Amazon MQ
Go/Node apps        →  EKS Pods
```

**Infrastructure components always added:**
- EKS Control Plane (required for Kubernetes)
- EKS Nodes (compute for pods)
- ALB (load balancer for ingress)
- NAT Gateway (outbound internet access)

### Instance Sizing Logic (TPS-Based)

#### Compute Sizing

| TPS Range | EKS Nodes | Why |
|-----------|-----------|-----|
| 1-50 | 2x c6i.xlarge | Minimum HA setup |
| 50-200 | 3x c6i.xlarge | More headroom for scaling |
| 200-500 | 4x c6i.2xlarge | Larger instances for throughput |

#### Database Sizing (SHARED - schema-based)

For shared databases, size based on **total platform TPS** (all customers combined):

| Total Platform TPS | PostgreSQL | Read Replicas |
|--------------------|------------|---------------|
| 1-100 | db.m7g.large | 0 |
| 100-300 | db.m7g.xlarge | 1 |
| 300-500 | db.m7g.2xlarge | 2 |

#### Database Sizing (DEDICATED - isolated)

For dedicated databases, size based on **customer's TPS only**:

| Customer TPS | PostgreSQL | Read Replicas |
|--------------|------------|---------------|
| 1-50 | db.m7g.large | 0 |
| 50-150 | db.m7g.xlarge | 1 |
| 150-300 | db.m7g.2xlarge | 1-2 |

### Cost Attribution Formula

#### For SHARED components:

```
Cost per Customer = Total Component Cost ÷ Number of Customers Sharing

Example:
  Valkey Total Cost: R$ 650
  Customers Sharing: 5
  Cost per Customer: R$ 650 ÷ 5 = R$ 130
```

#### For DEDICATED components:

```
Cost per Customer = Total Component Cost (full cost)

Example:
  PostgreSQL DEDICATED: R$ 1,490
  Customers: 1 (only this customer)
  Cost per Customer: R$ 1,490
```

### Environment Differentiation

| Aspect | Production (São Paulo) | Homolog (Ohio) |
|--------|------------------------|----------------|
| **Region** | sa-east-1 | us-east-2 |
| **Pricing** | Higher (~35% more) | Lower |
| **Multi-AZ** | YES (HA required) | NO (testing only) |
| **Read Replicas** | Based on TPS | 0 (no need) |
| **Pod Replicas** | 3 per service | 1 per service |

**Why different regions?**
- Production in São Paulo: Low latency for Brazilian customers
- Homolog in Ohio: 35% cheaper, latency doesn't matter for testing

### Fully-Loaded Cost Calculation

```
Per-Customer Infrastructure
  + Support Overhead (15%)      ← Team, on-call, maintenance
  + Platform Fee (10%)          ← SaaS platform margin
  ───────────────────────────────
  = Fully-Loaded Cost

Example:
  Infrastructure:    R$ 2,508
  Support (15%):    +R$ 376
  Platform (10%):   +R$ 251
  ─────────────────────────
  Fully-Loaded:      R$ 3,135
```

### Profitability Calculation

```
Revenue = Price per Unit × Expected Volume
Profit  = Revenue - Fully-Loaded Cost
Margin  = (Profit ÷ Revenue) × 100

Break-Even Volume = Fully-Loaded Cost ÷ Price per Unit

Example:
  Price per Transaction: R$ 0.10
  Volume: 1,000,000/month
  Revenue: R$ 100,000
  Cost: R$ 3,135
  Profit: R$ 96,865
  Margin: 96.9%
  Break-Even: 31,350 transactions
```

### TPS Capacity Validation

Based on load test benchmarks:

| Configuration | With Auth | Without Auth | Notes |
|---------------|-----------|--------------|-------|
| 1 Pod/service | 815 TPS | 980 TPS | Baseline |
| 3 Pods/service | 2,030 TPS | 1,500 TPS | Near-linear scaling |

**Operational limit:** 80% of max capacity (headroom for spikes)

```
Customer needs 100 TPS
Current capacity: 2,030 TPS (with auth)
Operational limit: 1,624 TPS (80%)
Utilization: 100 ÷ 1,624 = 6.2%
Status: ✅ OK (plenty of headroom)
```

---

## Pricing Reference

### AWS sa-east-1 (São Paulo) - BRL/month

#### Compute & Network

| Component | Instance | Monthly Cost |
|-----------|----------|--------------|
| EKS Control Plane | - | R$ 365 |
| EKS Node | c6i.xlarge | R$ 852/node |
| EKS Node | c6i.2xlarge | R$ 1,708/node |
| Amazon MQ | mq.m7g.large | R$ 1,058 |
| Valkey | cache.m7g.large | R$ 650 |
| ALB | - | R$ 180 |
| NAT Gateway | - | R$ 205 |

#### Database (Single-AZ vs Multi-AZ)

| Component | Instance | Single-AZ | Multi-AZ | Read Replica |
|-----------|----------|-----------|----------|--------------|
| RDS PostgreSQL | db.m7g.large | R$ 745 | R$ 1,490 | +R$ 745/each |
| RDS PostgreSQL | db.m7g.xlarge | R$ 1,490 | R$ 2,980 | +R$ 1,490/each |
| RDS PostgreSQL | db.m7g.2xlarge | R$ 2,980 | R$ 5,960 | +R$ 2,980/each |
| DocumentDB | db.r8g.large | R$ 925 | R$ 1,850 | +R$ 925/each |
| DocumentDB | db.r8g.xlarge | R$ 1,850 | R$ 3,700 | +R$ 1,850/each |

**Multi-AZ = 2x cost** (standby instance in different AZ for automatic failover)

#### Storage

| Type | Cost | Notes |
|------|------|-------|
| RDS Storage (gp3) | R$ 0.58/GB/month | Minimum 20GB |
| RDS IOPS (gp3) | R$ 0.10/IOPS/month | Above 3,000 IOPS |
| DocumentDB Storage | R$ 0.50/GB/month | Auto-scales |
| EBS (gp3) | R$ 0.42/GB/month | EKS node storage |
| S3 Standard | R$ 0.12/GB/month | Backups |

### AWS us-east-2 (Ohio) - BRL/month (~35% cheaper)

| Component | Instance | Single-AZ | Notes |
|-----------|----------|-----------|-------|
| EKS Control Plane | - | R$ 265 | - |
| EKS Node | c6i.xlarge | R$ 657/node | - |
| RDS PostgreSQL | db.m7g.large | R$ 632 | No Multi-AZ needed |
| DocumentDB | db.r8g.large | R$ 785 | No Multi-AZ needed |
| Amazon MQ | mq.m7g.large | R$ 882 | - |
| Valkey | cache.m7g.large | R$ 562 | - |
| ALB | - | R$ 115 | - |
| NAT Gateway | - | R$ 174 | - |

---

## Workflow Summary

```
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: User Request                                             │
│ "Estimate infrastructure for 100 TPS customer"                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: Skill Collects Basic Info                                │
│ - Repo path                                                      │
│ - TPS: 100                                                       │
│ - Total customers: 5                                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: Environment Selection                                    │
│ "Which environments to calculate?"                               │
│ [x] Both (Homolog + Production)                                  │
│ [ ] Production only                                              │
│ [ ] Homolog only                                                 │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 4: Read LerianStudio/helm & Collect Sharing Model           │
│ - Read actual CPU/memory from LerianStudio/helm at runtime       │
│ - charts/midaz, charts/reporter, charts/plugin-access-manager    │
│ - Per-component sharing model                                    │
│ - Billing: R$ 0.10/transaction, 1M/month                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 5: Skill Dispatches Agent with ALL Data                     │
│ Task(subagent_type="ring:infrastructure-cost-estimator",         │
│      prompt="ALL DATA PROVIDED...")                              │
│ Includes: Actual values from LerianStudio/helm, Environments     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 6: Agent Calculates PER ENVIRONMENT                         │
│ - Uses actual CPU/memory from LerianStudio/helm (in prompt)      │
│ - Calculates EKS nodes from actual resources                     │
│ - HOMOLOG: Single-AZ, 1 replica, Ohio pricing                    │
│ - PRODUCTION: Multi-AZ, 3 replicas, São Paulo pricing            │
│ - Applies sharing model per component                            │
│ - Combines environment costs for profitability                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 7: Agent Returns Environment-Aware Report                   │
│ 10 required sections with side-by-side environment comparison    │
└──────────────────────────────────────────────────────────────────┘
```

### Checklist Before Dispatch

```
[ ] Repo path collected?
[ ] TPS collected?
[ ] Total customers collected?
[ ] Environments selected (Homolog, Production, or Both)?
[ ] LerianStudio/helm values read at runtime?
[ ] For EACH component: Shared or Dedicated?
[ ] Billing unit collected?
[ ] Price per unit collected?
[ ] Expected volume collected?

If any NO → Ask user first, then dispatch.
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Skill orchestrates, agent calculates** | Separation of concerns: UI/collection vs computation |
| **Per-component sharing model** | Different components have different isolation needs |
| **Environment-aware calculations** | Real-world deployments need both Homolog and Production |
| **Dynamic data from LerianStudio/helm (v6.0)** | Always current values, no stale hardcoded data |
| **Read at runtime, not hardcoded** | Single source of truth, smaller prompts |
| **Combined environment costs** | Customer pays for both environments |
| **TPS-based sizing** | Predictable scaling based on throughput |
| **80% capacity limit** | Headroom for traffic spikes |
| **25% overhead (15% support + 10% platform)** | Realistic fully-loaded cost |
| **Multi-AZ for production only** | HA where it matters, cost savings for testing |
| **São Paulo for prod, Ohio for homolog** | Latency for prod, cost for testing |
| **NAT Gateway always shared** | Platform-level resource, cannot be dedicated |
| **Fallback to Midaz core** | If plugin not available, use Midaz setup as baseline |

---

## Example Dispatch (v6.0)

**The skill reads LerianStudio/helm at runtime and passes actual values:**

```yaml
Task tool:
  subagent_type: "ring:infrastructure-cost-estimator"
  prompt: |
    Calculate infrastructure costs and profitability.

    ALL DATA PROVIDED (do not ask questions):

    Infrastructure:
    - App Repo: /workspace/midaz
    - Helm Source: LerianStudio/helm (values read below)
    - TPS: 100
    - Total Customers on Platform: 5

    Environments to Calculate: [Homolog, Production]

    Actual Resource Configurations (READ from LerianStudio/helm):
    [SKILL INSERTS VALUES FROM charts/midaz/values.yaml]
    [SKILL INSERTS VALUES FROM charts/reporter/values.yaml]
    [SKILL INSERTS VALUES FROM charts/plugin-access-manager/values.yaml]

    Example format:
    | Service | CPU Request | Memory Request | HPA | Source |
    |---------|-------------|----------------|-----|--------|
    | onboarding | 1500m | 512Mi | 2-5 | midaz |
    | transaction | 2000m | 512Mi | 3-9 | midaz |
    | auth | 500m | 256Mi | 3-9 | access-manager |
    | ... | ... | ... | ... | ... |

    Component Sharing Model:
    | Component | Sharing | Customers |
    |-----------|---------|-----------|
    | VPC | SHARED | 5 |
    | EKS Cluster | SHARED | 5 |
    | EKS Nodes | SHARED | 5 |
    | PostgreSQL | DEDICATED | 1 |
    | Valkey | SHARED | 5 |
    | DocumentDB | SHARED | 5 |
    | RabbitMQ | SHARED | 5 |
    | ALB | SHARED | 5 |
    | NAT Gateway | ALWAYS SHARED | ALL |

    Database Configuration (Production):
    - Multi-AZ: YES
    - Read Replicas: Based on TPS

    Billing Model:
    - Billing Unit: transaction
    - Price per Unit: R$ 0.10
    - Expected Volume: 1,000,000/month

    Calculate and return all 10 required sections:
    1. Discovered Services (from Helm charts)
    2. Compute Resources (from actual values in prompt)
    3. Homolog Environment Costs
    4. Production Environment Costs
    5. Environment Comparison
    6. Cost by Category
    7. Shared vs Dedicated Summary
    8. TPS Capacity Analysis
    9. Profitability Analysis (combined)
    10. Summary
```

---

## Related Files

| File | Description |
|------|-------------|
| `finops-team/skills/infrastructure-cost-estimation/SKILL.md` | Skill definition (orchestrator) |
| `finops-team/agents/infrastructure-cost-estimator.md` | Agent definition (calculator) |
| `finops-team/skills/using-finops-team/SKILL.md` | Plugin introduction |

---

## Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Assume all components are shared" | Customer may have dedicated DB | **ASK for each component** |
| "Skip component questions" | Cost attribution will be wrong | **Must ask shared/dedicated** |
| "Agent can figure it out" | Agent calculates, skill orchestrates | **Skill collects all data** |
| "Just use total customers" | Some components may be dedicated | **Per-component model required** |
| "Data is missing, assume values" | Assumptions lead to wrong calculations | **STOP and report missing data** |
