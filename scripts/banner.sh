#!/usr/bin/env bash
# Reset scenario environment and render clean header
clear
rm -f /tmp/opencode_session_active
rm -rf .config/ard .config/gcloud

SCENARIO="${1:-0}"

case "$SCENARIO" in
  0)
    echo -e "\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;36m║\033[0m                   \033[1;37mOPENCODE AGENT WITH ARD GOOGLE ECOSYSTEM DISCOVERY\033[0m                                 \033[1;36m║\033[0m"
    echo -e "\033[1;36m║\033[0m            \033[0;33mAutonomous AI Agent Tool Calling, Progressive Auth Tiers & Opt-Out Control\033[0m                \033[1;36m║\033[0m"
    echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  1)
    echo -e "\033[1;32m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[1;37mSCENARIO 1: Pure Public Discovery (Tier 0 Zero-Auth Counterpoint)\033[0m                                   \033[1;32m║\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[0;33mUser asks for security & SQL tuning -> OpenCode finds & recommends Tier 0 skills (No auth needed)\033[0m   \033[1;32m║\033[0m"
    echo -e "\033[1;32m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  2)
    echo -e "\033[1;35m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[1;37mSCENARIO 2: Cloud Intent -> User Opts Out ('No with an opt out')\033[0m                                     \033[1;35m║\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[0;33mOpenCode asks 'Do you want to login to GCP?' -> User: 'No with an opt out' -> GCP silenced forever\033[0m  \033[1;35m║\033[0m"
    echo -e "\033[1;35m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  3)
    echo -e "\033[1;34m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[1;37mSCENARIO 3: Cloud Intent -> User Onboards ('Yes') -> Human OAuth & Live BigQuery Execution\033[0m           \033[1;34m║\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[0;33mOpenCode asks to login -> User: 'Yes' -> Human OAuth -> OpenCode executes live BigQuery query\033[0m       \033[1;34m║\033[0m"
    echo -e "\033[1;34m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  4)
    echo -e "\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;36m║\033[0m  \033[1;37mAUTOMATED E2E TEST RUNNER IN PODMAN CONTAINER\033[0m                                                       \033[1;36m║\033[0m"
    echo -e "\033[1;36m║\033[0m  \033[0;33mVerifying all 3 core scenarios with real OpenCode AI agent calls\033[0m                                     \033[1;36m║\033[0m"
    echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
esac
echo ""
