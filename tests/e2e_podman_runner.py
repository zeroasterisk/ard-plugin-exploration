#!/usr/bin/env python3
"""
E2E Podman Experiment Runner for ARD Google Ecosystem Discovery

Runs real isolated container experiments using Podman:
- Experiment 1: The Pure Open-Source Developer (Zero GCP, Zero Auth, Offline Skills)
- Experiment 2: The Strict Opt-Out Developer (Explicit Anti-Cloud Preference)
- Experiment 3: The Progressive Onboarding User (Live Cloud Intent without credentials)
- Experiment 4: The Authenticated Enterprise Developer (Active Service Account Key)
- Experiment 5: The Free AI Developer (Gemini API Key, No GCP Account)
- Experiment 6: Read-Only Filesystem / Containerized Agent (Stateless in-memory preference handling)
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTAINER_IMAGE = "docker.io/library/python:3.13-slim"


def run_container_command(
    cmd_args: List[str],
    env: Optional[Dict[str, str]] = None,
    volumes: Optional[Dict[str, str]] = None,
    read_only_fs: bool = False,
) -> subprocess.CompletedProcess:
    """Executes a command inside an isolated Podman container."""
    podman_cmd = ["podman", "run", "--rm"]

    if read_only_fs:
        podman_cmd.append("--read-only")

    # Mount the repo root into /app (read-only)
    podman_cmd.extend(["-v", f"{REPO_ROOT}:/app:ro"])

    if volumes:
        for host_path, container_path in volumes.items():
            podman_cmd.extend(["-v", f"{host_path}:{container_path}"])

    if env:
        for k, v in env.items():
            podman_cmd.extend(["-e", f"{k}={v}"])

    podman_cmd.extend([CONTAINER_IMAGE, "python3", "/app/src/ard_resolver.py"])
    podman_cmd.extend(cmd_args)

    return subprocess.run(
        podman_cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_experiment_1_pure_open_source_developer():
    """
    Experiment 1: Zero GCP, Zero Auth, Offline Local Developer.
    Goal: Verify that asking for architecture and SQL optimization returns Tier 0 skills
    without any annoying prompts or GCP signup nags.
    """
    print("\n" + "=" * 80)
    print("🧪 EXPERIMENT 1: Pure Open Source Developer (Zero Auth / Offline)")
    print("=" * 80)

    # Empty env, no keys, no gcloud
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin"}
    res = run_container_command(
        ["search", "how to design zero trust security and optimize sql", "--json"],
        env=env,
    )

    assert res.returncode == 0, f"Container execution failed: {res.stderr}"
    data = json.loads(res.stdout)

    print(f"• Returned {len(data)} results in clean container.")

    # Top items must be Tier 0 and marked ready
    top_item = data[0]
    print(f"• Top Result: {top_item['displayName']} (Tier {top_item['tier']}) -> Status: {top_item['status']}")

    assert top_item["tier"] == 0, f"Expected Tier 0 top result, got Tier {top_item['tier']}"
    assert top_item["auth_ready"] is True, "Tier 0 items must be auth_ready=True"
    assert top_item["status"] == "ready", "Tier 0 items must have status=ready"

    # Verify no GCP onboarding nagging on Tier 0 results
    for item in data:
        if item["tier"] == 0:
            assert item["onboarding"] is None, "Tier 0 skills must not contain onboarding messages"

    print("✅ Experiment 1 Passed: Zero-auth user received immediate offline skills without nags.")


def test_experiment_2_strict_opt_out_developer():
    """
    Experiment 2: Strict Opt-Out Developer.
    Goal: Verify that an explicit opt-out preference strictly filters out all Tier >= 3 cloud tools,
    even when the user query explicitly mentions cloud services like BigQuery.
    """
    print("\n" + "=" * 80)
    print("🧪 EXPERIMENT 2: Strict Opt-Out Developer (Explicit Anti-Cloud Preference)")
    print("=" * 80)

    # Injected stateless opt-out preference via env
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "ARD_PREFERENCES_JSON": json.dumps({"gcp_mode": "opt_out"}),
    }
    res = run_container_command(
        ["search", "bigquery analytical database query", "--json"],
        env=env,
    )

    assert res.returncode == 0, f"Container execution failed: {res.stderr}"
    data = json.loads(res.stdout)

    print(f"• Query: 'bigquery analytical database query' (Opt-Out Active)")
    print(f"• Results returned: {len(data)}")

    identifiers = [r["identifier"] for r in data]
    print(f"• Discovered IDs: {identifiers}")

    # Assert BigQuery guideline skill (Tier 0) is present
    assert any("skills:bigquery-guidelines" in i for i in identifiers), "Tier 0 BigQuery Skill should be present"

    # Assert BigQuery MCP server (Tier 3) is strictly absent
    assert not any("mcp:bigquery" in i for i in identifiers), "Tier 3 BigQuery MCP must be filtered out"

    # Assert zero results have tier >= 3
    for r in data:
        assert r["tier"] < 3, f"Item {r['identifier']} has tier {r['tier']}, expected < 3"

    print("✅ Experiment 2 Passed: Strict opt-out guaranteed 0 GCP account items returned.")


def test_experiment_3_progressive_onboarding_user():
    """
    Experiment 3: Progressive Onboarding User.
    Goal: When an unauthenticated user specifically asks for live cloud execution,
    the resolver returns the tool with clear non-intrusive onboarding info and an offline fallback.
    """
    print("\n" + "=" * 80)
    print("🧪 EXPERIMENT 3: Progressive Onboarding (Cloud intent without auth)")
    print("=" * 80)

    env = {"PATH": "/usr/local/bin:/usr/bin:/bin"}
    res = run_container_command(
        ["search", "query bigquery dataset", "--json"],
        env=env,
    )

    assert res.returncode == 0, f"Container execution failed: {res.stderr}"
    data = json.loads(res.stdout)

    bq_mcp = next((r for r in data if "mcp:bigquery" in r["identifier"]), None)
    assert bq_mcp is not None, "BigQuery MCP should be found"

    print(f"• BigQuery MCP Status: {bq_mcp['status']}")
    print(f"• Action Suggestion:   {bq_mcp['action_suggestion']}")
    print(f"• Fallback Skill:      {bq_mcp['fallback_skill']}")
    print(f"• Onboarding Message:  {bq_mcp['onboarding']['message']}")
    print(f"• Free Tier:           {bq_mcp['onboarding']['freeTier']} ({bq_mcp['onboarding']['freeTierDetails']})")

    assert bq_mcp["auth_ready"] is False
    assert bq_mcp["status"] == "needs_onboarding"
    assert "gcloud auth application-default login" in bq_mcp["onboarding"]["command"]
    assert bq_mcp["fallback_skill"] == "urn:ai:google.com:skills:bigquery-guidelines"

    print("✅ Experiment 3 Passed: Non-intrusive onboarding plan and fallback provided.")


def test_experiment_4_authenticated_enterprise_developer():
    """
    Experiment 4: Enterprise Developer with Active Service Account.
    Goal: When a service account key is mounted, Tier 3 tools are immediately marked [READY].
    """
    print("\n" + "=" * 80)
    print("🧪 EXPERIMENT 4: Authenticated Enterprise Developer (Service Account Active)")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temp_host_dir:
        sa_key_path = Path(temp_host_dir) / "sa_key.json"
        with open(sa_key_path, "w", encoding="utf-8") as f:
            json.dump({
                "type": "service_account",
                "project_id": "enterprise-prod-987",
                "private_key_id": "mock-key-id",
                "client_email": "agent@enterprise-prod-987.iam.gserviceaccount.com"
            }, f)

        volumes = {str(temp_host_dir): "/secrets"}
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "GOOGLE_APPLICATION_CREDENTIALS": "/secrets/sa_key.json",
        }

        res = run_container_command(
            ["search", "inspect cloud storage bucket and run bigquery", "--json"],
            env=env,
            volumes=volumes,
        )

        assert res.returncode == 0, f"Container execution failed: {res.stderr}"
        data = json.loads(res.stdout)

        bq_mcp = next((r for r in data if "mcp:bigquery" in r["identifier"]), None)
        gcs_mcp = next((r for r in data if "mcp:cloud-storage" in r["identifier"]), None)

        assert bq_mcp is not None and gcs_mcp is not None
        print(f"• BigQuery MCP Auth Ready:      {bq_mcp['auth_ready']} (Status: {bq_mcp['status']})")
        print(f"• Cloud Storage MCP Auth Ready: {gcs_mcp['auth_ready']} (Status: {gcs_mcp['status']})")

        assert bq_mcp["auth_ready"] is True
        assert bq_mcp["status"] == "ready"
        assert gcs_mcp["auth_ready"] is True
        assert gcs_mcp["status"] == "ready"

    print("✅ Experiment 4 Passed: Authenticated environment marked cloud tools as ready with zero prompts.")


def test_experiment_5_free_gemini_api_developer():
    """
    Experiment 5: Free AI Developer (Gemini API key active, zero GCP account).
    Goal: Verify Tier 1 Gemini skills are marked [READY] while Tier 3 remain unauthenticated.
    """
    print("\n" + "=" * 80)
    print("🧪 EXPERIMENT 5: Free AI Developer (Gemini API Key, No GCP Account)")
    print("=" * 80)

    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "GEMINI_API_KEY": "AIzaSyMockKeyForGeminiStudio123",
    }
    res = run_container_command(
        ["search", "gemini tool calling structured outputs", "--json"],
        env=env,
    )

    assert res.returncode == 0, f"Container execution failed: {res.stderr}"
    data = json.loads(res.stdout)

    gemini_skill = next((r for r in data if "skills:gemini-api-patterns" in r["identifier"]), None)
    assert gemini_skill is not None
    print(f"• Gemini Skill: {gemini_skill['displayName']} -> Status: {gemini_skill['status']} (Auth Ready: {gemini_skill['auth_ready']})")

    assert gemini_skill["tier"] == 1
    assert gemini_skill["auth_ready"] is True
    assert gemini_skill["status"] == "ready"

    print("✅ Experiment 5 Passed: Gemini API key recognized; Tier 1 tool ready without GCP account.")


def test_experiment_6_stateless_container_read_only_fs():
    """
    Experiment 6: Stateless / Read-Only Container (e.g. Cloud Run / strict sandbox).
    Goal: Verify resolver operates smoothly without crashing on read-only filesystems.
    """
    print("\n" + "=" * 80)
    print("🧪 EXPERIMENT 6: Stateless Read-Only Container Environment")
    print("=" * 80)

    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "ARD_PREFERENCES_JSON": json.dumps({"gcp_mode": "auto"}),
    }
    res = run_container_command(
        ["search", "cloud run container microservice", "--json"],
        env=env,
        read_only_fs=True,
    )

    assert res.returncode == 0, f"Container execution failed on read-only FS: {res.stderr}"
    data = json.loads(res.stdout)
    assert len(data) > 0

    print(f"• Returned {len(data)} results on strict --read-only container filesystem.")
    print("✅ Experiment 6 Passed: Stateless read-only sandbox executed flawlessly.")


def main():
    print("=" * 80)
    print("🚀 LAUNCHING PODMAN CONTAINER E2E EXPERIMENT SUITE")
    print(f"• Container Runtime: podman")
    print(f"• Image:             {CONTAINER_IMAGE}")
    print(f"• Target Repo:       {REPO_ROOT}")
    print("=" * 80)

    tests = [
        test_experiment_1_pure_open_source_developer,
        test_experiment_2_strict_opt_out_developer,
        test_experiment_3_progressive_onboarding_user,
        test_experiment_4_authenticated_enterprise_developer,
        test_experiment_5_free_gemini_api_developer,
        test_experiment_6_stateless_container_read_only_fs,
    ]

    passed = 0
    failed = 0

    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:
            print(f"\n❌ FAILED: {t.__name__}: {exc}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"📊 E2E PODMAN EXPERIMENT SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
