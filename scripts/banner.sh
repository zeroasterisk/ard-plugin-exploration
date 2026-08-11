#!/usr/bin/env bash
# Helper script to display clean scenario headers instantly
clear
SCENARIO="${1:-0}"

case "$SCENARIO" in
  0)
    echo -e "\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;36m║\033[0m                   \033[1;37mOPENCODE AGENT WITH ARD GOOGLE ECOSYSTEM DISCOVERY\033[0m                                 \033[1;36m║\033[0m"
    echo -e "\033[1;36m║\033[0m         \033[0;33mReal AI Agent Execution with Autonomous Tool Calling, Auth Tiers & Opt-Out\033[0m                   \033[1;36m║\033[0m"
    echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  1)
    echo -e "\033[1;32m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[1;37mSCENARIO 1: Pure Open-Source Dev (Zero Auth / Zero GCP Account)\033[0m                                     \033[1;32m║\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[0;33mUser asks for security design & SQL tuning -> OpenCode finds & recommends Tier 0 offline skills\033[0m      \033[1;32m║\033[0m"
    echo -e "\033[1;32m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  2)
    echo -e "\033[1;35m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[1;37mSCENARIO 2: OpenCode Multi-Turn Opt-Out Flow (Never Show Cloud Tools)\033[0m                               \033[1;35m║\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[0;33mUser declines GCP -> OpenCode calls ard_set_preference(mode='opt_out') -> BigQuery silenced forever\033[0m \033[1;35m║\033[0m"
    echo -e "\033[1;35m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  3)
    echo -e "\033[1;34m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[1;37mSCENARIO 3: Authenticated Enterprise Dev with Service Account\033[0m                                       \033[1;34m║\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[0;33mOpenCode calls ard_auth_status -> Detects SA key -> Marks BigQuery & Cloud Storage [READY]\033[0m           \033[1;34m║\033[0m"
    echo -e "\033[1;34m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  4)
    echo -e "\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;36m║\033[0m  \033[1;37mSCENARIO 4: Automated E2E Test Suite Execution in Podman Container\033[0m                                  \033[1;36m║\033[0m"
    echo -e "\033[1;36m║\033[0m  \033[0;33mRunning all 11 unit & multi-turn conversational flow tests inside container\033[0m                          \033[1;36m║\033[0m"
    echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
esac
echo ""
