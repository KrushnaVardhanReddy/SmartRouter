#!/bin/bash

# ──────────────────────────────────────────────────────────────────────────────
# merge_prs.sh — Batch merge Jules-generated PRs for Local AI Assistant
#
# Usage:
#   bash scripts/merge_prs.sh <start_pr> <end_pr>
#   bash scripts/merge_prs.sh 1 5
# ──────────────────────────────────────────────────────────────────────────────

REPO_ROOT=$(dirname "$(dirname "$(readlink -f "$0")")")
cd "$REPO_ROOT" || exit 1

# Load environment variables
if [ -f ".env.local" ]; then
    set -a
    source .env.local
    set +a
fi

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <start_pr_number> <end_pr_number>"
    echo "Example: $0 1 5   (merges PRs #1 through #5)"
    exit 1
fi

if ! command -v gh &>/dev/null; then
    echo "❌ GitHub CLI (gh) not installed. Run: sudo apt install gh"
    exit 1
fi

START_PR=$1
END_PR=$2
MERGED=0
FAILED=0

echo "🔀 Batch merging Jules PRs #$START_PR → #$END_PR into branch: main"
echo "──────────────────────────────────────────────────────"

for pr in $(seq $START_PR $END_PR); do
    echo "📌 Processing PR #$pr..."

    # Mark ready if still a draft
    gh pr ready "$pr" >/dev/null 2>&1 || true

    # Squash merge and delete remote branch
    if gh pr merge "$pr" --squash --delete-branch 2>/dev/null; then
        echo "  ✅ Merged PR #$pr"
        ((MERGED++))
    else
        echo "  ❌ Failed PR #$pr (already merged, closed, or merge conflict)"
        ((FAILED++))
    fi
    echo "──────────────────────────────────────────────────────"
done

echo ""
echo "🎉 Done! Merged: $MERGED | Failed/Skipped: $FAILED"
echo "📥 Run: git pull origin main   to sync your local branch."
