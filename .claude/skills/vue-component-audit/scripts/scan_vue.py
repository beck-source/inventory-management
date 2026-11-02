#!/usr/bin/env python3
"""Inventory a Vue 3 codebase and flag candidate performance / reuse issues.

Every hit is a *candidate*: the caller is expected to read the code and confirm
it before reporting. The scanner is deliberately regex-based (stdlib only) so it
runs anywhere without installing a parser; that makes it fast but imprecise.

Usage: python3 scan_vue.py [SRC_DIR] [--json]
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

LARGE_FILE_LINES = 400
LARGE_TEMPLATE_LINES = 200

# `v-for="(x, i) in xs" :key="i"` -- index keys break identity when the list
# is filtered or reordered, which this app's filters do constantly.
VFOR_RE = re.compile(r'v-for="\s*\(?\s*([\w$]+)\s*(?:,\s*([\w$]+))?\s*\)?\s+(?:in|of)\s+([^"]+)"')
KEY_RE = re.compile(r':key="([^"]+)"')
# Function calls in the v-for source re-run on every render; a computed caches.
CALL_IN_SOURCE_RE = re.compile(r'[\w$.]+\s*\(')
FUNC_DEF_RE = re.compile(
    r'^\s*(?:export\s+)?(?:const|let|function)\s+([a-zA-Z_$][\w$]*)\s*(?:=\s*(?:async\s*)?\(|=\s*(?:async\s+)?[\w$]+\s*=>|\()',
    re.M,
)
HEX_RE = re.compile(r'#[0-9a-fA-F]{3,8}\b')
WATCH_RE = re.compile(r'watch\(\s*\[([^\]]*)\]')
EMPTY_WATCH_RE = re.compile(r'watch\(\s*[^,]+,\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)')
DEEP_WATCH_RE = re.compile(r'deep\s*:\s*true')
TOKEN_BLOCK_RE = re.compile(r'(?::root|\[data-theme[^\]]*\])[^{]*\{[^}]*\}')
STYLE_CLASS_RE = re.compile(r'^\s*\.([a-zA-Z][\w-]*)\s*[,{]', re.M)


def section(text, tag):
    """Return (start_line, body) of the first <tag ...> block, or (0, '')."""
    m = re.search(rf'<{tag}\b[^>]*>(.*?)</{tag}>', text, re.S)
    if not m:
        return 0, ''
    return text[: m.start(1)].count('\n') + 1, m.group(1)


def template_body(text):
    # Root <template> can contain nested <template> tags, so take the span from
    # the first opening tag to the last closing one instead of the first match.
    start = text.find('<template')
    end = text.rfind('</template>')
    if start == -1 or end == -1:
        return 0, ''
    open_end = text.find('>', start) + 1
    return text[:open_end].count('\n') + 1, text[open_end:end]


def scan_file(path, src):
    text = path.read_text(encoding='utf-8')
    rel = str(path.relative_to(src))
    findings = []
    lines = text.count('\n') + 1

    t_start, tmpl = template_body(text)
    s_start, script = section(text, 'script')
    _, style = section(text, 'style')
    tmpl_lines = tmpl.count('\n')

    if lines > LARGE_FILE_LINES or tmpl_lines > LARGE_TEMPLATE_LINES:
        findings.append({
            'kind': 'large-component', 'file': rel, 'line': 1,
            'detail': f'{lines} lines total, template ~{tmpl_lines} lines',
        })

    for i, line in enumerate(tmpl.split('\n')):
        lineno = t_start + i
        m = VFOR_RE.search(line)
        if not m:
            continue
        item, idx, source = m.group(1), m.group(2), m.group(3).strip()
        # :key is often on the next line in multi-line tags; look a few ahead.
        window = '\n'.join(tmpl.split('\n')[i:i + 4])
        key = KEY_RE.search(window)
        if not key:
            findings.append({'kind': 'vfor-missing-key', 'file': rel, 'line': lineno,
                             'detail': f'v-for over `{source}` has no :key'})
        elif idx and key.group(1).strip() == idx:
            findings.append({'kind': 'vfor-index-key', 'file': rel, 'line': lineno,
                             'detail': f'v-for over `{source}` keyed by index `{idx}`'})
        if CALL_IN_SOURCE_RE.search(source):
            findings.append({'kind': 'vfor-call-in-source', 'file': rel, 'line': lineno,
                             'detail': f'v-for source `{source}` is a call; recomputed every render'})

    for m in EMPTY_WATCH_RE.finditer(script):
        findings.append({'kind': 'empty-watcher', 'file': rel,
                         'line': s_start + script[: m.start()].count('\n'),
                         'detail': 'watch() with an empty callback does nothing'})
    for m in DEEP_WATCH_RE.finditer(script):
        findings.append({'kind': 'deep-watch', 'file': rel,
                         'line': s_start + script[: m.start()].count('\n'),
                         'detail': 'deep watcher traverses the whole object on every change'})

    # Token definitions (:root / theme selectors) are where hex values belong;
    # only count colors hard-coded into component rules.
    rules = TOKEN_BLOCK_RE.sub('', style)
    hexes = HEX_RE.findall(rules)
    if hexes:
        findings.append({'kind': 'hardcoded-colors', 'file': rel, 'line': 1,
                         'detail': f'{len(hexes)} hex colors in <style> ({", ".join(sorted(set(hexes))[:5])})'})

    funcs = [m.group(1) for m in FUNC_DEF_RE.finditer(script)]
    watches = [re.sub(r'\s+', '', w) for w in WATCH_RE.findall(script)]
    classes = set(STYLE_CLASS_RE.findall(style))
    return {
        'file': rel, 'lines': lines, 'template_lines': tmpl_lines,
        'functions': funcs, 'watch_sources': watches, 'style_classes': sorted(classes),
        'findings': findings,
    }


def cross_file(results):
    """Find logic and styling repeated across files -- the code-reuse signal."""
    findings = []
    by_func = defaultdict(list)
    for r in results:
        for f in set(r['functions']):
            by_func[f].append(r['file'])
    # Lifecycle-ish names recur by convention, not duplication.
    ignore = {'setup', 'loadData', 'fetchData', 'handleClose', 'close', 'onClose', 't'}
    for name, files in sorted(by_func.items()):
        if len(files) > 1 and name not in ignore:
            findings.append({'kind': 'duplicate-function', 'file': files[0], 'line': 1,
                             'detail': f'`{name}` defined in {len(files)} files: {", ".join(files)}'})

    by_watch = defaultdict(list)
    for r in results:
        for w in r['watch_sources']:
            by_watch[w].append(r['file'])
    for sources, files in by_watch.items():
        if len(files) > 1:
            findings.append({'kind': 'repeated-watch-pattern', 'file': files[0], 'line': 1,
                             'detail': f'watch([{sources}]) repeated in {len(files)} files: {", ".join(files)}'})

    # Classes that a shared ui/ primitive owns but other files restyle locally.
    ui = [r for r in results if '/ui/' in f'/{r["file"]}']
    ui_classes = {c: r['file'] for r in ui for c in r['style_classes']}
    for r in results:
        if r in ui:
            continue
        overlap = sorted(c for c in r['style_classes'] if c in ui_classes)
        if overlap:
            findings.append({'kind': 'restyles-ui-primitive', 'file': r['file'], 'line': 1,
                             'detail': f'defines classes owned by ui/ primitives: {", ".join(overlap)}'})
    return findings


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    src = Path(args[0] if args else 'client/src').resolve()
    if not src.is_dir():
        sys.exit(f'not a directory: {src}')
    files = sorted(p for p in src.rglob('*.vue') if 'node_modules' not in p.parts)
    results = [scan_file(p, src) for p in files]
    findings = [f for r in results for f in r['findings']] + cross_file(results)

    if '--json' in sys.argv:
        print(json.dumps({'src': str(src), 'files': results, 'findings': findings}, indent=2))
        return

    print(f'# Vue scan: {src}  ({len(files)} components)\n')
    print('## Components by size')
    for r in sorted(results, key=lambda r: -r['lines']):
        print(f'{r["lines"]:5d}  {r["file"]}  (template ~{r["template_lines"]})')
    print('\n## Candidate findings (verify each before reporting)')
    by_kind = defaultdict(list)
    for f in findings:
        by_kind[f['kind']].append(f)
    for kind, items in sorted(by_kind.items()):
        print(f'\n### {kind} ({len(items)})')
        for f in items:
            print(f'- {f["file"]}:{f["line"]}  {f["detail"]}')


if __name__ == '__main__':
    main()
