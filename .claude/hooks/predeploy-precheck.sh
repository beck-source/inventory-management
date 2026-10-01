#!/bin/bash

# Pre-deploy precheck hook for Claude Code (PreToolUse, matcher: Bash)
# Runs the frontend build before any command that actually *executes* a
# deploy-related step and blocks the command if the build fails:
#   - git push
#   - npm/pnpm/yarn run build | deploy | deploy:* | deploy-*
#   - make deploy (or a deploy-named make target)
#   - a deploy script, e.g. ./scripts/deploy.sh, bash deploy.sh, deploy-prod
# The word "deploy" in arguments, grep patterns, echo text, file names, or
# quoted/JSON strings does not trigger it. Non-deploy commands pass through.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Fallback when the command can't be parsed: the original loose match, so we
# err on the side of running the check rather than skipping it.
loose_match() {
    echo "$COMMAND" | grep -qE \
        -e '(^|[^[:alnum:]_])git[[:space:]]+push([^[:alnum:]_-]|$)' \
        -e '(^|[^[:alnum:]_])npm[[:space:]]+run[[:space:]]+build([^[:alnum:]_:-]|$)' \
        -e '(^|[^[:alnum:]_])deploy([^[:alnum:]_]|$)'
}

# Exit 0 = executes a deploy step, 1 = does not, anything else = parse error
is_deploy_command() {
    python3 - "$COMMAND" <<'PY'
import os, re, shlex, sys

SEPARATORS = {";", ";;", "&", "&&", "|", "||", "|&", "(", ")", "\n"}
WRAPPERS = {"sudo", "env", "time", "nohup", "exec", "command", "nice", "!"}
SHELLS = {"bash", "sh", "zsh", "dash", "source", "."}
INTERPRETERS = SHELLS | {"python", "python3", "node", "ruby", "perl"}
DEPLOY_NAME = re.compile(r"(^|[-_.])deploy([-_.]|$)")
DEPLOY_SCRIPT = re.compile(r"^(build|deploy([:-].*)?)$")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def tokenize(cmd):
    lex = shlex.shlex(cmd, posix=True, punctuation_chars="();<>|&\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    return list(lex)


def segments(tokens):
    seg = []
    for tok in tokens:
        if tok in SEPARATORS:
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def positional(args, takes_value=()):
    """Yield non-option arguments, skipping options and their values."""
    it = iter(args)
    for arg in it:
        if arg in (">", ">>", "<", "2>", "&>"):
            next(it, None)
        elif arg.startswith("-"):
            if arg in takes_value:
                next(it, None)
        else:
            yield arg


def is_deploy(seg, depth=0):
    # Drop leading VAR=value assignments and wrappers like sudo/env/time
    while seg and (ASSIGNMENT.match(seg[0]) or seg[0] in WRAPPERS
                   or (seg[0].startswith("-") and len(seg) > 1)):
        seg = seg[1:]
    if not seg:
        return False

    prog, args = os.path.basename(seg[0]), seg[1:]

    if prog == "git":
        sub = next(positional(args, {"-C", "-c", "--git-dir", "--work-tree",
                                     "--namespace"}), None)
        return sub == "push"

    if prog in ("npm", "pnpm", "yarn"):
        pos = list(positional(args, {"--prefix", "-C", "--dir", "--cwd",
                                     "-w", "--workspace", "--filter"}))
        if not pos:
            return False
        if pos[0] in ("run", "run-script"):
            return len(pos) > 1 and bool(DEPLOY_SCRIPT.match(pos[1]))
        # pnpm/yarn allow running scripts without "run"
        return prog != "npm" and bool(DEPLOY_SCRIPT.match(pos[0]))

    if prog == "make":
        return any(DEPLOY_NAME.search(t)
                   for t in positional(args, {"-C", "-f", "--file",
                                              "--directory"}))

    if prog in INTERPRETERS:
        if "-c" in args and prog in SHELLS:
            idx = args.index("-c") + 1
            return depth < 3 and idx < len(args) and analyze(args[idx], depth + 1)
        if any(a in ("-c", "-e", "-m") for a in args):  # inline code/module
            return False
        script = next(positional(args), None)
        return script is not None and bool(
            DEPLOY_NAME.search(os.path.basename(script)))

    return bool(DEPLOY_NAME.search(prog))


def analyze(cmd, depth=0):
    return any(is_deploy(s, depth) for s in segments(tokenize(cmd)))


try:
    sys.exit(0 if analyze(sys.argv[1]) else 1)
except ValueError:  # unbalanced quotes etc.
    sys.exit(2)
PY
}

if command -v python3 &> /dev/null; then
    is_deploy_command
    case $? in
        0) ;;
        1) exit 0 ;;
        *) loose_match || exit 0 ;;
    esac
else
    loose_match || exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CLIENT_DIR="$PROJECT_DIR/client"

# Block the command with a reason shown to Claude and the user
deny() {
    jq -n --arg reason "$1" '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: $reason
        }
    }'
    exit 0
}

if ! command -v npm &> /dev/null; then
    deny "Pre-deploy check failed: npm is not installed, so the frontend build (npm run build in client/) could not be verified. Install Node ^20.19.0 || >=22.12.0 and retry."
fi

if [ ! -d "$CLIENT_DIR/node_modules" ]; then
    deny "Pre-deploy check failed: client dependencies are not installed. Run 'cd client && npm install', then retry."
fi

BUILD_OUTPUT=$(cd "$CLIENT_DIR" && npm run build 2>&1)
BUILD_STATUS=$?

if [ $BUILD_STATUS -ne 0 ]; then
    deny "Pre-deploy check failed: 'npm run build' in client/ exited with code $BUILD_STATUS. Fix the build before running: $COMMAND

Last 30 lines of build output:
$(echo "$BUILD_OUTPUT" | tail -30)"
fi

# Build passed: exit silently so the normal permission flow still applies
exit 0
