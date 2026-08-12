#!/usr/bin/env python3
"""
Automated Test Suite for OpenCode ARD Discovery Scenarios

Simulates the 3 real-world multi-turn conversational flows with OpenCode:
- Scenario A (Opt-Out): User asks for analytics -> BQ needs onboarding -> User opts out -> Prefs saved -> Re-search strictly excludes BQ -> Offline skill used.
- Scenario B (gcloud Onboarding): User asks for analytics -> BQ needs onboarding -> User adds gcloud -> Runs auth -> Re-search marks BQ ready -> BQ succeeds.
- Scenario C (Service Account): User asks for analytics -> BQ needs onboarding -> User attaches SA key -> Re-search marks BQ ready -> BQ succeeds.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add src to path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from ard_mcp_server import ARDMCPServer
from ard_resolver import ARDCatalogResolver, AuthInspector, PreferencesManager


class TestOpenCodeDiscoveryScenarios(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.catalog_path = Path(__file__).resolve().parent.parent / "ai-catalog.json"
        self.prefs_dir = Path(self.test_dir) / "prefs"
        self.prefs_manager = PreferencesManager(config_dir=self.prefs_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scenario_a_opt_out_flow(self):
        """
        Scenario A:
        1. User asks for analytical data.
        2. ARD returns BigQuery (with needs_onboarding).
        3. OpenCode sees unauthenticated status and prompts user.
        4. User says 'no and don't ask again'.
        5. OpenCode sets preference mode='opt_out'.
        6. OpenCode re-runs search.
        7. ARD results NO LONGER return BigQuery; only Tier 0 skills returned.
        """
        # Step 1 & 2: Clean unauthenticated environment searches for analytics
        inspector = AuthInspector(
            env={"PATH": "/usr/bin"},
            custom_gcloud_bin="",
            custom_adc_path=Path(self.test_dir) / "non_existent.json",
        )
        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector,
            prefs_manager=self.prefs_manager,
        )

        initial_results = resolver.search("analyze large analytical sales data")
        bq_initial = next((r for r in initial_results if "mcp:bigquery" in r.identifier), None)
        self.assertIsNotNone(bq_initial)
        # Step 3: Verify BQ requires onboarding
        self.assertFalse(bq_initial.auth_ready)
        self.assertEqual(bq_initial.status, "needs_onboarding")

        # Step 4 & 5: User says 'no and don't ask again' -> Store preference
        self.prefs_manager.set_gcp_mode("opt_out")
        self.assertEqual(self.prefs_manager.get_gcp_mode(), "opt_out")

        # Step 6 & 7: Re-search with new stored preferences
        post_opt_out_results = resolver.search("analyze large analytical sales data")
        post_identifiers = [r.identifier for r in post_opt_out_results]

        # Step 8: BigQuery MCP MUST NOT appear anymore
        self.assertFalse(any("mcp:bigquery" in i for i in post_identifiers))

        # Tier 0 BigQuery Guidelines and performance skills must appear and be READY
        bq_skill = next((r for r in post_opt_out_results if "skills:bigquery-guidelines" in r.identifier), None)
        self.assertIsNotNone(bq_skill)
        self.assertTrue(bq_skill.auth_ready)
        self.assertEqual(bq_skill.status, "ready")

    def test_scenario_b_gcloud_onboarding_flow(self):
        """
        Scenario B:
        1. User asks for analytical data.
        2. ARD returns BigQuery (needs_onboarding).
        3. User authorizes gcloud login.
        4. gcloud ADC file is created.
        5. Re-search marks BigQuery as READY immediately.
        """
        mock_adc_path = Path(self.test_dir) / "application_default_credentials.json"

        # Step 1: Initial unauthenticated check
        inspector_before = AuthInspector(
            env={"PATH": "/usr/bin"},
            custom_gcloud_bin="",
            custom_adc_path=mock_adc_path,
        )
        resolver_before = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector_before,
            prefs_manager=self.prefs_manager,
        )
        res_before = resolver_before.search("query bigquery dataset")
        bq_before = next((r for r in res_before if "mcp:bigquery" in r.identifier), None)
        self.assertEqual(bq_before.status, "needs_onboarding")

        # Step 2: User completes gcloud auth -> ADC file exists
        with open(mock_adc_path, "w", encoding="utf-8") as f:
            json.dump({"client_id": "test.apps.googleusercontent.com", "refresh_token": "token123"}, f)

        # Step 3: Inspector now detects active User ADC
        inspector_after = AuthInspector(
            env={"PATH": "/usr/bin"},
            custom_gcloud_bin="",
            custom_adc_path=mock_adc_path,
        )
        resolver_after = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector_after,
            prefs_manager=self.prefs_manager,
        )
        res_after = resolver_after.search("query bigquery dataset")
        bq_after = next((r for r in res_after if "mcp:bigquery" in r.identifier), None)

        self.assertTrue(bq_after.auth_ready)
        self.assertEqual(bq_after.status, "ready")

    def test_scenario_c_service_account_onboarding_flow(self):
        """
        Scenario C:
        1. User asks for analytical data.
        2. ARD returns BigQuery (needs_onboarding).
        3. User provides Service Account key file via GOOGLE_APPLICATION_CREDENTIALS.
        4. Re-search detects Service Account and marks BigQuery READY immediately.
        """
        sa_key_path = Path(self.test_dir) / "service_account.json"

        # Step 1: Initial check without SA key
        inspector_before = AuthInspector(
            env={"PATH": "/usr/bin"},
            custom_gcloud_bin="",
            custom_adc_path=Path(self.test_dir) / "non_existent.json",
        )
        resolver_before = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector_before,
            prefs_manager=self.prefs_manager,
        )
        res_before = resolver_before.search("query bigquery dataset")
        bq_before = next((r for r in res_before if "mcp:bigquery" in r.identifier), None)
        self.assertEqual(bq_before.status, "needs_onboarding")

        # Step 2: User adds SA key
        with open(sa_key_path, "w", encoding="utf-8") as f:
            json.dump({
                "type": "service_account",
                "project_id": "prod-project-123",
                "client_email": "agent@prod-project-123.iam.gserviceaccount.com",
            }, f)

        # Step 3: Re-search with GOOGLE_APPLICATION_CREDENTIALS set
        inspector_after = AuthInspector(
            env={"GOOGLE_APPLICATION_CREDENTIALS": str(sa_key_path), "PATH": "/usr/bin"},
            custom_gcloud_bin="",
            custom_adc_path=Path(self.test_dir) / "non_existent.json",
        )
        resolver_after = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector_after,
            prefs_manager=self.prefs_manager,
        )
        res_after = resolver_after.search("query bigquery dataset")
        bq_after = next((r for r in res_after if "mcp:bigquery" in r.identifier), None)

        self.assertTrue(bq_after.auth_ready)
        self.assertEqual(bq_after.status, "ready")

    def test_scenario_d_gemini_api_key_only(self):
        """
        Scenario D (Path A):
        1. User has GEMINI_API_KEY in environment, but no GCP credentials.
        2. User searches for Gemini developer tools.
        3. ARD detects GEMINI_API_KEY is active -> marks Tier 1 Gemini tools READY.
        4. Tier 3 GCP tools (Vertex/BigQuery) remain marked as needs_onboarding.
        5. Zero login prompts required for Gemini API.
        """
        mock_env = {
            "GEMINI_API_KEY": "AIzaSy_TEST_KEY_12345",
            "PATH": "/usr/bin",
        }
        inspector = AuthInspector(
            env=mock_env,
            custom_gcloud_bin="",
            custom_adc_path=Path(self.test_dir) / "non_existent.json",
        )
        status = inspector.inspect()
        self.assertTrue(status.api_keys.get("GEMINI_API_KEY"))
        self.assertFalse(status.gcp_authenticated)

        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector,
            prefs_manager=self.prefs_manager,
        )

        results = resolver.search("gemini multimodal python generation")
        gemini_skill = next((r for r in results if "gemini-api-patterns" in r.identifier), None)
        self.assertIsNotNone(gemini_skill)
        self.assertEqual(gemini_skill.tier, 1)
        self.assertTrue(gemini_skill.auth_ready)
        self.assertEqual(gemini_skill.status, "ready")

    def test_scenario_e_change_mind_opt_out_to_opt_in(self):
        """
        Scenario E (Path C):
        1. User initially opts out -> preference set to 'opt_out'.
        2. ARD search strictly filters out Tier >= 3 tools.
        3. User later changes mind: 'Actually, I changed my mind, enable BigQuery and log me in'.
        4. Preference is updated to 'allowed' / 'interactive'.
        5. ARD search now presents BigQuery with clear onboarding guidance.
        """
        # Step 1: User previously opted out
        self.prefs_manager.set_gcp_mode("opt_out")
        self.prefs_manager.record_service_decision("urn:ai:google.com:mcp:bigquery", "declined")

        inspector = AuthInspector(
            env={"PATH": "/usr/bin"},
            custom_gcloud_bin="",
            custom_adc_path=Path(self.test_dir) / "non_existent.json",
        )
        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector,
            prefs_manager=self.prefs_manager,
        )

        # Step 2: In opt-out mode, BigQuery MCP is excluded
        res1 = resolver.search("query bigquery dataset")
        self.assertFalse(any("mcp:bigquery" in r.identifier for r in res1))

        # Step 3 & 4: User changes mind -> sets decision to 'allowed'
        self.prefs_manager.set_gcp_mode("auto")
        self.prefs_manager.record_service_decision("urn:ai:google.com:mcp:bigquery", "allowed")
        self.assertEqual(
            self.prefs_manager.get_service_decision("urn:ai:google.com:mcp:bigquery"), "allowed"
        )

        # Step 5: Re-search now includes BigQuery MCP with onboarding
        res2 = resolver.search("query bigquery dataset")
        bq_res = next((r for r in res2 if "mcp:bigquery" in r.identifier), None)
        self.assertIsNotNone(bq_res)
        self.assertFalse(bq_res.auth_ready)
        self.assertEqual(bq_res.status, "needs_onboarding")


if __name__ == "__main__":
    unittest.main()
