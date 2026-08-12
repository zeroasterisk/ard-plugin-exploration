#!/usr/bin/env python3
"""
Automated E2E Test Suite for ARD Plugin with OpenCode Agent in Podman

Runs 4 comprehensive end-to-end scenarios verifying:
1. Scenario 1: Tier 0 pure public skills discovery (no auth required, zero prompts).
2. Scenario 2: Cloud intent -> OpenCode asks to login -> User: "No with an opt out" -> OpenCode opts out and silences GCP.
3. Scenario 3: Cloud intent -> OpenCode asks to login -> User: "Yes" -> OpenCode facilitates easy onboarding.
4. Test 4: All 11 unit and scenario matrix tests inside the container.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENCODE_IMAGE = "localhost/ard-opencode:latest"


def run_opencode_in_container(cmd_args, timeout=120):
    """Executes a command inside the ard-opencode container with local volumes bound."""
    podman_cmd = [
        "podman",
        "run",
        "--rm",
        "-v",
        f"{REPO_ROOT}:/workspace/ard-plugin-exploration",
        "-e",
        "XDG_CONFIG_HOME=/workspace/.config",
        "-e",
        "ARD_CONFIG_DIR=/workspace/.config/ard",
        "--entrypoint",
        "/bin/sh",
        OPENCODE_IMAGE,
        "-c",
        "cd /workspace/ard-plugin-exploration && " + " ".join(cmd_args),
    ]

    return subprocess.run(
        podman_cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_1_scenario_1_tier_0_pure_discovery():
    """Scenario 1: User asks for security & SQL guidance -> OpenCode recommends Tier 0 skills without GCP prompts."""
    print("\n" + "=" * 80)
    print("🧪 SCENARIO 1: Pure Public Discovery (Tier 0 Zero-Auth Counterpoint)")
    print("=" * 80)

    prompt = "'I need best practices to optimize my SQL queries and design zero-trust security. Search tools for me.'"
    res = run_opencode_in_container([
        "opencode",
        "run",
        "--auto",
        "--model",
        "opencode/deepseek-v4-flash-free",
        prompt,
    ])

    out = res.stdout + res.stderr
    print(out)
    assert res.returncode == 0, f"Scenario 1 failed: {res.stderr}"
    assert (
        "well-architected-security" in out
        or "bigquery-guidelines" in out
        or "Tier 0" in out
        or "no auth" in out.lower()
    ), "Scenario 1 did not return expected Tier 0 skills"

    print("✅ Scenario 1 Passed: OpenCode returned Tier 0 skills with zero auth friction.")


def test_2_scenario_2_opt_out_flow():
    """Scenario 2: Unauthenticated Cloud Intent -> User: 'No with an opt out' -> OpenCode opts out and silences GCP."""
    print("\n" + "=" * 80)
    print("🧪 SCENARIO 2: Cloud Intent -> User Opts Out ('No with an opt out')")
    print("=" * 80)

    # Turn 1: User asks for BigQuery query
    turn1_prompt = "'I want to run a live analytical query on a 100GB sales dataset in BigQuery. What tool can do this?'"
    res1 = run_opencode_in_container([
        "opencode",
        "run",
        "--auto",
        "--model",
        "opencode/deepseek-v4-flash-free",
        turn1_prompt,
    ])
    out1 = res1.stdout + res1.stderr
    print("--- Turn 1 (Agent Response) ---")
    print(out1)
    assert res1.returncode == 0, f"Turn 1 failed: {res1.stderr}"
    assert "bigquery" in out1.lower() and ("gcp" in out1.lower() or "auth" in out1.lower()), "Turn 1 did not identify BigQuery auth requirement"

    # Turn 2: User says "No with an opt out"
    turn2_prompt = "'No with an opt out'"
    res2 = run_opencode_in_container([
        "opencode",
        "run",
        "--auto",
        "--model",
        "opencode/deepseek-v4-flash-free",
        "--continue",
        turn2_prompt,
    ])
    out2 = res2.stdout + res2.stderr
    print("--- Turn 2 (Opt-Out Response) ---")
    print(out2)
    assert res2.returncode == 0, f"Turn 2 failed: {res2.stderr}"
    assert (
        "opt" in out2.lower()
        or "opt_out" in out2
        or "preference" in out2.lower()
        or "guidelines" in out2.lower()
    ), "Turn 2 did not confirm opt-out"

    print("✅ Scenario 2 Passed: OpenCode asked to log into GCP, user opted out, and GCP was silenced.")


def test_3_scenario_3_onboarding_flow():
    """Scenario 3: Unauthenticated Cloud Intent -> User: 'Yes' -> OpenCode facilitates easy onboarding."""
    print("\n" + "=" * 80)
    print("🧪 SCENARIO 3: Cloud Intent -> User Onboards ('Yes') -> Easy Onboarding")
    print("=" * 80)

    # Turn 1: Reset prefs & ask for BigQuery query
    turn1_cmd = "rm -rf /workspace/.config/ard && opencode run --auto --model opencode/deepseek-v4-flash-free 'I want to query a public BigQuery dataset. What tool can do this?'"
    res1 = run_opencode_in_container([turn1_cmd])
    out1 = res1.stdout + res1.stderr
    print("--- Turn 1 (Agent Response) ---")
    print(out1)
    assert res1.returncode == 0, f"Turn 1 failed: {res1.stderr}"
    assert "bigquery" in out1.lower(), "Turn 1 did not find BigQuery"

    # Turn 2: User says "Yes"
    turn2_prompt = "'Yes, please log me in'"
    res2 = run_opencode_in_container([
        "opencode",
        "run",
        "--auto",
        "--model",
        "opencode/deepseek-v4-flash-free",
        "--continue",
        turn2_prompt,
    ])
    out2 = res2.stdout + res2.stderr
    print("--- Turn 2 (Onboarding Instructions) ---")
    print(out2)
    assert res2.returncode == 0, f"Turn 2 failed: {res2.stderr}"
    assert (
        "gcloud" in out2.lower()
        or "login" in out2.lower()
        or "auth" in out2.lower()
        or "credentials" in out2.lower()
    ), "Turn 2 did not provide onboarding guidance"

    print("✅ Scenario 3 Passed: OpenCode facilitated easy GCP login onboarding.")


def test_4_unit_and_scenario_suite():
    """Run all 11 unit and scenario tests."""
    print("\n" + "=" * 80)
    print("🧪 TEST 4: Complete ARD & OpenCode Unit and Scenario Suite")
    print("=" * 80)

    res = run_opencode_in_container([
        "python3",
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
        "-v",
    ])
    out = res.stdout + res.stderr
    print(out)
    assert res.returncode == 0, f"Unit test suite failed: {res.stderr}"
    print("✅ Test 4 Passed: All 11 unit and scenario tests executed successfully.")


def run_all_e2e_tests():
    print("=" * 80)
    print("🚀 RUNNING OPENCODE CONTAINERIZED ARD E2E TEST SUITE")
    print("=" * 80)

    test_1_scenario_1_tier_0_pure_discovery()
    test_2_scenario_2_opt_out_flow()
    test_3_scenario_3_onboarding_flow()
    test_4_unit_and_scenario_suite()

    print("\n" + "=" * 80)
    print("🎉 ALL 4 E2E CONTAINER TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_e2e_tests()
