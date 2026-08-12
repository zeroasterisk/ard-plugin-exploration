---
name: google-resource-discovery
description: >-
  Discover, evaluate, and dynamically invoke Google Cloud Managed MCP servers and
  Google Agent Skills using the ARD v0.5 catalog. Handles tiered authentication
  (Tier 0: No Auth Skills, Tier 1: API Keys/Public Docs, Tier 2: Managed GCP MCPs),
  respects user opt-outs, and guides graceful onboarding.
---

# Google Resource Discovery & Auth Tier Resolver Skill

Use this skill when the user asks about Google Cloud services, cloud architecture, BigQuery queries, GCS storage, Cloud Run deployments, GKE, Gemini API patterns, or finding available Google tools and MCP servers.

---

## 1. When to Use

- Discovering available Google Cloud MCP servers (`bigquery`, `storage`, `cloud-run`, `gke`, `cloud-sql`, `secops`, `developer-knowledge`).
- Locating Google Agent Skills (`well-architected`, `bigquery-guidelines`, `cloud-run-architecture`, `gcp-auth-recipes`, `gemini-api-patterns`).
- Checking if the local environment is authenticated for GCP tools before attempting execution.
- Assisting the user in onboarding or offering zero-auth offline fallbacks when GCP authentication is absent.

---

## 2. Resolving Capabilities via CLI Tool

Run the resolver script to search the canonical ARD catalog:

```bash
python3 /usr/local/google/home/alanblount/.gemini/config/plugins/ard-google-discovery/scripts/ard_resolver.py search "<user intent or query>" --json
```

### Auth Tiers:
- **Tier 0 (Zero Auth)**: Skills and documentation playbooks. Always ready to view and apply offline.
- **Tier 1 (API Key / Public Docs)**: Developer Knowledge MCP or Gemini API.
- **Tier 2 (GCP Account / ADC)**: Managed cloud services requiring active ADC (`gcloud auth application-default login`) or a Service Account.

---

## 3. Agent Behavioral Flow

1. **Query Catalog**: Run `ard_resolver.py search "<query>" --json`.
2. **Inspect Item Auth Readiness**:
   - If `status == "ready"`: Recommend or use the resource immediately.
   - If `tier == 2` and `status == "needs_onboarding"`:
     - Check if user has opted out of GCP recommendations (`ard_resolver.py prefs get`).
     - If not opted out, present the choice gracefully:
       > *"I found the **Google BigQuery MCP Server** which can execute this query directly, but it requires Google Cloud Application Default Credentials (ADC). Alternatively, we can use the **BigQuery SQL Guidelines Skill** to optimize your SQL query offline. Which do you prefer?"*
     - If the user agrees to connect GCP, record their decision (`ard_record_decision {"decision": "allowed", "service_identifier": "..."}`) and provide the onboarding command for their terminal:
       `gcloud auth application-default login`
     - If the user prefers not to use GCP, record their decision so they are never prompted again:
       `ard_resolver.py prefs opt-out`

---

## 4. Fallback Matrix

| Goal / Query | Tier 2 Tool (GCP Account) | Tier 0 Offline Fallback (Zero Auth) |
| :--- | :--- | :--- |
| **BigQuery / Analytical SQL** | `mcp:bigquery` | `skills:bigquery-guidelines` |
| **Cloud Run / Containers** | `mcp:cloud-run` | `skills:cloud-run-architecture` |
| **Cloud Architecture & Security** | `mcp:secops` | `skills:well-architected-security` |
| **Cost Optimization & FinOps** | `mcp:gcloud` | `skills:well-architected-cost-optimization` |
| **GCP Authentication Issues** | N/A | `skills:gcp-auth-recipes` |
| **Google API Docs & Code Samples** | N/A | `mcp:developer-knowledge` (Tier 1 Public) |
