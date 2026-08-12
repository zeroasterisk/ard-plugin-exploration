#!/usr/bin/env bash
# Reset scenario environment and render clean 5-step basics headers
clear
rm -f .config/opencode_session_active /tmp/opencode_session_active
rm -rf .config/ard .config/gcloud

STEP="${1:-0}"

case "$STEP" in
  0)
    echo -e "\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;36m║\033[0m            \033[1;37mAGENT RESOURCE DISCOVERY (ARD v0.5) • 5-STEP BASICS WALKTHROUGH\033[0m                     \033[1;36m║\033[0m"
    echo -e "\033[1;36m║\033[0m       \033[0;33mHow OpenCode Discovers, Evaluates, Installs, and Uses Agent Skills & Plugins\033[0m            \033[1;36m║\033[0m"
    echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  1)
    echo -e "\033[1;32m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[1;37mSTEP 1: The Agent Environment (Here's OpenCode)\033[0m                                                      \033[1;32m║\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[0;33mOpenCode agent initializes with the canonical ARD discovery MCP plugin loaded\033[0m                        \033[1;32m║\033[0m"
    echo -e "\033[1;32m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  2)
    echo -e "\033[1;34m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[1;37mSTEP 2: Capability Search (Here's How It Searches via ARD)\033[0m                                           \033[1;34m║\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[0;33mUser asks high-level query -> OpenCode calls ard_search with semantic terms\033[0m                           \033[1;34m║\033[0m"
    echo -e "\033[1;34m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  3)
    echo -e "\033[1;35m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[1;37mSTEP 3: AI Catalog Lookup (Here's How It Finds What It Wants)\033[0m                                        \033[1;35m║\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[0;33mOpenCode inspects ai-catalog.json manifest, ranking Tier 0 skills vs MCP servers\033[0m                     \033[1;35m║\033[0m"
    echo -e "\033[1;35m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  4)
    echo -e "\033[1;33m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;33m║\033[0m  \033[1;37mSTEP 4: Plugin Setup & Enablement (Here's How It Installs / Loads the Plugin)\033[0m                        \033[1;33m║\033[0m"
    echo -e "\033[1;33m║\033[0m  \033[0;33mOpenCode enables the skill, verifying zero auth friction for Tier 0 standalone resources\033[0m              \033[1;33m║\033[0m"
    echo -e "\033[1;33m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  5)
    echo -e "\033[1;32m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[1;37mSTEP 5: Normal Execution (Here's How It Uses the Plugin to Solve Tasks)\033[0m                              \033[1;32m║\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[0;33mOpenCode applies the specialized guidelines directly into its coding response\033[0m                         \033[1;32m║\033[0m"
    echo -e "\033[1;32m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
esac
