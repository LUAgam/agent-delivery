# Helm Values Structure (Lerian Standard)

## ConfigMap vs Secrets Classification

```text
CONFIGMAP (non-sensitive):
  ✅ SERVER_PORT, SERVER_ADDRESS, LOG_LEVEL, ENV_NAME
  ✅ DB_HOST, DB_PORT, DB_NAME, DB_USER (NOT password)
  ✅ MONGO_HOST, MONGO_PORT, MONGO_NAME, MONGO_USER
  ✅ REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PROTOCOL
  ✅ RABBITMQ_HOST, RABBITMQ_PORT_AMQP, RABBITMQ_URI
  ✅ OTEL_*, ENABLE_TELEMETRY, SWAGGER_*
  ✅ PLUGIN_AUTH_ADDRESS, PLUGIN_AUTH_ENABLED
  ✅ Feature flags, timeouts, pool sizes
  ✅ Service URLs (MIDAZ_*, BTG_BASE_URL, etc.)

SECRETS (sensitive):
  🔒 DB_PASSWORD, MONGO_PASSWORD, REDIS_PASSWORD
  🔒 RABBITMQ_DEFAULT_PASS
  🔒 API keys (*_API_KEY, *_SECRET, *_TOKEN)
  🔒 LICENSE_KEY, ORGANIZATION_IDS
  🔒 OAuth credentials (*_CLIENT_ID, *_CLIENT_SECRET)
  🔒 Encryption keys (CRYPTO_*, WEBHOOK_SECRET)

RULE: If exposed in logs would be harmful → Secret
```

---

## Top-Level values.yaml Structure

<cannot_skip>
values.yaml MUST follow this exact structure. Do NOT invent custom structures.
</cannot_skip>

```yaml
# 1. Global overrides
nameOverride: ""
fullnameOverride: ""
namespaceOverride: "{namespace}"

# 2. Global external dependency configuration (if applicable)
global:
  externalPostgresDefinitions:
    enabled: false
    connection:
      host: ""
      port: "5432"
    postgresAdminLogin:
      useExistingSecret:
        name: ""
      username: ""
      password: ""
    credentials:
      useExistingSecret:
        name: ""
      username: ""
      password: ""

# 3. Per-component configuration (REPEAT for each component)
{component}:
  name: "{service_name}-{component}"
  enabled: true
  replicaCount: 1
  revisionHistoryLimit: 10

  image:
    repository: ghcr.io/lerianstudio/{service_name}-{component}
    pullPolicy: IfNotPresent
    tag: "1.0.0"
  imagePullSecrets: []

  nameOverride: ""
  fullnameOverride: ""

  annotations: {}
  podAnnotations: {}

  deploymentStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0

  service:
    type: ClusterIP                    # ALWAYS ClusterIP
    port: {assigned_port}
    annotations: {}

  ingress:
    enabled: false
    className: "nginx"
    annotations: {}
    hosts: []
    tls: []

  resources:
    limits:
      cpu: 200m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi

  autoscaling:
    enabled: true
    minReplicas: 1
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
    targetMemoryUtilizationPercentage: 80
    scaleDownStabilizationSeconds: 300

  pdb:
    enabled: true
    maxUnavailable: 1
    minAvailable: 0
    annotations: {}

  readinessProbe:
    initialDelaySeconds: 10
    periodSeconds: 5
    timeoutSeconds: 3
    successThreshold: 1
    failureThreshold: 3

  livenessProbe:
    initialDelaySeconds: 15
    periodSeconds: 20
    timeoutSeconds: 5
    successThreshold: 1
    failureThreshold: 3

  nodeSelector: {}
  tolerations: {}
  affinity: {}

  useExistingSecret: false
  existingSecretName: ""

  serviceAccount:
    create: true
    annotations: {}
    name: ""

  configmap:
    annotations: {}
    # Non-sensitive configuration
    ENV_NAME: "development"
    VERSION: "v1.0.0"
    SERVER_PORT: "{port}"
    SERVER_ADDRESS: ":{port}"
    LOG_LEVEL: "debug"
    # ... service-specific vars

  secrets: {}
    # Sensitive configuration (passwords, keys, tokens)
    # DB_PASSWORD: ""
    # API_KEY: ""

  extraEnvVars: {}

# 4. Common shared configuration (if multi-component)
common:
  configmap:
    ENV_NAME: "development"
    # Shared vars across all components

# 5. Dependency configurations
# ... (postgresql, mongodb, rabbitmq, valkey, keda)
```

---

## Mandatory Environment Variable Groups

```text
FOR EVERY service, MUST include:

1. APP CONFIG:
   ENV_NAME, VERSION, SERVER_PORT, SERVER_ADDRESS, LOG_LEVEL

2. TELEMETRY (if applicable):
   ENABLE_TELEMETRY, OTEL_RESOURCE_SERVICE_NAME, OTEL_LIBRARY_NAME,
   OTEL_RESOURCE_SERVICE_VERSION, OTEL_RESOURCE_DEPLOYMENT_ENVIRONMENT,
   OTEL_EXPORTER_OTLP_ENDPOINT

3. HEALTH (if service has health endpoint):
   HEALTH_PORT (for workers without HTTP server)

4. AUTH (if applicable):
   PLUGIN_AUTH_ENABLED, PLUGIN_AUTH_ADDRESS

5. DATABASE (per type used):
   PostgreSQL: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSL_MODE
   MongoDB: MONGO_URI, MONGO_HOST, MONGO_PORT, MONGO_NAME, MONGO_USER, MONGO_PASSWORD
   Redis/Valkey: REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, REDIS_PROTOCOL
   RabbitMQ: RABBITMQ_URI, RABBITMQ_HOST, RABBITMQ_PORT_AMQP, RABBITMQ_DEFAULT_USER,
             RABBITMQ_DEFAULT_PASS

VERIFY: Compare with application's .env.example or config struct to ensure
        ALL env vars are covered. Missing vars cause runtime failures.
```

<block_condition>
HARD GATE: MUST read the application's .env.example or config.go to extract
ALL expected environment variables. Do NOT guess. Missing env vars are the
#1 cause of CrashLoopBackOff in production.
</block_condition>
