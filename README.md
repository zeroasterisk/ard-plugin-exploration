# ARD Plugin Exploration (`ard-google-discovery`)

Prototype implementation and specification exploration for **Agent Resource Discovery (ARD v0.5)** combining Google Cloud Managed MCP Servers and Google Agent Skills with tiered authentication and progressive onboarding.

---

## 🎯 Overview & Addressing Detractor Concerns

### The Detractor Objection:
> *"Why publish an ARD catalog if it's useless without a Google Cloud account?"*

### The Multi-Tier Reality:
Agent capabilities exist on a **spectrum of friction**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Tier 0: Zero Auth (Friction: 0)                                         │
│ • google/skills/well-architected (Security, Reliability, Cost)          │
│ • google/skills/bigquery-guidelines (Offline SQL optimization patterns) │
│ • google/skills/cloud-run-architecture (Dockerfiles & microservices)    │
│ • google/skills/gcp-auth-recipes (ADC runbooks & setup playbooks)       │
├─────────────────────────────────────────────────────────────────────────┤
│ Tier 1: Public / Lightweight Keys (Friction: Low)                       │
│ • Google Developer Knowledge MCP (Docs & code samples - zero GCP auth)  │
│ • Gemini API Structured Outputs Skill (Free API key in AI Studio)       │
├─────────────────────────────────────────────────────────────────────────┤
│ Tier 2: Managed Cloud Services (Friction: Medium / Optional)            │
│ • BigQuery MCP Server (Public datasets, queries, enterprise schemas)    │
│ • Cloud Storage MCP Server (Buckets & object management)                │
│ • Cloud Run / GKE / Cloud SQL MCP Servers                               │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Tier 0 Skills provide immediate standalone value**: Developers write better code, design zero-trust perimeters, and optimize analytical SQL without needing GCP credentials.
2. **Opt-Out Control**: Users who never want GCP tools can enforce `opt-out` mode (`--opt-out` or `ard-resolver prefs opt-out`), completely filtering out Tier 2 resources.
3. **Progressive Onboarding**: When a user *does* need cloud scale (e.g. 50GB dataset query), the agent presents actionable onboarding (`gcloud auth application-default login`) or falls back to a Tier 0 offline skill.
4. **Persistent Decisions**: The agent stores user choices in `~/.config/ard/preferences.json`, ensuring the user is never repeatedly prompted or spammed.

---

## 📁 Repository Structure

```text
ard-plugin-exploration/
├── ai-catalog.json                # ARD v0.5 canonical catalog definition
├── src/
│   └── ard_resolver.py            # Standalone zero-dependency Python search & auth engine
├── tests/
│   └── test_ard_resolver.py       # Automated test suite testing all auth scenarios
├── plugin/                        # OpenCode / Antigravity / Jetski plugin bundle
│   ├── plugin.json
│   ├── ai-catalog.json
│   ├── scripts/
│   │   └── ard_resolver.py
│   ├── skills/
│   │   └── google-resource-discovery/
│   │       └── SKILL.md
│   └── rules/
│       └── auth_progressive_disclosure.md
└── README.md
```

---

## 🚀 CLI Usage

### 1. Search Catalog with Auth Tier Awareness
```bash
# Natural language search
python3 src/ard_resolver.py search "how to optimize bigquery sql"

# Search with strict GCP Opt-Out
python3 src/ard_resolver.py search "analyze analytical dataset" --opt-out

# Output machine-readable JSON for agents
python3 src/ard_resolver.py search "deploy container to cloud run" --json
```

### 2. Inspect Authentication Environment
```bash
# Check current system auth (Service Account, User ADC, gcloud CLI status)
python3 src/ard_resolver.py auth status
```

### 3. Manage Persistent Preferences
```bash
# View preferences
python3 src/ard_resolver.py prefs get

# Permanently opt out of all GCP account suggestions
python3 src/ard_resolver.py prefs opt-out

# Reset to default auto discovery
python3 src/ard_resolver.py prefs opt-in
```

---

## 🧪 Automated Testing

The test suite validates 7 core auth scenarios in isolated, bare shells:
- **Scenario 1**: Active Service Account (`GOOGLE_APPLICATION_CREDENTIALS`)
- **Scenario 2**: Active User ADC (`~/.config/gcloud/application_default_credentials.json`)
- **Scenario 3**: `gcloud` installed, but unauthenticated (generates onboarding plan)
- **Scenario 4**: Bare system with zero `gcloud` or credentials (offline Tier 0 skills top-ranked)
- **Scenario 5**: User Opt-Out mode (strictly guarantees 0 Tier 2 items returned)
- **Scenario 6**: Fallback skills & Gemini API key detection
- **Scenario 7**: Persistent preferences storage & reload

```bash
python3 -m unittest discover -s tests -v
```

---

## 🌐 Canonical Hosting Plan

This `ai-catalog.json` is designed to be hosted at:
- `https://cloud.google.com/.well-known/ai-catalog.json`
- `https://developers.google.com/.well-known/ai-catalog.json`

Clients using `hf-discover` or any ARD v0.5 client can navigate directly:
```bash
hf discover navigate https://cloud.google.com "optimize bigquery"
```
