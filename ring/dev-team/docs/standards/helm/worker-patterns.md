# Helm Worker Patterns (Lerian Standard)

## Dual-Mode Worker Pattern

MUST support both KEDA (default) and Deployment modes:

```text
MODE SELECTION:
  if keda.enabled OR keda.external:
    → Render ScaledJob (keda-scaled-job.yaml)
    → Render TriggerAuthentication (common/keda-trigger-authentication.yaml)
  else:
    → Render Deployment (deployment.yaml)
    → Render HPA (hpa.yaml)

GUARD in templates:
  ScaledJob:   {{- if or .Values.keda.enabled .Values.keda.external }}
  Deployment:  {{- if not (or .Values.keda.enabled .Values.keda.external) }}
```

---

## Worker Dual-Mode Pattern (Agent Reference)

```text
if service has background worker:

  MODE 1 - KEDA (default):
    Guard: {{- if or .Values.keda.enabled .Values.keda.external }}
    Template: keda-scaled-job.yaml
    + keda-trigger-authentication.yaml in common/

  MODE 2 - Deployment (fallback for multi-tenant):
    Guard: {{- if not (or .Values.keda.enabled .Values.keda.external) }}
    Template: deployment.yaml + hpa.yaml
    replicaCount: minimum pool (typically 2+)

  BOTH modes MUST include:
    - Same container spec (envFrom, resources, env vars)
    - initContainers for dependency checks
    - AWS IAM sidecar (conditional)
```

---

## ScaledJob Template (KEDA mode)

```text
MUST include:
- jobTargetRef with backoffLimit, ttlSecondsAfterFinished, activeDeadlineSeconds
- Container spec matching Deployment pattern (envFrom, resources, etc.)
- restartPolicy: Never
- Triggers with authenticationRef
- Polling interval, history limits, maxReplicaCount
```

---

## Worker Deployment Template (non-KEDA mode)

```text
MUST include:
- Same container spec as ScaledJob
- initContainers for dependency checks
- readinessProbe and livenessProbe
- VERIFY health endpoint paths against application code
- replicaCount as minimum pool size (typically 2+)
```
