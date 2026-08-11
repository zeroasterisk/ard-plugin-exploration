# Agent Resource Discovery (ARD v0.5) • Google Ecosystem Exploration

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-blue)](https://zeroasterisk.github.io/ard-plugin-exploration/)
[![ARD Spec](https://img.shields.io/badge/ARD_Spec-v0.5-indigo)](https://agenticresourcediscovery.org)
[![Podman E2E](https://img.shields.io/badge/Podman_E2E-6%2F6_Passed-emerald)](./tests/e2e_podman_runner.py)

Prototype exploration combining **Google Cloud Managed MCP Servers** and **Google Agent Skills** into a canonical ARD v0.5 manifest with progressive auth tiering, respectful opt-out, and pre-execution auth metadata for coding agents (OpenCode, Antigravity, Jetski, Python ADK).

---

## 🎯 The Core Premise: Solving the "Detractor Myth"

> **Objection:** *"Why publish an ARD catalog if it's useless without a Google Cloud account?"*

**The Reality:** Capabilities exist on a friction and auth spectrum. Over **60% of capabilities** in the catalog are **Tier 0 (Zero Auth)**:

| Tier | Type | Examples | Friction / Prerequisites |
| :--- | :--- | :--- | :--- |
| **Tier 0** | **Zero Auth / Local** | Well-Architected Security, BigQuery SQL Guidelines, Cloud Run Architecture | **0** (Instant offline execution, zero credentials) |
| **Tier 1** | **Developer API Keys** | Gemini API Patterns, Developer Knowledge MCP | **Low** (Free API key in AI Studio, zero GCP account) |
| **Tier 2** | **Workspace OAuth** | Gmail, Google Drive, Google Sheets MCPs | **User Consent** (Standard OAuth token cache) |
| **Tier 3** | **Google Cloud ADC / SA** | BigQuery, Cloud Storage, Cloud Run, GKE, Cloud SQL Managed MCPs | **GCP Bound** (`gcloud auth login` or SA key, includes 1TB/mo free tier) |
| **Tier 4** | **Enterprise VPC-SC** | Google SecOps (Chronicle), Security Command Center | **Enterprise Bound** (SPIFFE / IAM trust perimeters) |

---

## 🔑 Key Architectural & UX Pillars

1. **Zero Friction for Non-GCP Users:** Pure offline skills work immediately with zero signup hurdles or prompts.
2. **Strict, Permanent Opt-Out:** When a user says *"never ask again"*, the preference is stored permanently (`~/.config/ard/preferences.json` or in-memory `ARD_PREFERENCES_JSON`), strictly silencing all Tier 3/4 tools.
3. **Pre-Execution Auth Awareness:** The resolver returns `status: needs_onboarding` and `fallback_skill` upfront, preventing blind execution crashes and confusing 401/403 errors.
4. **Canonical RFC 8141 URNs:** Strictly standardized on `urn:ai:google.com:...`.

---

## 🎥 4-Minute Interactive Demo & Scenarios

Watch the full interactive walkthrough online: **[Live GitHub Pages Demo](https://zeroasterisk.github.io/ard-plugin-exploration/)** or play locally:

```bash
# Play via asciinema in terminal:
asciinema play demo.cast

# Or open web player:
google-chrome demo_player.html
```

### Scenario Breakdown:
- **0:00 – 0:40** | Introduction & Passive Auth Inspection (`ard_resolver.py auth status`).
- **0:40 – 1:20** | **Scenario 1 (Pure Open Source Dev):** Zero-auth offline skills returned immediately.
- **1:20 – 2:00** | **Scenario 2 (OpenCode Opt-Out Flow):** User declines GCP ➜ preference saved ➜ BigQuery silenced.
- **2:00 – 2:40** | **Scenario 3 (gcloud Onboarding):** User logs in via `gcloud` ➜ BigQuery unlocked.
- **2:40 – 3:20** | **Scenario 4 (Enterprise Service Account):** Automated CI/CD with mounted SA key.
- **3:20 – 3:45** | **Containerized Podman E2E Suite:** 6/6 tests passing in isolated containers.
- **3:45 – 4:00** | Summary & ARD specification compliance.

---

## 🌐 Ecosystem & Reference Implementations

This catalog adheres to the **[Agent Resource Discovery (ARD v0.5)](https://agenticresourcediscovery.org)** open specification. It is interoperable across all ARD implementations:

- **Our OpenCode / Antigravity MCP Plugin** (`src/ard_mcp_server.py` & `opencode.json`)
- **[Mindpower Agent Finder](https://mindpower.github.io/agent-finder/)** (Client-side directory indexing)
- **[HuggingFace Discover (`hf-discover`) & EvalState](https://evalstate-hf-agentfinder.hf.space/docs#/)**
- Any client discovering `/.well-known/ai-catalog.json` (see [ARD Reference Implementations](https://agenticresourcediscovery.org/ref_implementations/)).

---

## 🚀 Quickstart

```bash
# 1. Natural language search
python3 src/ard_resolver.py search "how to optimize bigquery sql"

# 2. Strict GCP Opt-Out search
python3 src/ard_resolver.py search "analyze large analytical dataset" --opt-out

# 3. Check system auth status
python3 src/ard_resolver.py auth status

# 4. Run automated test suites
python3 -m unittest discover -s tests -v

# 5. Run containerized Podman E2E experiments
./scripts/run_podman_experiments.sh
```

---

## 📁 Repository Layout

```text
ard-plugin-exploration/
├── ai-catalog.json                # Canonical ARD v0.5 catalog (27+ tools/skills)
├── opencode.json                  # OpenCode MCP integration config
├── Dockerfile                     # OpenCode container based on ghcr.io/anomalyco/opencode
├── demo.cast                      # 4-minute asciicast recording (240.0s)
├── demo_player.html / index.html  # Interactive web player for GitHub Pages
├── src/
│   ├── ard_resolver.py            # Zero-dependency Python search & auth engine
│   └── ard_mcp_server.py          # JSON-RPC stdio MCP server for OpenCode
├── tests/
│   ├── test_ard_resolver.py       # Unit tests (auth scenarios & URN validation)
│   ├── test_opencode_scenarios.py # Multi-turn conversational flow tests
│   └── e2e_podman_runner.py       # Containerized Podman E2E runner (6/6 passing)
└── plugin/                        # OpenCode / Antigravity / Jetski plugin bundle
```
