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


if __name__ == "__main__":
    unittest.main()
