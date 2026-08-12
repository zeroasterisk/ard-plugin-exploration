#!/usr/bin/env bash
# Reset scenario environment and render clean 5-step basics headers

STEP="${1:-0}"

if [ "$STEP" -le 1 ]; then
  clear
  rm -f .config/opencode_session_active /tmp/opencode_session_active
  rm -rf .config/ard .config/gcloud
  mkdir -p .config/gcloud .config/ard
  cat << 'EOF' > .config/gcloud/application_default_credentials.json
{
  "account": "developer@example.com",
  "client_id": "764086051850-sample.apps.googleusercontent.com",
  "client_secret": "[REDACTED_CLIENT_SECRET]",
  "quota_project_id": "my-developer-project",
  "refresh_token": "1//04_SAMPLE_ACTIVE_TOKEN",
  "type": "authorized_user",
  "universe_domain": "googleapis.com"
}
EOF
fi

case "$STEP" in
  0)
    echo -e "\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;36m║\033[0m            \033[1;37mAGENT RESOURCE DISCOVERY (ARD v0.5) • 5-STEP BASICS WALKTHROUGH\033[0m                     \033[1;36m║\033[0m"
    echo -e "\033[1;36m║\033[0m       \033[0;33mSingle Continuous Session: OpenCode Discovers, Evaluates, Installs & Uses Skills\033[0m        \033[1;36m║\033[0m"
    echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  1)
    echo -e "\033[1;32m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[1;37mSTEP 1: The Agent Environment (Here's OpenCode)\033[0m                                                      \033[1;32m║\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[0;33mOpenCode agent initializes in clean workspace with the canonical ARD discovery tool loaded\033[0m           \033[1;32m║\033[0m"
    echo -e "\033[1;32m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  2)
    echo -e "\033[1;34m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[1;37mSTEP 2: Capability Search (Here's How It Searches via ARD)\033[0m                                           \033[1;34m║\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[0;33mDeveloper asks high-level query -> OpenCode autonomously calls ard_search\033[0m                            \033[1;34m║\033[0m"
    echo -e "\033[1;34m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  3)
    echo -e "\033[1;35m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[1;37mSTEP 3: AI Catalog Lookup (Here's How It Finds What It Wants)\033[0m                                        \033[1;35m║\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[0;33mOpenCode inspects ai-catalog.json manifest via ard_get_resource to check capabilities & tier\033[0m         \033[1;35m║\033[0m"
    echo -e "\033[1;35m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  4)
    echo -e "\033[1;33m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;33m║\033[0m  \033[1;37mSTEP 4: Plugin Setup & Enablement (Here's How It Installs / Loads the Plugin)\033[0m                        \033[1;33m║\033[0m"
    echo -e "\033[1;33m║\033[0m  \033[0;33mOpenCode enables and registers the skill in the active multi-turn session\033[0m                            \033[1;33m║\033[0m"
    echo -e "\033[1;33m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  5)
    echo -e "\033[1;32m╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[1;37mSTEP 5: Normal Execution (Here's How It Uses the Plugin to Solve Tasks)\033[0m                              \033[1;32m║\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[0;33mOpenCode applies the loaded domain rules directly to generate the optimal schema & partition plan\033[0m     \033[1;32m║\033[0m"
    echo -e "\033[1;32m╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
esac
