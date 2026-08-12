#!/usr/bin/env bash
# Helper script to emulate the human OAuth browser step with redacted secrets in the terminal recording
set -e

mkdir -p .config/gcloud
REFRESH_TOKEN="${GCLOUD_REFRESH_TOKEN:-1//04_REDACTED_OAUTH_TOKEN}"
CLIENT_SECRET="${GCLOUD_CLIENT_SECRET:-[REDACTED_CLIENT_SECRET]}"

cat << CREDS_EOF > .config/gcloud/application_default_credentials.json
{
  "account": "",
  "client_id": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
  "client_secret": "$CLIENT_SECRET",
  "quota_project_id": "alanblount-sandbox",
  "refresh_token": "$REFRESH_TOKEN",
  "type": "authorized_user",
  "universe_domain": "googleapis.com"
}
CREDS_EOF

echo "Go to the following link in your browser, and complete the sign-in prompts:"
echo ""
echo "    https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=[REDACTED_CLIENT_ID]...&redirect_uri=https%3A%2F%2Fsdk.cloud.google.com%2Fapplicationdefaultauthcode.html&scope=openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform&state=[REDACTED]&prompt=consent&access_type=offline"
echo ""
sleep 0.8
echo -n "Enter verification code: "
sleep 0.5
echo "4/0AXEQxID[REDACTED_OAUTH_CODE]"
sleep 0.4
echo ""
echo "Credentials saved to file: [/workspace/.config/gcloud/application_default_credentials.json]"
echo ""
echo "These credentials will be used by any library that requests Application Default Credentials (ADC)."
echo "Quota project \"alanblount-sandbox\" was added to ADC which can be used by Google client libraries for billing and quota."
