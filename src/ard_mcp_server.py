#!/usr/bin/env python3
"""
Standard MCP (Model Context Protocol) Server for ARD Google Discovery

Exposes ARD catalog search, passive auth inspection, and persistent user preferences
over JSON-RPC stdio for OpenCode, Claude Code, Cursor, Antigravity, and other MCP clients.
Zero external dependencies (pure Python standard library).
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to import ard_resolver
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ard_resolver import ARDCatalogResolver, AuthInspector, PreferencesManager


class ARDMCPServer:
    def __init__(self, catalog_path: Path = None):
        self.auth_inspector = AuthInspector()
        self.prefs_manager = PreferencesManager()
        self.resolver = ARDCatalogResolver(
            catalog_path=catalog_path,
            auth_inspector=self.auth_inspector,
            prefs_manager=self.prefs_manager,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "ard_search",
                "description": (
                    "Search Google Cloud Managed MCP servers and Google Agent Skills "
                    "using natural language queries. Returns capabilities with Auth Tiers "
                    "(Tier 0: No auth, Tier 1: API keys, Tier 3: GCP ADC/Service Account) "
                    "and onboarding recommendations. Respects user opt-out preferences."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query describing the needed capability or task.",
                        },
                        "tier": {
                            "type": "integer",
                            "description": "Optional Auth Tier filter (0: No auth, 1: API key, 3: GCP account).",
                        },
                        "opt_out": {
                            "type": "boolean",
                            "description": "If true, strictly filters out all GCP account-required tools.",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "ard_auth_status",
                "description": "Inspect the local system authentication status (Service Account, User ADC, gcloud CLI).",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "ard_set_preference",
                "description": (
                    "Persistently set the user's Google Cloud discovery preference. "
                    "Use 'opt_out' when the user requests never to be asked about GCP again."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["auto", "always_allow", "opt_out"],
                            "description": "GCP discovery mode: 'auto' (smart fallback), 'always_allow', or 'opt_out' (strict zero-cloud).",
                        }
                    },
                    "required": ["mode"],
                },
            },
            {
                "name": "ard_record_decision",
                "description": (
                    "Record a persistent user decision for a specific service URN so the user is never asked twice. "
                    "When the user agrees to onboard or use a service (decision='allowed'), call this tool to persist "
                    "their consent, then output clear onboarding commands (e.g. 'gcloud auth application-default login') "
                    "for the user to run on their terminal."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service_identifier": {
                            "type": "string",
                            "description": "URN identifier of the service (e.g. urn:ai:google.com:mcp:bigquery).",
                        },
                        "decision": {
                            "type": "string",
                            "enum": ["allowed", "declined", "onboarded"],
                            "description": "The user's decision.",
                        },
                    },
                    "required": ["service_identifier", "decision"],
                },
            },
            {
                "name": "ard_get_resource",
                "description": (
                    "Retrieve the full catalog resource definition and details for a specific canonical URN "
                    "(e.g. urn:ai:google.com:skills:bigquery-guidelines or urn:ai:google.com:mcp:bigquery)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service_identifier": {
                            "type": "string",
                            "description": "Canonical URN identifier of the resource.",
                        }
                    },
                    "required": ["service_identifier"],
                },
            },
        ]

    def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "ard_search":
            query = arguments.get("query", "")
            tier = arguments.get("tier")
            opt_out = arguments.get("opt_out", False)
            results = self.resolver.search(query=query, tier_filter=tier, force_opt_out=opt_out)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps([r.to_dict() for r in results], indent=2),
                    }
                ]
            }
        elif name == "ard_get_resource":
            ident = arguments.get("service_identifier", "")
            resource = self.resolver.get_resource(ident)
            if resource:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(resource, indent=2),
                        }
                    ]
                }
            else:
                return {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"Resource with identifier '{ident}' not found in catalog.",
                        }
                    ],
                }
        elif name == "ard_auth_status":
            status = self.auth_inspector.inspect(fast=True)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(status.to_dict(), indent=2),
                    }
                ]
            }
        elif name == "ard_set_preference":
            mode = arguments.get("mode", "auto")
            self.prefs_manager.set_gcp_mode(mode)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"GCP discovery mode successfully set to '{mode}'.",
                    }
                ]
            }
        elif name == "ard_record_decision":
            service_id = arguments.get("service_identifier", "")
            decision = arguments.get("decision", "")
            self.prefs_manager.record_service_decision(service_id, decision)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Decision for '{service_id}' successfully recorded as '{decision}'.",
                    }
                ]
            }
        else:
            raise ValueError(f"Unknown tool: {name}")

    def run_stdio(self) -> None:
        """Main JSON-RPC stdio loop."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                continue

            msg_id = msg.get("id")
            method = msg.get("method")
            params = msg.get("params", {})

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "ard-google-discovery",
                            "version": "1.0.0",
                        },
                    },
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": self.get_tools()},
                }
            elif method == "tools/call":
                tool_name = params.get("name", "")
                args = params.get("arguments", {})
                try:
                    result = self.handle_call_tool(tool_name, args)
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": result,
                    }
                except Exception as exc:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32603, "message": str(exc)},
                    }
            elif method == "notifications/initialized":
                continue
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method {method} not found"},
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    server = ARDMCPServer()
    server.run_stdio()
