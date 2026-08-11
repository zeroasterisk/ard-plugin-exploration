#!/usr/bin/env python3
"""
ARD (Agent Resource Discovery) Google Ecosystem Resolver & Auth Manager

This standalone, zero-dependency engine handles:
1. ARD v0.5 catalog search and natural language matching.
2. Progressive Auth Tier resolution (Tier 0: No Auth, Tier 1: API Key, Tier 2: GCP Account/ADC).
3. System Auth Environment Inspection (Service Accounts, User ADC, gcloud CLI status).
4. Persistent User Preferences (e.g. Opt-Out of GCP tools, remember onboarding choices forever).
5. Non-intrusive progressive onboarding recommendations and fallback skills.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen


DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent / "ai-catalog.json"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "ard"
PREFERENCES_FILE = "preferences.json"


@dataclass
class AuthStatus:
    gcloud_installed: bool = False
    gcloud_path: Optional[str] = None
    service_account_active: bool = False
    service_account_path: Optional[str] = None
    user_adc_active: bool = False
    user_adc_path: Optional[str] = None
    gcp_authenticated: bool = False
    api_keys: Dict[str, bool] = field(default_factory=dict)
    summary: str = "no_gcp_auth"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuthInspector:
    """Inspects system authentication state without modifying environment."""

    def __init__(
        self,
        env: Optional[Dict[str, str]] = None,
        custom_gcloud_bin: Optional[str] = None,
        custom_adc_path: Optional[Path] = None,
    ):
        self.env = env if env is not None else os.environ
        self.custom_gcloud_bin = custom_gcloud_bin
        self.custom_adc_path = custom_adc_path

    def inspect(self, fast: bool = True) -> AuthStatus:
        status = AuthStatus()

        # 1. Check Service Account Key via GOOGLE_APPLICATION_CREDENTIALS
        sa_env = self.env.get("GOOGLE_APPLICATION_CREDENTIALS")
        if sa_env and Path(sa_env).is_file():
            try:
                with open(sa_env, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data.get("type") in {
                        "service_account",
                        "authorized_user",
                        "external_account",
                    }:
                        status.service_account_active = True
                        status.service_account_path = sa_env
            except Exception:
                pass

        # 2. Check Standard User ADC Location
        if self.custom_adc_path:
            adc_path = self.custom_adc_path
        else:
            if sys.platform == "win32":
                appdata = self.env.get("APPDATA", "")
                adc_path = Path(appdata) / "gcloud" / "application_default_credentials.json"
            else:
                config_home = self.env.get("XDG_CONFIG_HOME")
                base = Path(config_home) if config_home else Path.home() / ".config"
                adc_path = base / "gcloud" / "application_default_credentials.json"

        if adc_path.is_file():
            try:
                with open(adc_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "client_id" in data:
                        status.user_adc_active = True
                        status.user_adc_path = str(adc_path)
            except Exception:
                pass

        # 3. Check gcloud CLI binary availability
        if self.custom_gcloud_bin is not None:
            gcloud_bin = self.custom_gcloud_bin if self.custom_gcloud_bin else None
        else:
            gcloud_bin = shutil.which("gcloud", path=self.env.get("PATH"))

        if gcloud_bin:
            status.gcloud_installed = True
            status.gcloud_path = gcloud_bin

        # 4. Determine GCP authentication state
        if status.service_account_active:
            status.gcp_authenticated = True
            status.summary = "service_account"
        elif status.user_adc_active:
            status.gcp_authenticated = True
            status.summary = "user_adc"
        elif status.gcloud_installed:
            if not fast:
                # Optionally run dry-run token check if deep inspection requested
                try:
                    res = subprocess.run(
                        [gcloud_bin, "auth", "application-default", "print-access-token"],
                        capture_output=True,
                        text=True,
                        timeout=3,
                        env=self.env,
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        status.gcp_authenticated = True
                        status.summary = "gcloud_authenticated"
                    else:
                        status.summary = "gcloud_unauthenticated"
                except Exception:
                    status.summary = "gcloud_unauthenticated"
            else:
                status.summary = "gcloud_unauthenticated"
        else:
            status.summary = "no_gcloud"

        # 5. Check relevant API keys
        status.api_keys = {
            "GEMINI_API_KEY": bool(self.env.get("GEMINI_API_KEY")),
            "GOOGLE_API_KEY": bool(self.env.get("GOOGLE_API_KEY")),
        }

        return status


class PreferencesManager:
    """Manages persistent user preferences (e.g. GCP opt-out, tool permissions)."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.prefs_file = self.config_dir / PREFERENCES_FILE
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.prefs_file.is_file():
            return {
                "gcp_mode": "auto",  # 'auto', 'always_allow', 'opt_out'
                "service_decisions": {},
                "suppress_onboarding_prompts": False,
            }
        try:
            with open(self.prefs_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "gcp_mode": "auto",
                "service_decisions": {},
                "suppress_onboarding_prompts": False,
            }

    def save(self, data: Dict[str, Any]) -> None:
        self._ensure_config_dir()
        with open(self.prefs_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_gcp_mode(self) -> str:
        return self.load().get("gcp_mode", "auto")

    def set_gcp_mode(self, mode: str) -> None:
        if mode not in {"auto", "always_allow", "opt_out"}:
            raise ValueError(f"Invalid mode: {mode}. Choose auto, always_allow, or opt_out.")
        data = self.load()
        data["gcp_mode"] = mode
        self.save(data)

    def get_service_decision(self, identifier: str) -> Optional[str]:
        decisions = self.load().get("service_decisions", {})
        return decisions.get(identifier)

    def record_service_decision(self, identifier: str, decision: str) -> None:
        data = self.load()
        data.setdefault("service_decisions", {})[identifier] = decision
        self.save(data)


@dataclass
class ResolvedResource:
    identifier: str
    displayName: str
    type: str
    description: str
    url: str
    tags: List[str]
    capabilities: List[str]
    score: int
    tier: int
    auth_type: str
    auth_required: bool
    auth_ready: bool
    status: str  # 'ready', 'needs_api_key', 'needs_onboarding', 'opted_out'
    action_suggestion: Optional[str] = None
    onboarding: Optional[Dict[str, Any]] = None
    fallback_skill: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ARDCatalogResolver:
    """Loads ARD v0.5 catalog, performs query matching, applies auth & user preferences."""

    def __init__(
        self,
        catalog_path: Optional[Path] = None,
        auth_inspector: Optional[AuthInspector] = None,
        prefs_manager: Optional[PreferencesManager] = None,
    ):
        self.catalog_path = catalog_path or DEFAULT_CATALOG_PATH
        self.auth_inspector = auth_inspector or AuthInspector()
        self.prefs_manager = prefs_manager or PreferencesManager()
        self._catalog_data: Optional[Dict[str, Any]] = None

    def load_catalog(self) -> Dict[str, Any]:
        if self._catalog_data is not None:
            return self._catalog_data

        if isinstance(self.catalog_path, str) and self.catalog_path.startswith(("http://", "https://")):
            req = Request(self.catalog_path, headers={"User-Agent": "ard-resolver/1.0"})
            with urlopen(req, timeout=10) as resp:
                self._catalog_data = json.loads(resp.read().decode("utf-8"))
        else:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self._catalog_data = json.load(f)
        return self._catalog_data

    STOP_WORDS = {
        "how", "to", "for", "a", "an", "the", "in", "and", "of", "with", "is", "on", "by",
        "at", "from", "do", "i", "can", "my", "me", "this", "that", "it", "what"
    }

    def _score_entry(self, entry: Dict[str, Any], query_terms: List[str]) -> int:
        if not query_terms:
            return 50

        # Filter out stop words if there are specific content terms
        meaningful_terms = [t for t in query_terms if t not in self.STOP_WORDS]
        active_terms = meaningful_terms if meaningful_terms else query_terms

        display_name = entry.get("displayName", "").lower()
        description = entry.get("description", "").lower()
        tags = [t.lower() for t in entry.get("tags", [])]
        capabilities = [c.lower() for c in entry.get("capabilities", [])]
        rep_queries = [rq.lower() for rq in entry.get("representativeQueries", [])]

        score = 0
        matched_terms = set()

        # Check exact query match in representative queries
        full_query = " ".join(query_terms).lower()
        if any(full_query in rq for rq in rep_queries):
            score += 45

        for term in active_terms:
            term_matched = False
            if term in display_name:
                score += 25
                term_matched = True
            if any(term in tag for tag in tags):
                score += 20
                term_matched = True
            if any(term in cap for cap in capabilities):
                score += 20
                term_matched = True
            if any(term in rq for rq in rep_queries):
                score += 15
                term_matched = True
            if term in description:
                score += 10
                term_matched = True

            if term_matched:
                matched_terms.add(term)

        if not matched_terms:
            return 0

        # Add coverage multiplier
        coverage = len(matched_terms) / len(active_terms)
        score = int(score * coverage)

        return min(100, max(20, score))

    def search(
        self,
        query: str,
        limit: int = 10,
        tier_filter: Optional[int] = None,
        force_opt_out: bool = False,
    ) -> List[ResolvedResource]:
        catalog = self.load_catalog()
        entries = catalog.get("entries", [])
        auth_status = self.auth_inspector.inspect()
        gcp_mode = "opt_out" if force_opt_out else self.prefs_manager.get_gcp_mode()

        query_terms = [t.lower() for t in query.strip().split() if t]
        results: List[ResolvedResource] = []

        for entry in entries:
            metadata = entry.get("metadata", {})
            auth_meta = metadata.get("auth", {})
            tier = auth_meta.get("tier", 0)
            auth_type = auth_meta.get("type", "none")
            auth_required = auth_meta.get("required", False)

            # Filter out Tier 2 if user has opted out of GCP services
            if gcp_mode == "opt_out" and tier >= 2:
                continue

            # Apply explicit tier filter if requested
            if tier_filter is not None and tier != tier_filter:
                continue

            score = self._score_entry(entry, query_terms)
            if score == 0:
                continue

            # Determine Auth Readiness and Action Suggestions
            auth_ready = False
            status = "ready"
            action_suggestion = None
            onboarding = None
            fallback_skill = auth_meta.get("fallbackSkill")

            if tier == 0:
                auth_ready = True
                status = "ready"
                action_suggestion = "Ready for immediate offline/local execution."
            elif tier == 1:
                env_vars = auth_meta.get("envVars", [])
                has_key = any(auth_status.api_keys.get(k) for k in env_vars)
                if not auth_required or has_key or auth_type == "none":
                    auth_ready = True
                    status = "ready"
                    action_suggestion = "Public endpoint or API key active."
                else:
                    auth_ready = False
                    status = "needs_api_key"
                    onboarding = {
                        "type": "api_key",
                        "url": auth_meta.get("onboardingUrl"),
                        "envVars": env_vars,
                        "message": f"Requires free API key in {', '.join(env_vars)}.",
                    }
                    action_suggestion = f"Set {', '.join(env_vars)} or design offline."
            elif tier == 2:
                if auth_status.gcp_authenticated:
                    auth_ready = True
                    status = "ready"
                    action_suggestion = f"GCP authenticated ({auth_status.summary}). Ready to execute."
                else:
                    auth_ready = False
                    status = "needs_onboarding"
                    cmd = auth_meta.get("onboardingCommand", "gcloud auth application-default login")
                    onboarding = {
                        "type": "gcp_adc",
                        "command": cmd,
                        "url": auth_meta.get("onboardingUrl"),
                        "freeTier": auth_meta.get("freeTier", False),
                        "freeTierDetails": auth_meta.get("freeTierDetails", ""),
                        "message": (
                            f"Requires GCP credentials. Run `{cmd}` or sign up for free tier."
                        ),
                    }
                    action_suggestion = (
                        f"Requires GCP auth (`{cmd}`). "
                        + (f"Fallback: `{fallback_skill}`." if fallback_skill else "")
                    )

            # Adjust score ranking based on user readiness
            final_score = score
            if not auth_ready and gcp_mode == "auto":
                # Slightly de-prioritize unauthenticated cloud tools below ready local skills
                final_score = max(10, score - 15)

            results.append(
                ResolvedResource(
                    identifier=entry["identifier"],
                    displayName=entry["displayName"],
                    type=entry["type"],
                    description=entry.get("description", ""),
                    url=entry.get("url", ""),
                    tags=entry.get("tags", []),
                    capabilities=entry.get("capabilities", []),
                    score=final_score,
                    tier=tier,
                    auth_type=auth_type,
                    auth_required=auth_required,
                    auth_ready=auth_ready,
                    status=status,
                    action_suggestion=action_suggestion,
                    onboarding=onboarding,
                    fallback_skill=fallback_skill,
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ard-resolver",
        description="ARD Resource Discovery & Auth Tier Resolver CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # search
    search_p = subparsers.add_parser("search", help="Search ARD catalog resources")
    search_p.add_argument("query", help="Natural language query")
    search_p.add_argument("--catalog", help="Path or URL to ai-catalog.json")
    search_p.add_argument("--limit", type=int, default=10, help="Max results")
    search_p.add_argument("--tier", type=int, choices=[0, 1, 2], help="Filter by Auth Tier")
    search_p.add_argument("--opt-out", action="store_true", help="Filter out all GCP tools")
    search_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # auth
    auth_p = subparsers.add_parser("auth", help="Manage and inspect authentication")
    auth_sub = auth_p.add_subparsers(dest="auth_action", help="Auth action")
    auth_status_p = auth_sub.add_parser("status", help="Show current auth environment")
    auth_status_p.add_argument("--json", action="store_true", help="Output JSON")

    # prefs
    prefs_p = subparsers.add_parser("prefs", help="Manage persistent user preferences")
    prefs_sub = prefs_p.add_subparsers(dest="prefs_action", help="Preferences action")
    prefs_get_p = prefs_sub.add_parser("get", help="Get current preferences")
    prefs_get_p.add_argument("--json", action="store_true", help="Output JSON")

    prefs_set_p = prefs_sub.add_parser("set-mode", help="Set GCP mode")
    prefs_set_p.add_argument(
        "mode", choices=["auto", "always_allow", "opt_out"], help="GCP discovery mode"
    )

    prefs_sub.add_parser("opt-out", help="Opt out of all GCP account recommendations")
    prefs_sub.add_parser("opt-in", help="Reset GCP discovery mode to auto")

    return parser


def main() -> None:
    parser = build_cli()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "search":
        catalog_path = Path(args.catalog) if args.catalog else DEFAULT_CATALOG_PATH
        resolver = ARDCatalogResolver(catalog_path=catalog_path)
        results = resolver.search(
            query=args.query,
            limit=args.limit,
            tier_filter=args.tier,
            force_opt_out=args.opt_out,
        )

        if args.json:
            print(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            print(f"\n🔍 ARD Discovery Results for: '{args.query}' (Found: {len(results)})")
            print("=" * 80)
            for idx, res in enumerate(results, 1):
                tier_badge = f"[Tier {res.tier}: {res.auth_type.upper()}]"
                status_badge = f"[{res.status.upper()}]"
                print(f"{idx}. {res.displayName} (Score: {res.score}) {tier_badge} {status_badge}")
                print(f"   ID:   {res.identifier}")
                print(f"   Type: {res.type}")
                print(f"   Desc: {res.description}")
                print(f"   URL:  {res.url}")
                if res.action_suggestion:
                    print(f"   💡 Action: {res.action_suggestion}")
                if res.onboarding:
                    print(f"   🚀 Onboarding: {res.onboarding.get('message')}")
                print("-" * 80)

    elif args.command == "auth":
        inspector = AuthInspector()
        status = inspector.inspect(fast=False)
        if getattr(args, "json", False):
            print(json.dumps(status.to_dict(), indent=2))
        else:
            print("\n🔐 System Authentication Status:")
            print("=" * 50)
            print(f"• gcloud CLI installed:     {'✅ Yes' if status.gcloud_installed else '❌ No'}")
            if status.gcloud_path:
                print(f"  Path:                    {status.gcloud_path}")
            print(f"• Service Account Active:  {'✅ Yes' if status.service_account_active else '❌ No'}")
            if status.service_account_path:
                print(f"  Path:                    {status.service_account_path}")
            print(f"• User ADC Active:         {'✅ Yes' if status.user_adc_active else '❌ No'}")
            if status.user_adc_path:
                print(f"  Path:                    {status.user_adc_path}")
            print(f"• GCP Authenticated:       {'✅ YES' if status.gcp_authenticated else '❌ NO'}")
            print(f"• Auth Mode Summary:       {status.summary}")
            print(f"• Gemini API Key Set:      {'✅ Yes' if status.api_keys.get('GEMINI_API_KEY') else '❌ No'}")
            print("=" * 50)

    elif args.command == "prefs":
        prefs = PreferencesManager()
        if args.prefs_action == "get":
            data = prefs.load()
            if getattr(args, "json", False):
                print(json.dumps(data, indent=2))
            else:
                print("\n⚙️ Persistent ARD Preferences:")
                print("=" * 40)
                print(f"• GCP Discovery Mode: {data.get('gcp_mode')}")
                print(f"• Suppress Prompts:   {data.get('suppress_onboarding_prompts')}")
                print(f"• Service Decisions:  {len(data.get('service_decisions', {}))} recorded")
                print("=" * 40)
        elif args.prefs_action == "set-mode":
            prefs.set_gcp_mode(args.mode)
            print(f"✅ Set GCP mode to: {args.mode}")
        elif args.prefs_action == "opt-out":
            prefs.set_gcp_mode("opt_out")
            print("🚫 Opted out of all GCP account recommendations. Tier 2 items will never be shown.")
        elif args.prefs_action == "opt-in":
            prefs.set_gcp_mode("auto")
            print("✅ Reset GCP discovery mode to 'auto'.")


if __name__ == "__main__":
    main()
