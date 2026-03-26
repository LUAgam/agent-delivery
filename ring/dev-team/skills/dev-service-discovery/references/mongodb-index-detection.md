# MongoDB Index Detection & Script Generation

**Only execute this phase if MongoDB was detected in any module during Phase 3.**

This phase detects MongoDB index definitions in two places:
1. **In-code indexes** — `EnsureIndexes()` methods in repository files that create indexes at startup
2. **Script-based indexes** — `scripts/mongodb/*.js` files meant to be run via `mongosh`

---

## Step 1: Detect In-Code Index Definitions

```text
For EACH module where MongoDB was detected:

1. Find EnsureIndexes methods:
   - Grep tool (regex): grep -E 'func.*EnsureIndexes|IndexModel|CreateIndex|createIndex'
     in {base_path}mongodb/ OR {base_path}mongo/ --include="*.go"
   - For each file with matches, extract:
     a. Collection name (from the receiver's collection field or constant)
     b. Index keys (from bson.D{{Key: "field", Value: 1}})
     c. Index options (unique, sparse, TTL, etc.)
     d. Index name (if specified via SetName)

2. Parse index models:
   - Look for mongo.IndexModel{} structs
   - Extract Keys (bson.D fields) and Options
   - Map each to: {collection, keys: [{field, order}], unique: bool, name: string}

Store results:
  module.mongo_indexes_in_code = [
    {
      file: "service_repository.go",
      collection: "services",
      indexes: [
        {keys: [{"service_name": 1}], unique: true, name: ""},
        {keys: [{"tenant_id": 1, "service_name": 1}], unique: true, name: ""},
      ]
    }
  ]
```

---

## Step 2: Detect Existing Index Scripts

```text
Scan for existing MongoDB index scripts:

1. Glob tool: pattern "scripts/mongodb/*.js" OR "scripts/mongo/*.js"
2. For each script found:
   a. Extract collection name (from db.getCollection("name"))
   b. Extract index definitions (from both createIndex() and createIndexSafely() calls)
   c. Map each to: {file, collection, indexes: [{keys, options}]}

3. Also check for:
   - Makefile targets that reference mongosh or mongo scripts
   - Docker/docker-compose commands that run index scripts
   - CI/CD pipeline steps that execute index creation

Store results:
  existing_scripts = [
    {
      file: "scripts/mongodb/create-service-indexes.js",
      collection: "services",
      indexes: [
        {keys: {"tenant_id": 1}, name: "idx_tenant_id"},
        {keys: {"tenant_id": 1, "service_name": 1}, name: "idx_tenant_service_unique", unique: true},
      ]
    }
  ]
```

---

## Step 3: Cross-Reference and Identify Gaps

```text
Compare in-code indexes vs script indexes:

For each in-code index:
  - Find matching script index (same collection + same key fields)
  - If found → status: "covered"
  - If NOT found → status: "missing_script"

For each script index:
  - Find matching in-code index
  - If found → status: "covered"
  - If NOT found → status: "script_only" (index exists in script but not enforced in code)

Generate gap analysis:
  index_coverage = {
    covered: [{collection, keys, in_code_file, script_file}],
    missing_script: [{collection, keys, in_code_file}],  // needs script
    script_only: [{collection, keys, script_file}],       // extra scripts, no code match
  }
```

---

## Step 3.5: Validate Existing S3 Migration JSON Files

**Execute BEFORE generating new scripts. Checks that existing `.up.json` and `.down.json` files in S3 follow the canonical format.**

```text
For EACH existing S3 migration file (downloaded in Step 2 or fetched now):

1. Verify AWS CLI + bucket access (same as Step 5 checks)
2. List existing migrations: aws s3 ls s3://{bucket}/{service}/ --recursive | grep mongodb
3. Download each .up.json and .down.json for comparison

VALIDATE each .up.json:

V1. Index name present:
    - Every index in "indexes" array MUST have "name" in "options"
    - Name MUST follow idx_* convention
    - ⛔ FAIL: {"keys": {"field": 1}, "options": {"unique": true}}  ← missing "name"
    - ✅ PASS: {"keys": {"field": 1}, "options": {"unique": true, "name": "idx_field_unique"}}

V2. Key order matches code:
    - For compound indexes, the key order in the JSON MUST match the order
      in the Go source code (bson.D is ordered)
    - JSON object key order matters for MongoDB compound indexes (ESR rule)
    - ⛔ FAIL: code has {search.document: 1, external_id: 1} but JSON has {external_id: 1, search.document: 1}
    - ✅ PASS: both code and JSON have {search.document: 1, external_id: 1}

V3. Index count matches code:
    - Number of indexes in .up.json MUST match number of in-code indexes for that collection
    - Missing indexes → report as "S3 migration outdated — missing N indexes"
    - Extra indexes → report as "S3 migration has N extra indexes not in code — review"

VALIDATE each .down.json:

V4. Down references match up:
    - Every "name" in the .up.json MUST appear in the .down.json "indexNames" array
    - ⛔ FAIL: .up.json has "idx_field_unique" but .down.json has "field_1" (auto-generated name)
    - ✅ PASS: .down.json has ["idx_field_unique"] matching .up.json

OUTPUT format:
  S3 Migration Validation:
  | File | V1 (names) | V2 (key order) | V3 (count) | V4 (down match) | Status |
  |------|------------|----------------|------------|-----------------|--------|
  | holder/000001_holders_indexes | ✅ | ✅ | ✅ | ✅ | PASS |
  | alias/000001_aliases_indexes  | ⛔ missing names | ⛔ key order | ✅ | ⛔ auto-gen names | FAIL |

If ANY validation fails → fix the JSON files and re-upload BEFORE generating new scripts.
```

---

## Step 4: Generate Index Scripts for Missing Coverage

**Only if `missing_script` entries exist.**

For each missing index, generate a `mongosh`-compatible script following the tenant-manager pattern.

**Naming convention for generated scripts:**
- `scripts/mongodb/create-{collection}-indexes.js`
- If the `scripts/mongodb/` directory doesn't exist, create it.
- If a script already exists for that collection, create a new file with a numeric suffix (e.g., `create-{collection}-indexes-2.js`) to avoid modifying existing scripts. The original script remains untouched.

**Index naming convention:**
- Single field: `idx_{field}` (e.g., `idx_tenant_id`)
- Compound: `idx_{field1}_{field2}` (e.g., `idx_tenant_service`)
- Unique: append `_unique` (e.g., `idx_tenant_service_unique`)
- Nested fields: replace dots with underscores (e.g., `modules.name` → `idx_modules_name`)

**⛔ HARD GATE: Index naming is MANDATORY in S3 migration JSON files.**
Every index in a `.up.json` file MUST have an explicit `"name": "idx_..."` in its `options`.
The corresponding `.down.json` MUST use those exact names in `indexNames`.
Indexes without explicit names use MongoDB's auto-generated names (e.g., `field_1`),
which are inconsistent across environments and break down migrations.

### Script Template

```javascript
// MongoDB Index Creation Script for {Collection} Collection
// =====================================================
//
// Purpose:
//   Creates indexes for the '{collection}' collection detected from
//   in-code EnsureIndexes() in {source_file}.
//
// Usage:
//   mongosh "mongodb://localhost:27017/{database}" {script_path}
//
//   Or with authentication:
//   mongosh "mongodb://user:pass@host:port/{database}?authSource=admin" {script_path}
//
// Indexes Created:
//   {numbered list of indexes with descriptions}
//
// Notes:
//   - Script is idempotent (safe to run multiple times)
//   - Checks for existing indexes before creating
//   - Logs success/failure for each index
//
// =====================================================

// Helper function to safely create an index
function createIndexSafely(collection, keys, options) {
    // Compute fallback name from keys if options.name is not provided
    const indexName = options.name || Object.entries(keys).map(([k, v]) => `${k}_${v}`).join("_");
    options.name = indexName;
    const existingIndexes = collection.getIndexes();
    const indexExists = existingIndexes.some(idx => idx.name === indexName);

    if (indexExists) {
        print(`  [SKIP] Index '${indexName}' already exists`);
        return true;
    }

    try {
        collection.createIndex(keys, options);
        print(`  [OK] Index '${indexName}' created successfully`);
        return true;
    } catch (err) {
        print(`  [ERROR] Failed to create index '${indexName}': ${err.message}`);
        return false;
    }
}

// Main execution
print("");
print("=".repeat(60));
print("MongoDB Index Creation - {Collection} Collection");
print("=".repeat(60));
print("");

const coll = db.getCollection("{collection}");
print(`Database: ${db.getName()}`);
print(`Collection: {collection}`);
print("");
print("Creating indexes...");
print("");

let success = true;

// {For each detected index, generate a createIndexSafely call}
// Index N: {description based on keys and purpose}
success = createIndexSafely(coll,
    { "{field}": 1 },
    { name: "idx_{field}" }
) && success;

// ... repeat for each index ...

print("");
print("-".repeat(60));

if (success) {
    print("All indexes created/verified successfully");
} else {
    print("WARNING: Some indexes failed to create - review errors above");
}

print("");
print("Current indexes:");
print("");
const indexes = coll.getIndexes();
indexes.forEach(idx => {
    print(`  - ${idx.name}: ${JSON.stringify(idx.key)}${idx.unique ? " (unique)" : ""}`);
});
print("");
print("=".repeat(60));
print("Script completed");
print("=".repeat(60));
print("");
```

---

## Step 5: Upload Index Scripts to S3

**Execute after Step 4 (script generation) or when scripts already exist.**

Upload index scripts to S3 following the migrations bucket convention. Uses the AWS CLI installed on the local machine.

### S3 Path Convention

The migrations bucket follows the **Service → Module → Resource Type** hierarchy:

```
{bucket}/
├── {service}/
│   ├── {module_1}/
│   │   ├── mongodb/        ← index scripts go here
│   │   └── postgresql/     ← DDL migrations (not managed by this skill)
│   └── {module_2}/
│       ├── mongodb/
│       └── postgresql/
```

Example for ledger service:
```
lerian-development-migrations/
├── ledger/
│   ├── onboarding/
│   │   ├── mongodb/         ← 7 index migration files
│   │   └── postgresql/      ← 9 DDL migrations
│   └── transaction/
│       ├── mongodb/         ← 4 index migration files
│       └── postgresql/      ← 18 DDL migrations
```

Each module's MongoDB index scripts go into `s3://{bucket}/{service}/{module}/mongodb/`.

### Upload Flow

```text
1. Collect index scripts per module:
   - For each module with MongoDB detected (from Phase 3):
     - Glob: scripts/mongodb/*{module}* OR scripts/mongodb/*.js
     - Map each script to its target module
   - If none found → skip upload, log warning

2. Verify AWS CLI is available:
   - Run: aws --version
   - If not found → SKIP Step 5: Log warning "AWS CLI not installed. Skipping S3 upload."
     → Continue to Phase 4 report with upload status: "Skipped (AWS CLI not available)"

3. Ask the user which S3 bucket to use:
   "Found {N} index scripts to upload for service '{service_name}'.
    Which S3 bucket should I upload to?
    
    Example: lerian-development-migrations
    (scripts will be placed at: s3://{bucket}/{service}/{module}/mongodb/)"

   - Wait for user response
   - Store as: s3_bucket = "{user_response}"

4. Verify S3 access:
   - Run: aws s3 ls s3://{s3_bucket}/ 2>&1
   - If access denied → SKIP Step 5: Log warning "No access to bucket '{s3_bucket}'."
     → Continue to Phase 4 report with upload status: "Failed (access denied)"
   - If bucket not found → SKIP Step 5: Log warning "Bucket '{s3_bucket}' not found."
     → Continue to Phase 4 report with upload status: "Failed (bucket not found)"

5. Upload each script to the correct module path (best-effort, continue on failure):
   - For each (script, module) pair:
     aws s3 cp {script_path} \
       s3://{s3_bucket}/{service_name}/{module}/mongodb/{filename} \
       --content-type "application/javascript"
   - If a single upload fails, log the error and continue with remaining files
   - Track: successful_uploads = [], failed_uploads = []

6. Verify upload per module:
   - For each module:
     aws s3 ls s3://{s3_bucket}/{service_name}/{module}/mongodb/
   - List uploaded files with sizes
   - If count mismatches: report as "Partially uploaded ({X}/{Y})"

7. Report results:
   "Uploaded {N} index scripts to S3:
    ✅ s3://{s3_bucket}/ledger/onboarding/mongodb/create-metadata-indexes.js
    ✅ s3://{s3_bucket}/ledger/transaction/mongodb/create-metadata-indexes.js"
```

### Report Section Addition

Add to the Phase 4 HTML report:

```
┌──────────────────────────────────────────────────────┐
│ S3 Upload Status                                     │
├──────────────────────────┬───────────────────────────┤
│ Script                   │ Status                    │
├──────────────────────────┼───────────────────────────┤
│ create-service-indexes   │ ✅ Uploaded               │
│ create-resource-indexes  │ ✅ Uploaded               │
│ create-audit-indexes     │ ⚠️  Generated (not yet    │
│                          │    uploaded — run again)   │
└──────────────────────────┴───────────────────────────┘
S3 prefix: s3://{bucket}/{service}/{module}/mongodb/
```

---

## Report Section: MongoDB Index Coverage

Include this section in the Phase 4 HTML report when MongoDB indexes are detected.

### Table Format

```
┌──────────────────────────────────────────────────────────────┐
│ MongoDB Index Coverage                                       │
├──────────────┬────────────────────┬────────┬────────────────┤
│ Collection   │ Index Keys         │ Code   │ Script         │
├──────────────┼────────────────────┼────────┼────────────────┤
│ services     │ {service_name: 1}  │ ✅     │ ✅             │
│ services     │ {tenant_id: 1}     │ ❌     │ ✅ (extra)     │
│ services     │ {status: 1}        │ ❌     │ ✅ (extra)     │
│ audit_logs   │ {created_at: 1}    │ ✅     │ ❌ MISSING     │
└──────────────┴────────────────────┴────────┴────────────────┘

Legend:
  ✅ ✅  = Covered (in code + has script)
  ✅ ❌  = Missing script (generate one)
  ❌ ✅  = Script-only (no code match — review if still needed)
```

If there are **missing scripts**, show a callout:

```
⚠️  {N} indexes detected in code without corresponding scripts.
    Scripts will be generated automatically in scripts/mongodb/.
```

### Checklist Addition

For each module with MongoDB, add index status to the registration checklist:

```
- [ ] **Module:** `onboarding`
  - [ ] Resource: mongodb
  - [ ] MongoDB indexes: 3 in-code, 2 scripts (1 missing)
```
