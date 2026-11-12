#!/bin/bash
# PostToolUse hook (Edit|Write): run Prettier on the edited file when it lives in client/.
# Never blocks: formatting failures are reported to stderr but exit 0.

FILE=$(jq -r '.tool_response.filePath // .tool_input.file_path // empty')
CLIENT_DIR="${CLAUDE_PROJECT_DIR}/client"

# Only format files inside client/ (where prettier is installed); skip node_modules.
case "$FILE" in
  "$CLIENT_DIR"/node_modules/*) exit 0 ;;
  "$CLIENT_DIR"/*) ;;
  *) exit 0 ;;
esac

cd "$CLIENT_DIR" || exit 0
# --ignore-unknown skips file types Prettier can't parse instead of erroring.
npx --no-install prettier --write --ignore-unknown --log-level warn "$FILE" >&2 || true
exit 0
