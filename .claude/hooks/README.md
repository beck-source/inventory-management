# Claude Code Hooks

This directory contains hooks for Claude Code that automate tasks during development.

## Available Hooks

### 1. Post Tool Use Logger (`post-tool-use.sh`)

**Purpose**: Logs all tool usage to help with debugging and tracking Claude's actions.

**Trigger**: Runs after every tool call (Read, Write, Edit, Bash, etc.)

**Configuration**: Enabled in `.claude/settings.local.json` under the `hooks.PostToolUse` section.

**Log Location**: `.claude/logs/tool-usage-YYYY-MM-DD.log`

**Log Format**:
```
=== Tool Usage: 2025-10-16 09:15:23 ===
Tool: Read
Session: abc123
Input: {"file_path": "/path/to/file.js"}
Response: {"content": "..."}
```

**Features**:
- Creates daily log files with timestamps
- Uses `jq` for clean JSON parsing (falls back to raw logging if jq is not installed)
- Logs tool name, session ID, input parameters, and response
- Never blocks tool execution

**Usage**:
The hook runs automatically once configured. To view logs:
```bash
# View today's log
cat .claude/logs/tool-usage-$(date +%Y-%m-%d).log

# View logs with live updates
tail -f .claude/logs/tool-usage-$(date +%Y-%m-%d).log

# Search logs for specific tool
grep "Tool: Bash" .claude/logs/*.log
```

**Requirements**:
- Optional: `jq` for better JSON formatting (`brew install jq` on macOS)

### 2. User Prompt Submit Hook (`user-prompt-submit.sh`)

**Purpose**: Runs pre-commit linting checks when Claude creates commits.

**Trigger**: Runs when the user's prompt contains "commit" or "git commit"

**Features**:
- Lints Python files with `ruff`
- Lints JavaScript/Vue files with `eslint`
- Blocks commits if linting fails

### 3. Pre-Deploy Build Check (`predeploy-precheck.sh`)

**Purpose**: Runs the frontend build before deploy-related commands and blocks them if the build fails.

**Trigger**: `PreToolUse` on `Bash`. Acts only when the command actually *executes* a deploy step, in any part of a `;`/`&&`/`||`/`|` chain or a `bash -c "..."` string:
- `git push` (including `git -C dir push`)
- `npm`/`pnpm`/`yarn` running the `build`, `deploy`, `deploy:*`, or `deploy-*` script
- `make deploy`
- a deploy script, e.g. `./scripts/deploy.sh`, `bash deploy.sh`, `deploy-prod`

Mentions of these in arguments, grep patterns, echo text, commit messages, file names, or JSON strings (e.g. `grep "deploy"`, `cat deploy.sh`, `echo git push`) do not trigger it. The command is tokenized with Python's `shlex`; if `python3` is missing or the command can't be parsed, the hook falls back to a loose text match so a deploy is never silently skipped.

**Configuration**: Registered in `.claude/settings.json` under `hooks.PreToolUse`.

**Behavior**:
- Runs `npm run build` in `client/` (timeout 300s)
- On failure, denies the command and shows the exit code plus the last 30 lines of build output
- Also blocks, with an explanation, if `npm` is missing or `client/node_modules` is not installed
- On success, exits silently so the normal permission prompts still apply

**Requirements**: `jq`, Node/npm, `python3` (for command parsing)

## Disabling Hooks

To temporarily disable a hook, you can:

1. **Comment out in settings**: Edit `.claude/settings.local.json` and remove the hook configuration
2. **Remove execute permission**: `chmod -x .claude/hooks/post-tool-use.sh`
3. **Delete the hook file**: `rm .claude/hooks/post-tool-use.sh`

## Creating Custom Hooks

See the [Claude Code Hooks Documentation](https://docs.claude.com/en/docs/claude-code/hooks.md) for more information on creating custom hooks.

### Available Hook Events:
- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution
- `UserPromptSubmit` - When user submits a prompt
- `Stop` - When agent finishes responding
- `SubagentStop` - When subagent finishes
- `SessionStart` - When session starts
- `SessionEnd` - When session ends

### Hook Exit Codes:
- `0` - Success, allow action to proceed
- `2` - Block action and show error message
- Other non-zero - Error occurred

## Troubleshooting

**Hook not running?**
- Check that the hook file is executable: `ls -l .claude/hooks/`
- Verify configuration in `.claude/settings.local.json`
- Check Claude Code logs for errors

**Permission errors?**
- Ensure the hook script has execute permissions: `chmod +x .claude/hooks/*.sh`

**Can't find logs?**
- Logs are created in `.claude/logs/` directory
- Check that `CLAUDE_PROJECT_DIR` environment variable is set correctly
- Try running the hook manually to test: `./.claude/hooks/post-tool-use.sh`
