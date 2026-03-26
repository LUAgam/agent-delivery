# Infrastructure Tiers by TPS

**Purpose:** Pre-configured infrastructure tiers optimized for specific TPS ranges.

**Source:** Based on actual Midaz service capacities from Helm charts and production analysis.

---

## Service Capacity Reference

| Service | CPU Request | TPS per Replica | Bottleneck |
|---------|-------------|-----------------|------------|
| **auth** | 500m | ~670 TPS | ✅ PRIMARY BOTTLENECK |
| **transaction** | 2000m | ~815 TPS | Secondary |
| **onboarding** | 1500m | ~750 TPS | Background |
| **identity** | 100m | ~135 TPS | Lightweight |

**Note:** auth service is the bottleneck (lowest TPS/replica), so tier sizing is based on auth capacity.

---

## Tier 1: Starter (50-100 TPS)

**Target:** Small deployments, proof of concept, single tenant with low traffic

### Configuration

**Production:**
- **Replicas:** 1 per service (no HA)
- **EKS Nodes:** 2× c6i.large (2 vCPU, 4 GiB each)
- **Database:** db.t4g.medium (2 vCPU, 4 GiB)
- **Cache:** cache.t4g.medium
- **RabbitMQ:** mq.t3.micro

**Homolog:**
- **EKS Nodes:** 1× c6i.large
- **Database:** db.t4g.small

### Capacity

| Metric | Value |
|--------|-------|
| **Max TPS** | 670 TPS (1 auth replica) |
| **Recommended TPS** | 100 TPS (15% utilization) |
| **Headroom** | 570 TPS available |

### Estimated Cost (Monthly)

| Environment | Cost |
|-------------|------|
| Homolog | R$ 3,200 |
| Production | R$ 8,500 |
| **Total** | **R$ 11,700** |

**Cost Reduction vs Standard:** -58% (from R$ 27,545)

---

## Tier 2: Growth (100-500 TPS)

**Target:** Growing business, multiple tenants, moderate traffic

### Configuration

**Production:**
- **Replicas:** 2 per critical service (auth, transaction)
- **EKS Nodes:** 3× c6i.xlarge (4 vCPU, 8 GiB each)
- **Database:** db.m7g.large (2 vCPU, 8 GiB) + 1 read replica
- **Cache:** cache.m7g.medium (Multi-AZ)
- **RabbitMQ:** mq.m5.large (active/standby)

**Homolog:**
- **EKS Nodes:** 2× c6i.large
- **Database:** db.t4g.large

### Capacity

| Metric | Value |
|--------|-------|
| **Max TPS** | 1,340 TPS (2 auth replicas) |
| **Recommended TPS** | 500 TPS (37% utilization) |
| **Headroom** | 840 TPS available |

### Estimated Cost (Monthly)

| Environment | Cost |
|-------------|------|
| Homolog | R$ 4,500 |
| Production | R$ 14,800 |
| **Total** | **R$ 19,300** |

**Cost Reduction vs Standard:** -30% (from R$ 27,545)

---

## Tier 3: Business (500-1,500 TPS)

**Target:** Established business, high availability required, multi-tenant

### Configuration

**Production:**
- **Replicas:** 3 per service (1 per AZ for HA)
- **EKS Nodes:** 4× c6i.xlarge (4 vCPU, 8 GiB each)
- **Database:** db.m7g.large (2 vCPU, 8 GiB) + 1 read replica
- **Cache:** cache.m7g.large (Multi-AZ)
- **RabbitMQ:** mq.m7g.large (active/standby)

**Homolog:**
- **EKS Nodes:** 2× c6i.xlarge
- **Database:** db.m7g.large

### Capacity

| Metric | Value |
|--------|-------|
| **Max TPS** | 2,010 TPS (3 auth replicas) |
| **Recommended TPS** | 1,500 TPS (75% utilization) |
| **Headroom** | 510 TPS available |

### Estimated Cost (Monthly)

| Environment | Cost |
|-------------|------|
| Homolog | R$ 5,983 |
| Production | R$ 21,562 |
| **Total** | **R$ 27,545** |

**Note:** This is the CURRENT standard configuration analyzed in the cost report.

---

## Tier 4: Enterprise (1,500-5,000 TPS)

**Target:** Large scale, mission critical, requires high performance

### Configuration

**Production:**
- **Replicas:** 6-9 per service (autoscaling)
- **EKS Nodes:** 8× c6i.2xlarge (8 vCPU, 16 GiB each)
- **Database:** db.m7g.2xlarge (8 vCPU, 32 GiB) + 3 read replicas
- **Cache:** cache.r7g.xlarge (Multi-AZ)
- **RabbitMQ:** mq.m7g.2xlarge (active/standby)

**Homolog:**
- **EKS Nodes:** 3× c6i.xlarge
- **Database:** db.m7g.xlarge

### Capacity

| Metric | Value |
|--------|-------|
| **Max TPS** | 6,030 TPS (9 auth replicas) |
| **Recommended TPS** | 5,000 TPS (83% utilization) |
| **Headroom** | 1,030 TPS available |

### Estimated Cost (Monthly)

| Environment | Cost |
|-------------|------|
| Homolog | R$ 8,200 |
| Production | R$ 48,500 |
| **Total** | **R$ 56,700** |

**Cost Increase vs Standard:** +106% (from R$ 27,545)

---

## Tier Comparison Table

| Tier | TPS Range | EKS Nodes (Prod) | DB Instance | Monthly Cost | Cost/TPS |
|------|-----------|------------------|-------------|--------------|----------|
| **Starter** | 50-100 | 2× c6i.large | db.t4g.medium | R$ 11,700 | R$ 117.00 |
| **Growth** | 100-500 | 3× c6i.xlarge | db.m7g.large | R$ 19,300 | R$ 38.60 |
| **Business** | 500-1,500 | 4× c6i.xlarge | db.m7g.large | R$ 27,545 | R$ 18.36 |
| **Enterprise** | 1,500-5,000 | 8× c6i.2xlarge | db.m7g.2xlarge | R$ 56,700 | R$ 11.34 |

**Key Insight:** Cost per TPS decreases significantly with scale (economies of scale).

---

## Tier Selection Guide

### When to Choose Each Tier

| Your Situation | Recommended Tier | Why |
|----------------|------------------|-----|
| POC, testing, < 100 TPS | **Starter** | Lowest cost, adequate performance |
| Growing business, 100-500 TPS | **Growth** | Balance of cost and capacity |
| Production app, 500-1,500 TPS | **Business** | Full HA, optimal cost/performance |
| Mission critical, > 1,500 TPS | **Enterprise** | Maximum performance and reliability |

### Upgrade Path

```
Starter (R$ 11.7k/mo, 100 TPS)
   ↓ Business grows
Growth (R$ 19.3k/mo, 500 TPS)
   ↓ Scale increases
Business (R$ 27.5k/mo, 1,500 TPS)
   ↓ Enterprise scale
Enterprise (R$ 56.7k/mo, 5,000 TPS)
```

**Upgrades can be done with zero downtime** using Kubernetes rolling updates.

---

## Important Notes

### 1. Backup Costs Not Included

The costs above **do not include backup storage**. Add based on retention policy:

| Retention | Additional Cost/Month |
|-----------|----------------------|
| 7 days | R$ 0 (free tier) |
| 90 days | R$ 347 |
| 1 year | R$ 1,387 |
| 5 years | R$ 6,935 |

### 2. Multi-Tenant Considerations

For **shared infrastructure** (multiple customers), divide costs:

```
Example: 5 customers on Growth tier
Total Cost: R$ 19,300/month
Cost per Customer: R$ 3,860/month
```

### 3. Reserved Instances Discount

All tiers can benefit from **Reserved Instances** (1-3 year commitment):

| Commitment | Discount |
|------------|----------|
| 1 year | ~30% off compute |
| 3 years | ~50% off compute |

**Example:** Business tier with 3-year RI = R$ 27,545 → R$ 23,413/month (-15% total)

---

## Custom Configuration

If your TPS needs don't fit these tiers, use **custom TPS input** in the skill:

1. Skill will calculate required replicas based on TPS
2. Agent will size infrastructure accordingly
3. Returns cost estimate for your specific requirements

**Formula:**
```
Required auth replicas = (Target TPS ÷ 670) × 1.25 (for headroom)
Required nodes = (replicas × CPU per pod) ÷ (node vCPU × 0.85 usable)
```

---

## Tier Configuration Details

### Starter Tier - Detailed Specs

**Production Environment:**
```yaml
EKS:
  nodes: 2
  instance_type: c6i.large (2 vCPU, 4 GiB)

Services:
  identity: 1 replica
  auth: 1 replica
  auth-backend: 1 replica
  onboarding: 1 replica
  transaction: 1 replica

Database:
  auth-postgresql: db.t4g.medium (Single-AZ)
  midaz-postgresql: db.t4g.medium (Single-AZ)
  documentdb: db.t4g.medium (Single-AZ)

Cache:
  auth-valkey: cache.t4g.medium (standalone)
  midaz-valkey: cache.t4g.medium (standalone)

Queue:
  rabbitmq: mq.t3.micro (single broker)
```

### Growth Tier - Detailed Specs

**Production Environment:**
```yaml
EKS:
  nodes: 3
  instance_type: c6i.xlarge (4 vCPU, 8 GiB)

Services:
  identity: 1 replica
  auth: 2 replicas
  auth-backend: 1 replica
  onboarding: 2 replicas
  transaction: 2 replicas

Database:
  auth-postgresql: db.m7g.large (Multi-AZ + 1 replica)
  midaz-postgresql: db.m7g.large (Multi-AZ + 1 replica)
  documentdb: db.m7g.large (Multi-AZ + 1 replica)

Cache:
  auth-valkey: cache.m7g.medium (Multi-AZ)
  midaz-valkey: cache.m7g.medium (Multi-AZ)

Queue:
  rabbitmq: mq.m5.large (active/standby)
```

### Business Tier - Detailed Specs

**Production Environment:**
```yaml
EKS:
  nodes: 4
  instance_type: c6i.xlarge (4 vCPU, 8 GiB)

Services:
  identity: 1 replica
  auth: 3 replicas (1 per AZ)
  auth-backend: 1 replica
  onboarding: 2 replicas
  transaction: 3 replicas (1 per AZ)

Database:
  auth-postgresql: db.m7g.large (Multi-AZ + 1 replica)
  midaz-postgresql: db.m7g.large (Multi-AZ + 1 replica)
  documentdb: db.r8g.large (Multi-AZ + 1 replica)

Cache:
  auth-valkey: cache.m7g.large (Multi-AZ)
  midaz-valkey: cache.m7g.large (Multi-AZ)

Queue:
  rabbitmq: mq.m7g.large (active/standby)
```

### Enterprise Tier - Detailed Specs

**Production Environment:**
```yaml
EKS:
  nodes: 8
  instance_type: c6i.2xlarge (8 vCPU, 16 GiB)

Services:
  identity: 3 replicas
  auth: 9 replicas (3 per AZ)
  auth-backend: 3 replicas
  onboarding: 6 replicas
  transaction: 9 replicas (3 per AZ)

Database:
  auth-postgresql: db.m7g.2xlarge (Multi-AZ + 3 replicas)
  midaz-postgresql: db.m7g.2xlarge (Multi-AZ + 3 replicas)
  documentdb: db.r8g.2xlarge (Multi-AZ + 3 replicas)

Cache:
  auth-valkey: cache.r7g.xlarge (Multi-AZ, clustered)
  midaz-valkey: cache.r7g.xlarge (Multi-AZ, clustered)

Queue:
  rabbitmq: mq.m7g.2xlarge (active/standby)
```

---

## References

- **Source Data:** Midaz infrastructure cost report (2026-01-30)
- **Helm Charts:** LerianStudio/helm repository
- **Service Capacities:** Based on actual production analysis at 50 TPS
- **AWS Pricing:** São Paulo (sa-east-1) region, January 2026
