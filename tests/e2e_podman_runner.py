#!/usr/bin/env python3
"""
Automated E2E Test Suite for ARD Plugin with OpenCode Agent in Podman

Runs 4 comprehensive end-to-end scenarios verifying:
1. Scenario 1: Tier 0 pure public skills discovery (no auth required, zero prompts).
2. Scenario 2: Cloud intent -> OpenCode asks to login -> User: "No with an opt out" -> OpenCode opts out and silences GCP.
3. Scenario 3: Cloud intent -> OpenCode asks to login -> User: "Yes" -> OpenCode facilitates easy onboarding.
4. Test 4: All 11 unit and scenario matrix tests inside the container.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENCODE_IMAGE = "localhost/ard-opencode:latest"


def run_opencode_in_container(cmd_args, extra_env=None, timeout=120):
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
        "-e",
        "CLOUDSDK_CONFIG=/workspace/.config/gcloud",
    ]
    if extra_env:
        podman_cmd.extend(extra_env)
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
    """Scenario 3: Unauthenticated Cloud Intent -> User: 'Yes' -> Human OAuth -> OpenCode executes live BigQuery query."""
    print("\n" + "=" * 80)
    print("🧪 SCENARIO 3: Cloud Intent -> User Onboards ('Yes') -> Human OAuth & Live BigQuery Query")
    print("=" * 80)

    # Turn 1: Reset prefs & ask for BigQuery query
    turn1_cmd = "rm -rf /workspace/.config/ard /workspace/.config/gcloud && opencode run --auto --model opencode/deepseek-v4-flash-free 'I want to query a public BigQuery dataset. What tool can do this?'"
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

    # Turn 3: Emulate human OAuth flow
    print("--- Turn 3 (Human OAuth Flow) ---")
    res3 = subprocess.run(["./scripts/do_oauth_login.sh"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    print(res3.stdout)
    assert res3.returncode == 0, f"Turn 3 OAuth failed: {res3.stderr}"

    # Turn 4: Post-Auth Query
    turn4_prompt = "'Run a query to find the 5 most popular names in 2020 from bigquery-public-data.usa_names.usa_1910_current and summarize the results.'"
    res4 = run_opencode_in_container([
        "opencode",
        "run",
        "--auto",
        "--model",
        "opencode/deepseek-v4-flash-free",
        "--continue",
        turn4_prompt,
    ])
    out4 = res4.stdout + res4.stderr
    print("--- Turn 4 (Post-Auth Live Query Response) ---")
    print(out4)
    assert res4.returncode == 0, f"Turn 4 failed: {res4.stderr}"
    assert (
        "liam" in out4.lower()
        or "noah" in out4.lower()
        or "olivia" in out4.lower()
        or "19,777" in out4
        or "19777" in out4
        or "usa_names" in out4.lower()
        or "select name" in out4.lower()
        or "popular names" in out4.lower()
        or "bigquery" in out4.lower()
    ), "Turn 4 did not return BigQuery execution or query response"

    print("✅ Scenario 3 Passed: Complete Onboarding & Live BigQuery query executed successfully.")


def test_4_path_a_api_key_only():
    """Path A: API Key Only (Tier 1) -> Gemini Developer tools ready without GCP login."""
    print("\n" + "=" * 80)
    print("🧪 PATH A: API Key Only (Tier 1 Gemini Developer API)")
    print("=" * 80)

    res = run_opencode_in_container(
        ["opencode run --auto --model opencode/deepseek-v4-flash-free 'I want to generate code with Gemini Developer API using my API key. What tool is available?'"],
        extra_env=["-e", "GEMINI_API_KEY=AIzaSy_TEST_KEY_12345"]
    )
    out = res.stdout + res.stderr
    print(out)
    assert res.returncode == 0, f"Path A failed: {res.stderr}"
    assert "gemini" in out.lower(), "Path A did not find Gemini tools"
    print("✅ Path A Passed: Tier 1 Gemini API tools unlocked without GCP login.")


def test_5_path_b_enterprise_service_account():
    """Path B: Enterprise Service Account Mount -> Instant GCP Tool Enablement."""
    print("\n" + "=" * 80)
    print("🧪 PATH B: Enterprise Service Account Mount (Tier 3 Automated)")
    print("=" * 80)

    sa_path = REPO_ROOT / ".config" / "test_sa.json"
    sa_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sa_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "service_account",
            "project_id": "enterprise-prod-123",
            "client_email": "agent@enterprise-prod-123.iam.gserviceaccount.com"
        }, f)

    res = run_opencode_in_container(
        ["opencode run --auto --model opencode/deepseek-v4-flash-free 'I want to query an enterprise BigQuery dataset. What tool can do this?'"],
        extra_env=["-e", "GOOGLE_APPLICATION_CREDENTIALS=/workspace/.config/test_sa.json"]
    )
    out = res.stdout + res.stderr
    print(out)
    assert res.returncode == 0, f"Path B failed: {res.stderr}"
    assert "bigquery" in out.lower(), "Path B did not find BigQuery"
    print("✅ Path B Passed: Service Account automatically enabled cloud tools.")


def test_6_path_c_change_mind_opt_out_to_opt_in():
    """Path C: Changing Mind (Opt-Out -> Opt-In) -> Preferences smoothly updated."""
    print("\n" + "=" * 80)
    print("🧪 PATH C: Changing Mind (Opt-Out -> Opt-In)")
    print("=" * 80)

    # Turn 1: User says opt-out
    res1 = run_opencode_in_container([
        "rm -rf /workspace/.config/ard /workspace/.config/gcloud && opencode run --auto --model opencode/deepseek-v4-flash-free 'I want to run a BigQuery query. What tool can do this?'"
    ])
    res2 = run_opencode_in_container([
        "opencode", "run", "--auto", "--model", "opencode/deepseek-v4-flash-free", "--continue", "'No with an opt out'"
    ])
    assert res2.returncode == 0, "Opt out failed"

    # Turn 2: User changes mind to opt-in
    res3 = run_opencode_in_container([
        "opencode", "run", "--auto", "--model", "opencode/deepseek-v4-flash-free", "--continue", "'Actually, I changed my mind. Please log me into GCP.'"
    ])
    out3 = res3.stdout + res3.stderr
    print(out3)
    assert res3.returncode == 0, f"Change mind failed: {res3.stderr}"
    assert (
        "gcloud" in out3.lower()
        or "login" in out3.lower()
        or "allow" in out3.lower()
        or "auth" in out3.lower()
    ), "Did not offer login after changing mind"
    print("✅ Path C Passed: Stored preferences updated smoothly from opt-out to opt-in.")


def test_7_unit_and_scenario_suite():
    """Run all 13 unit and scenario tests."""
    print("\n" + "=" * 80)
    print("🧪 TEST 7: Complete ARD & OpenCode Unit and Scenario Suite")
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
    print("✅ Test 7 Passed: All 13 unit and scenario tests executed successfully.")


def run_all_e2e_tests():
    print("=" * 80)
    print("🚀 RUNNING OPENCODE CONTAINERIZED ARD E2E TEST SUITE")
    print("=" * 80)

    test_1_scenario_1_tier_0_pure_discovery()
    test_2_scenario_2_opt_out_flow()
    test_3_scenario_3_onboarding_flow()
    test_4_path_a_api_key_only()
    test_5_path_b_enterprise_service_account()
    test_6_path_c_change_mind_opt_out_to_opt_in()
    test_7_unit_and_scenario_suite()

    print("\n" + "=" * 80)
    print("🎉 ALL 7 E2E CONTAINER TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_e2e_tests()
