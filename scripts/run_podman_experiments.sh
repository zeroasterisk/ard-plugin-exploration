#!/usr/bin/env bash
set -euo pipefail

echo "================================================================================"
echo "🚀 Running ARD Google Discovery E2E Podman Experiments"
echo "================================================================================"

python3 "$(dirname "$0")/../tests/e2e_podman_runner.py"
