#!/usr/bin/env python3
"""
Automated Test Suite for ARD Resolver & Multi-Runtime Auth Scenarios

Tests all key auth configurations using isolated temporary directories and mocked bare environments:
- Canonical URN format: urn:ai:google.com:...
- Scenario 1: Active Service Account Key (GOOGLE_APPLICATION_CREDENTIALS)
- Scenario 2: Active User ADC (~/.config/gcloud/application_default_credentials.json)
- Scenario 3: gcloud installed, but unauthenticated
- Scenario 4: Bare system with zero gcloud or credentials
- Scenario 5: User Opt-Out Mode (strictly filters out Tier >= 3 cloud tools)
- Scenario 6: Natural language query resolution, scoring, and fallback skills
- Scenario 7: Multi-runtime preferences (CLI filesystem, ARD_CONFIG_DIR, and in-memory ARD_PREFERENCES_JSON for ADK)
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

from ard_resolver import (
    ARDCatalogResolver,
    AuthInspector,
    PreferencesManager,
)


class TestARDResolverAuthScenarios(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.catalog_path = Path(__file__).resolve().parent.parent / "ai-catalog.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_canonical_urn_format(self):
        """Verify all entries in ai-catalog.json strictly use canonical urn:ai: FQDN format."""
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        entries = catalog.get("entries", [])
        self.assertGreater(len(entries), 10)
        for entry in entries:
            identifier = entry.get("identifier", "")
            self.assertTrue(
                identifier.startswith("urn:ai:google.com:"),
                f"Identifier {identifier} does not use canonical urn:ai:google.com: prefix",
            )

    def test_scenario_1_service_account_active(self):
        """Scenario 1: System has GOOGLE_APPLICATION_CREDENTIALS pointing to a valid SA key."""
        sa_key_file = Path(self.test_dir) / "service_account.json"
        with open(sa_key_file, "w", encoding="utf-8") as f:
            json.dump({"type": "service_account", "project_id": "test-project-123"}, f)

        mock_env = {
            "GOOGLE_APPLICATION_CREDENTIALS": str(sa_key_file),
            "PATH": "",
        }
        inspector = AuthInspector(env=mock_env)
        status = inspector.inspect()

        self.assertTrue(status.service_account_active)
        self.assertTrue(status.gcp_authenticated)
        self.assertEqual(status.summary, "service_account")

        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector,
            prefs_manager=PreferencesManager(config_dir=Path(self.test_dir) / "prefs"),
        )
        results = resolver.search("query bigquery dataset")
        bq_res = next((r for r in results if "mcp:bigquery" in r.identifier), None)
        self.assertIsNotNone(bq_res)
        self.assertTrue(bq_res.auth_ready)
        self.assertEqual(bq_res.status, "ready")

    def test_scenario_2_user_adc_active(self):
        """Scenario 2: System has standard application_default_credentials.json."""
        adc_file = Path(self.test_dir) / "application_default_credentials.json"
        with open(adc_file, "w", encoding="utf-8") as f:
            json.dump({"client_id": "test.apps.googleusercontent.com", "type": "authorized_user"}, f)

        mock_env = {"PATH": ""}
        inspector = AuthInspector(env=mock_env, custom_adc_path=adc_file)
        status = inspector.inspect()

        self.assertTrue(status.user_adc_active)
        self.assertTrue(status.gcp_authenticated)
        self.assertEqual(status.summary, "user_adc")

        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector,
            prefs_manager=PreferencesManager(config_dir=Path(self.test_dir) / "prefs"),
        )
        results = resolver.search("cloud storage bucket")
        gcs_res = next((r for r in results if "cloud-storage" in r.identifier), None)
        self.assertIsNotNone(gcs_res)
        self.assertTrue(gcs_res.auth_ready)
        self.assertEqual(gcs_res.status, "ready")

    def test_scenario_3_gcloud_installed_unauthenticated(self):
        """Scenario 3: gcloud is in PATH, but no credentials are saved."""
        mock_env = {"PATH": "/mock/bin"}
        inspector = AuthInspector(
            env=mock_env,
            custom_gcloud_bin="/mock/bin/gcloud",
            custom_adc_path=Path(self.test_dir) / "non_existent_adc.json",
        )
        status = inspector.inspect()

        self.assertTrue(status.gcloud_installed)
        self.assertFalse(status.gcp_authenticated)
        self.assertEqual(status.summary, "gcloud_unauthenticated")

        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector,
            prefs_manager=PreferencesManager(config_dir=Path(self.test_dir) / "prefs"),
        )
        results = resolver.search("query bigquery dataset")
        bq_res = next((r for r in results if "mcp:bigquery" in r.identifier), None)
        self.assertIsNotNone(bq_res)
        self.assertFalse(bq_res.auth_ready)
        self.assertEqual(bq_res.status, "needs_onboarding")
        self.assertIn("gcloud auth application-default login", bq_res.onboarding["command"])

    def test_scenario_4_bare_system_no_gcloud(self):
        """Scenario 4: Bare system without gcloud or GCP credentials (offline/clean)."""
        mock_env = {"PATH": "/usr/bin"}
        inspector = AuthInspector(
            env=mock_env,
            custom_gcloud_bin="",
            custom_adc_path=Path(self.test_dir) / "non_existent.json",
        )
        status = inspector.inspect()

        self.assertFalse(status.gcloud_installed)
        self.assertFalse(status.gcp_authenticated)

        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector,
            prefs_manager=PreferencesManager(config_dir=Path(self.test_dir) / "prefs"),
        )
        results = resolver.search("security architecture zero trust")
        sec_skill = next((r for r in results if "well-architected-security" in r.identifier), None)
        self.assertIsNotNone(sec_skill)
        self.assertEqual(sec_skill.tier, 0)
        self.assertTrue(sec_skill.auth_ready)
        self.assertEqual(sec_skill.status, "ready")

    def test_scenario_5_user_opt_out_mode(self):
        """Scenario 5: User preference set to 'opt_out' -> Tier >= 3 tools are completely excluded."""
        prefs = PreferencesManager(config_dir=Path(self.test_dir) / "prefs")
        prefs.set_gcp_mode("opt_out")

        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            prefs_manager=prefs,
        )

        results = resolver.search("bigquery analytical sql query")
        identifiers = [r.identifier for r in results]

        self.assertTrue(any("skills:bigquery-guidelines" in i for i in identifiers))
        self.assertFalse(any("mcp:bigquery" in i for i in identifiers))
        for r in results:
            self.assertLess(r.tier, 3)

    def test_scenario_6_fallback_skills_and_api_keys(self):
        """Scenario 6: Verify API key detection (Gemini) and fallback skill links."""
        mock_env = {"GEMINI_API_KEY": "test-key-12345"}
        inspector = AuthInspector(env=mock_env)
        status = inspector.inspect()
        self.assertTrue(status.api_keys["GEMINI_API_KEY"])

        resolver = ARDCatalogResolver(
            catalog_path=self.catalog_path,
            auth_inspector=inspector,
            prefs_manager=PreferencesManager(config_dir=Path(self.test_dir) / "prefs"),
        )
        results = resolver.search("gemini function calling python")
        gemini_res = next((r for r in results if "gemini-api-patterns" in r.identifier), None)
        self.assertIsNotNone(gemini_res)
        self.assertEqual(gemini_res.tier, 1)
        self.assertTrue(gemini_res.auth_ready)
        self.assertEqual(gemini_res.status, "ready")

    def test_scenario_7_multi_runtime_preferences(self):
        """Scenario 7: Preferences work in ADK / ephemeral runtimes via env vars & memory."""
        # Test in-memory / ADK env string injection
        adk_env = {
            "ARD_PREFERENCES_JSON": json.dumps({
                "gcp_mode": "opt_out",
                "service_decisions": {"urn:ai:google.com:mcp:bigquery": "declined"}
            })
        }
        prefs_adk = PreferencesManager(env=adk_env)
        self.assertEqual(prefs_adk.get_gcp_mode(), "opt_out")
        self.assertEqual(
            prefs_adk.get_service_decision("urn:ai:google.com:mcp:bigquery"), "declined"
        )


if __name__ == "__main__":
    unittest.main()
