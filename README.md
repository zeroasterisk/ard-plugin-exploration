# Agent Resource Discovery (ARD v0.5) • Google Ecosystem Exploration

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-blue)](https://zeroasterisk.github.io/ard-plugin-exploration/)
[![ARD Spec](https://img.shields.io/badge/ARD_Spec-v0.5-indigo)](https://agenticresourcediscovery.org)
[![Podman E2E](https://img.shields.io/badge/OpenCode_E2E-4%2F4_Passed-emerald)](./tests/e2e_podman_runner.py)

Autonomous AI coding agent exploration (**OpenCode**) discovering and using **Google Cloud Managed MCP Servers** and **Google Agent Skills** via a canonical ARD v0.5 manifest (`ai-catalog.json`).

---

## 🎯 The 3 Core Real-World Scenarios

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Scenario 1: Pure Public Discovery (Tier 0 Counterpoint)                                │
│ • User asks for security design & SQL optimization.                                    │
│ • OpenCode autonomously calls ard_search -> Returns Tier 0 skills.                     │
│ • Immediate standalone value with zero auth, zero credentials, and no GCP prompts.    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Scenario 2: Unauthenticated Cloud Intent -> User Opts Out ("No with an opt out")       │
│ • User asks for BigQuery 100GB dataset query.                                          │
│ • OpenCode: "BigQuery requires GCP auth. Do you want to login to GCP?"                │
│ • User: "No with an opt out"                                                           │
│ • OpenCode calls ard_set_preference(mode="opt_out") -> Silences GCP tools permanently. │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Scenario 3: Unauthenticated Cloud Intent -> User Onboards ("Yes")                      │
│ • User asks for BigQuery dataset query.                                                │
│ • OpenCode: "BigQuery requires GCP auth. Do you want to login to GCP?"                │
│ • User: "Yes"                                                                          │
│ • OpenCode guides easy onboarding (gcloud auth login) & unlocks tool without nagging.  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎥 Watch the Real OpenCode Agent Execution

🔗 **Live Web Player:** **[https://zeroasterisk.github.io/ard-plugin-exploration/](https://zeroasterisk.github.io/ard-plugin-exploration/)**

```bash
# Play locally via asciinema:
asciinema play demo.cast

# Or open in browser:
google-chrome index.html
```

---

## 🌐 Open ARD Ecosystem & Interoperability

This catalog complies with the **[Agent Resource Discovery (ARD v0.5)](https://agenticresourcediscovery.org)** open specification (`urn:ai:google.com:...`). It is compatible with all ARD implementations:

- **Our OpenCode / Antigravity MCP Plugin** (`src/ard_mcp_server.py` & `opencode.json`)
- **[Mindpower Agent Finder](https://mindpower.github.io/agent-finder/)** (Client-side directory indexing)
- **[Hugging Face Discover (`hf-discover`) & EvalState](https://evalstate-hf-agentfinder.hf.space/docs#/)**
- Any client discovering `/.well-known/ai-catalog.json` (see [ARD Reference Implementations](https://agenticresourcediscovery.org/ref_implementations/)).

---

## 🧪 Automated Testing

```bash
# Run real OpenCode AI agent E2E test runner in Podman container:
python3 tests/e2e_podman_runner.py

# Run unit and multi-turn conversational scenario suite:
python3 -m unittest discover -s tests -v
```

---

## 📁 Repository Layout

```text
ard-plugin-exploration/
├── ai-catalog.json                # Canonical ARD v0.5 catalog (27+ tools/skills)
├── opencode.json                  # OpenCode MCP integration config
├── Dockerfile                     # OpenCode container based on ghcr.io/anomalyco/opencode
├── demo.cast                      # Genuine live OpenCode AI agent PTY recording
├── index.html                     # Interactive web player for GitHub Pages
├── scripts/
│   ├── banner.sh                  # Fast scenario header rendering shortcuts
│   └── record_opencode_real_session.py # Real PTY recorder driving OpenCode binary
├── src/
│   ├── ard_resolver.py            # Zero-dependency Python search & auth engine
│   └── ard_mcp_server.py          # JSON-RPC stdio MCP server for OpenCode
└── tests/
    ├── test_ard_resolver.py       # Unit tests (auth scenarios & URN validation)
    ├── test_opencode_scenarios.py # Multi-turn conversational flow tests
    └── e2e_podman_runner.py       # Real OpenCode agent E2E test runner
```
