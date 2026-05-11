#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# OrangeFi — Push CI/CD Workflows to GitHub
# ═══════════════════════════════════════════════════════════════════════════════
# Run this after creating a classic GitHub PAT with `workflow` scope:
#   https://github.com/settings/tokens/new?scopes=repo,workflow&description=orangefi-deploy
#
# Usage: PUSH_TOKEN=github_pat_xxx bash push-workflows.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

TOKEN="${PUSH_TOKEN:-}"
if [ -z "$TOKEN" ]; then
  echo "❌ Set PUSH_TOKEN=github_pat_xxx before running"
  echo "   Create a classic PAT at: https://github.com/settings/tokens/new"
  exit 1
fi

git add .github/workflows/
git commit -m "Add CI/CD workflows" || echo "Nothing to commit"
git push "https://gjiky2003:${TOKEN}@github.com/gjiky2003/orangefi.git" main

git remote set-url origin https://github.com/gjiky2003/orangefi.git
echo "✅ Workflows pushed! Remote cleaned."
