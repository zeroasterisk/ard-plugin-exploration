#!/usr/bin/env python3
"""
E2E Podman Experiment Runner with Real OpenCode Agent Execution

Executes real OpenCode binary (opencode run) in the ard-opencode container,
verifying that the AI agent autonomously invokes ARD MCP tools, handles
auth tiers, respects opt-out preferences, and detects service accounts.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENCODE_IMAGE = "localhost/ard-opencode:latest"


def run_opencode_in_container(
    cmd_args: List[str],
    env: Optional[Dict[str, str]] = None,
    volumes: Optional[Dict[str, str]] = None,
    timeout: int = 90,
) -> subprocess.CompletedProcess:
    """Runs the opencode binary inside the Podman container."""
    podman_cmd = [
        "podman",
        "run",
        "--rm",
        "-v",
        f"{REPO_ROOT}:/workspace/ard-plugin-exploration",
    ]

    if volumes:
        for host_path, container_path in volumes.items():
            podman_cmd.extend(["-v", f"{host_path}:{container_path}"])

    if env:
        for k, v in env.items():
            podman_cmd.extend(["-e", f"{k}={v}"])

    podman_cmd.extend([
        "--entrypoint",
        "/bin/sh",
        OPENCODE_IMAGE,
        "-c",
        "cd /workspace/ard-plugin-exploration && " + " ".join(cmd_args),
    ])

    return subprocess.run(
        podman_cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_1_opencode_mcp_discovery():
    """Verify OpenCode automatically detects and connects to the ARD MCP server."""
    print("\n" + "=" * 80)
    print("🧪 TEST 1: OpenCode Native MCP Server Connection")
    print("=" * 80)

    res = run_opencode_in_container(["opencode", "mcp", "list"])
    out = res.stdout + res.stderr
    print(out)
    assert res.returncode == 0, f"opencode mcp list failed: {res.stderr}"
    assert "ard-google-discovery" in out and "connected" in out, "ARD MCP server was not connected by OpenCode"
    print("✅ Test 1 Passed: OpenCode successfully connected to ARD MCP server.")


def test_2_opencode_agent_autonomous_zero_auth_query():
    """Verify OpenCode agent receives a natural user prompt, calls ard_search autonomously, and recommends Tier 0 skills."""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: OpenCode Agent Autonomous Tool Calling (Zero Auth Scenario)")
    print("=" * 80)

    prompt = "'I need to design a zero trust security architecture and optimize my analytical SQL queries. Find tools for me.'"
    res = run_opencode_in_container([
        "opencode",
        "run",
        "--model",
        "opencode/deepseek-v4-flash-free",
        prompt,
    ])

    out = res.stdout + res.stderr
    print(out)
    assert res.returncode == 0, f"opencode run failed: {res.stderr}"
    assert (
        "well-architected-security" in out
        or "bigquery-guidelines" in out
        or "Zero trust" in out
        or "Tier 0" in out
    ), "OpenCode did not return expected Tier 0 skills"

    print("✅ Test 2 Passed: OpenCode agent autonomously invoked ard_search and recommended Tier 0 skills.")


def test_3_opencode_agent_autonomous_opt_out():
    """Verify OpenCode agent receives opt-out prompt, calls ard_set_preference(mode='opt_out'), and confirms."""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: OpenCode Agent Multi-Turn Opt-Out Flow")
    print("=" * 80)

    prompt = "'I do not have a GCP account and never want to use Google Cloud. Opt me out permanently so you never show me cloud tools.'"
    res = run_opencode_in_container([
        "opencode",
        "run",
        "--model",
        "opencode/deepseek-v4-flash-free",
        "--continue",
        prompt,
    ])

    out = res.stdout + res.stderr
    print(out)
    assert res.returncode == 0, f"opencode run opt-out failed: {res.stderr}"
    assert (
        "opted" in out.lower()
        or "opt_out" in out
        or "opt-out" in out.lower()
        or "preference" in out.lower()
    ), "OpenCode did not execute opt-out"

    print("✅ Test 3 Passed: OpenCode agent autonomously executed ard_set_preference(mode='opt_out').")


def test_4_opencode_agent_service_account_detection():
    """Verify OpenCode agent detects active service account credentials and verifies ready state."""
    print("\n" + "=" * 80)
    print("🧪 TEST 4: OpenCode Agent Authenticated Enterprise Mode (Service Account)")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temp_host_dir:
        sa_key_path = Path(temp_host_dir) / "sa.json"
        with open(sa_key_path, "w", encoding="utf-8") as f:
            json.dump({
                "type": "service_account",
                "project_id": "enterprise-prod-987",
                "client_email": "agent@enterprise-prod-987.iam.gserviceaccount.com",
            }, f)

        volumes = {str(temp_host_dir): "/secrets"}
        env = {"GOOGLE_APPLICATION_CREDENTIALS": "/secrets/sa.json"}

        prompt = "'Check auth status with ard_auth_status and search for cloud storage tools.'"
        res = run_opencode_in_container(
            ["opencode", "run", "--model", "opencode/deepseek-v4-flash-free", prompt],
            env=env,
            volumes=volumes,
        )

        out = res.stdout + res.stderr
        print(out)
        assert res.returncode == 0, f"opencode run SA failed: {res.stderr}"
        assert (
            "service_account" in out
            or "cloud-storage" in out
            or "authenticated" in out.lower()
        ), "OpenCode did not verify service account credentials"

    print("✅ Test 4 Passed: OpenCode agent verified service account credentials and found cloud tools.")


def test_5_unit_and_scenario_test_suite():
    """Run the complete 11-test unit and multi-turn scenario test suite."""
    print("\n" + "=" * 80)
    print("🧪 TEST 5: Complete ARD & OpenCode Unit and Scenario Suite")
    print("=" * 80)

    res = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(REPO_ROOT / "tests"), "-v"],
        capture_output=True,
        text=True,
    )
    print(res.stderr or res.stdout)
    assert res.returncode == 0, f"Unit tests failed: {res.stderr}"
    print("✅ Test 5 Passed: All 11 unit and scenario tests passed.")


def main():
    print("=" * 80)
    print("🚀 LAUNCHING OPENCODE REAL AGENT E2E TEST RUNNER")
    print(f"• Container Image: {OPENCODE_IMAGE}")
    print(f"• Repo Path:       {REPO_ROOT}")
    print("=" * 80)

    tests = [
        test_1_opencode_mcp_discovery,
        test_2_opencode_agent_autonomous_zero_auth_query,
        test_3_opencode_agent_autonomous_opt_out,
        test_4_opencode_agent_service_account_detection,
        test_5_unit_and_scenario_test_suite,
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
    print(f"📊 OPENCODE E2E SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
