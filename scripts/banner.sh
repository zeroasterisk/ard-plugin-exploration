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
    echo -e "\033[1;32m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[1;37mSCENARIO 4 (Path A): API Key Only (Tier 1 Gemini Developer API)\033[0m                                      \033[1;32m║\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[0;33mGEMINI_API_KEY detected -> Gemini developer tools unlocked directly with zero GCP login prompts\033[0m       \033[1;32m║\033[0m"
    echo -e "\033[1;32m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  5)
    echo -e "\033[1;33m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;33m║\033[0m  \033[1;37mSCENARIO 5 (Path B): Enterprise Service Account Mount (Tier 3 Automated)\033[0m                            \033[1;33m║\033[0m"
    echo -e "\033[1;33m║\033[0m  \033[0;33mGOOGLE_APPLICATION_CREDENTIALS mounted -> OpenCode passively enables cloud tools without prompts\033[0m      \033[1;33m║\033[0m"
    echo -e "\033[1;33m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  6)
    echo -e "\033[1;35m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[1;37mSCENARIO 6 (Path C): Changing Mind (Opt-Out -> Opt-In Re-Enablement)\033[0m                                 \033[1;35m║\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[0;33mUser previously opted out -> 'Actually, log me into GCP' -> ARD seamlessly flips to allowed\033[0m           \033[1;35m║\033[0m"
    echo -e "\033[1;35m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  7)
    echo -e "\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;36m║\033[0m  \033[1;37mSCENARIO 7: Complete 7-Test Automated E2E Suite in Podman Container\033[0m                                 \033[1;36m║\033[0m"
    echo -e "\033[1;36m║\033[0m  \033[0;33mExecuting full automated containerized test suite for ARD v0.5 & OpenCode\033[0m                            \033[1;36m║\033[0m"
    echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
esac
echo ""
