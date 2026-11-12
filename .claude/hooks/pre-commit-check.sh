#!/bin/bash
# PreToolUse hook (Bash, only for `git commit`): enforce code standards before committing.
# Blocks the commit (exit 2, reason on stderr is fed back to Claude) if:
#   - staged client/ files fail `prettier --check`
#   - staged changes contain obvious credentials or a private npm registry URL (repo is PUBLIC)

ROOT="${CLAUDE_PROJECT_DIR}"
cd "$ROOT" || exit 0

FAILED=0

# 1. Prettier check on staged files under client/ (added/copied/modified only).
STAGED_CLIENT=$(git diff --cached --name-only --diff-filter=ACM -- client/ | grep -v '^client/node_modules/' | sed 's#^client/##')
if [ -n "$STAGED_CLIENT" ]; then
  # Run from client/ so .prettierrc.json and the local prettier install are used.
  OUT=$(cd client && echo "$STAGED_CLIENT" | tr '\n' '\0' | xargs -0 npx --no-install prettier --check --ignore-unknown 2>&1)
  if [ $? -ne 0 ]; then
    echo "Pre-commit: Prettier check failed for staged client files:" >&2
    echo "$OUT" | grep '\[warn\]' >&2
    echo "Fix with: cd client && npx prettier --write <files>, then re-stage." >&2
    FAILED=1
  fi
fi

# 2. Secret / private-registry scan on added lines of the staged diff.
#    Prints only file names, never the matching values.
PATTERN='(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|_authToken=|(api[_-]?key|secret|password)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"']{8,})'
# This script is excluded: its own PATTERN line would otherwise match itself.
HITS=$(git diff --cached --name-only --diff-filter=ACM | grep -vx '.claude/hooks/pre-commit-check.sh' | while read -r f; do
  git diff --cached -U0 -- "$f" | grep '^+' | grep -v '^+++' | grep -qiE "$PATTERN" && echo "$f"
done)
if [ -n "$HITS" ]; then
  echo "Pre-commit: possible credentials in staged changes (this repo is PUBLIC):" >&2
  echo "$HITS" | sed 's/^/  /' >&2
  FAILED=1
fi

# 3. Guard files CLAUDE.md says must stay as-is / out of git.
if git diff --cached --name-only | grep -qx 'client/package-lock.json'; then
  echo "Pre-commit: client/package-lock.json must not be committed (see CLAUDE.md)." >&2
  FAILED=1
fi

[ "$FAILED" -eq 1 ] && exit 2
exit 0
