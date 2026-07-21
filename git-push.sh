#!/bin/bash
# =============================================================================
# Push nepal_decarb_pro to GitHub (Path B — you push yourself)
# =============================================================================
# Usage:
#   1. Create an empty repo on GitHub: https://github.com/new
#      - Name: nepal-decarb-pro
#      - Public
#      - DO NOT init with README, .gitignore, or license
#   2. Run this script:
#      ./git-push.sh https://github.com/YOUR_USERNAME/nepal-decarb-pro.git
# =============================================================================
set -euo pipefail

REPO_URL="${1:-}"
if [ -z "$REPO_URL" ]; then
  echo "Usage: $0 <github-repo-url>"
  echo "Example: $0 https://github.com/john-doe/nepal-decarb-pro.git"
  echo
  echo "First, create the empty repo at: https://github.com/new"
  exit 1
fi

# Use SSH if user provided it, else HTTPS
if [[ "$REPO_URL" == git@* ]]; then
  REMOTE_URL="$REPO_URL"
else
  REMOTE_URL="$REPO_URL"
fi

# We're in /workspace/nepal-decarb which already has .git/
cd "$(dirname "$0")"

echo "============================================"
echo " Pushing nepal_decarb_pro to GitHub"
echo " Remote: $REMOTE_URL"
echo "============================================"

# Check git status
if [ ! -d .git ]; then
  echo "ERROR: no .git directory. Are you in the project root?"
  exit 1
fi

# Add the new files (render.yaml, railway.json, fly.toml, docs-site/, etc.)
git add .github/ README.md LICENSE LICENSE-DATA CITATION.cff CONTRIBUTING.md CODE_OF_CONDUCT.md render.yaml railway.json fly.toml docs-site/

# Commit
git commit -m "Add GitHub package: README, CI, deploy configs, Pages demo

- Top-level README with badges, quick start, deployment options
- GitHub Actions CI: test on Python 3.10/3.11/3.12, build Docker images, deploy to Pages
- GitHub Actions release: auto-create release on tag push
- Issue templates: bug report, feature request, plant onboarding
- PR template, CODEOWNERS
- Render.com blueprint (render.yaml) — one-click free deploy
- Railway.json + fly.toml for alternative free deploys
- docs-site/ with full interactive platform explorer (auto-deployed to GitHub Pages)"

# Add remote
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE_URL"

# Rename branch to main (GitHub default)
git branch -M main

# Push everything
echo
echo "Pushing code, commits, and tags..."
git push -u origin main --tags --force

echo
echo "============================================"
echo " DONE"
echo "============================================"
echo
echo "Next steps:"
echo "  1. Go to https://github.com/$(basename $REPO_URL .git | sed 's|/||g')/settings/pages"
echo "     - Source: 'Deploy from a branch'"
echo "     - Branch: main, Folder: /docs-site"
echo "     - Click Save"
echo "     Your demo will be live at: https://YOUR_USERNAME.github.io/nepal-decarb-pro/"
echo
echo "  2. Go to https://render.com/deploy?repo=$REPO_URL"
echo "     - Click 'Apply' to deploy from render.yaml"
echo "     - Free tier: API + DB + static site"
echo
echo "  3. (Optional) Go to https://fly.io to deploy via fly.toml"
echo
echo "Revoke the token you used to push (if you used one):"
echo "  https://github.com/settings/tokens"
