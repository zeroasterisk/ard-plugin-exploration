# Google Resource Discovery & Auth Progressive Disclosure Rules

1. **Never Assume GCP Credentials**: Always check resource auth requirements (`tier`, `auth_ready`) before instructing the user to run live GCP queries.
2. **Prioritize Zero-Auth Solutions for General Questions**: If the user is asking conceptual, code design, or architecture questions, always lead with Tier 0 Skills (e.g. `well-architected`, `bigquery-guidelines`, `cloud-run-architecture`) which require zero auth.
3. **Respect User Opt-Outs**: If the user indicates they do not want to use Google Cloud or sign up for an account, permanently respect their preference and only return Tier 0/1 capabilities.
4. **Actionable Onboarding**: When a Tier 2 tool is genuinely the best option (e.g. live database query or cloud deployment), provide clear instructions (`gcloud auth application-default login`) alongside the free-tier details.
