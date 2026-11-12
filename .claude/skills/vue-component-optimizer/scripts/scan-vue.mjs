#!/usr/bin/env node
// Zero-dependency heuristic scanner for Vue 3 SFCs.
// Produces leads for the vue-component-optimizer skill; every lead must be
// confirmed by reading the code - regexes cannot understand templates fully.
//
// Usage: node scan-vue.mjs <file-or-dir> [more paths...] [--json]

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, extname } from 'node:path'

const args = process.argv.slice(2)
const asJson = args.includes('--json')
const targets = args.filter(a => a !== '--json')
if (targets.length === 0) {
  console.error('Usage: node scan-vue.mjs <file-or-dir> [...] [--json]')
  process.exit(1)
}

const LARGE_FILE_LINES = 400

function collectVueFiles(path, out = []) {
  const st = statSync(path)
  if (st.isFile()) {
    if (extname(path) === '.vue') out.push(path)
    return out
  }
  for (const entry of readdirSync(path)) {
    if (entry === 'node_modules' || entry.startsWith('.')) continue
    collectVueFiles(join(path, entry), out)
  }
  return out
}

// Extract a top-level SFC block; returns { content, startLine } or null.
function block(src, tag) {
  const re = new RegExp(`<${tag}(\\s[^>]*)?>([\\s\\S]*?)</${tag}>`)
  const m = re.exec(src)
  if (!m) return null
  const startLine = src.slice(0, m.index).split('\n').length
  return { attrs: m[1] || '', content: m[2], startLine }
}

// Template blocks can nest <template>; take outermost by matching the last closing tag.
function templateBlock(src) {
  const open = src.search(/<template(\s[^>]*)?>/)
  const close = src.lastIndexOf('</template>')
  if (open === -1 || close === -1) return null
  const openEnd = src.indexOf('>', open) + 1
  return { content: src.slice(openEnd, close), startLine: src.slice(0, open).split('\n').length }
}

function lineHits(text, startLine, regex) {
  const hits = []
  text.split('\n').forEach((line, i) => {
    if (regex.test(line)) hits.push({ line: startLine + i, text: line.trim().slice(0, 140) })
  })
  return hits
}

// Normalize a CSS rule body so formatting differences don't hide duplicates.
function normalizeCss(body) {
  return body
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .split(';')
    .map(d => d.trim().replace(/\s+/g, ' '))
    .filter(Boolean)
    .sort()
    .join(';')
}

function cssRules(style) {
  const rules = []
  if (!style) return rules
  // Flat rules only (selector { decls }); skips @media wrappers' outer braces.
  const re = /([^{}@]+)\{([^{}]*)\}/g
  let m
  while ((m = re.exec(style.content))) {
    const selector = m[1].trim().replace(/\s+/g, ' ')
    const body = normalizeCss(m[2])
    if (body.split(';').length < 3) continue // ignore tiny rules - too noisy
    const line = style.startLine + style.content.slice(0, m.index).split('\n').length
    rules.push({ selector, body, line })
  }
  return rules
}

function analyze(file, root) {
  const src = readFileSync(file, 'utf8')
  const rel = relative(process.cwd(), file)
  const lines = src.split('\n').length
  const tpl = templateBlock(src)
  const script = block(src, 'script')
  const style = block(src, 'style')

  let scriptStyle = 'none'
  if (script) {
    if (/\bsetup\b/.test(script.attrs)) scriptStyle = 'script-setup'
    else if (/\bsetup\s*\(/.test(script.content)) scriptStyle = 'setup()'
    else if (/\b(data|methods|computed)\s*[:(]/.test(script.content)) scriptStyle = 'options-api'
    else scriptStyle = 'other'
  }

  const issues = []
  const add = (check, hits, note) => hits.forEach(h => issues.push({ check, note, ...h }))

  if (tpl) {
    add('P1', lineHits(tpl.content, tpl.startLine, /:key="\s*(index|idx|i)\s*"/), 'v-for keyed by index')
    // v-for elements without a :key on the same line (multi-line tags may false-positive)
    add('P1', lineHits(tpl.content, tpl.startLine, /v-for="(?![^"]*"[^>]*:key)[^"]*"(?![^>]*:key)[^>]*>/), 'v-for without :key on same line (verify)')
    add('P4', lineHits(tpl.content, tpl.startLine, /v-for="[^"]*"[^>]*v-if=|v-if="[^"]*"[^>]*v-for=/), 'v-if and v-for on same element')
    // Calls in interpolations. Built-in method calls (.toFixed(), Math.round())
    // and the i18n t() helper are ignored. Formatter-style calls (format*,
    // translate*, money*) are cheap and pure, so they are only counted.
    // Anything else - especially getX(...).length - is reported, since it
    // usually means filtering/searching on every render.
    const CHEAP = /^(t|format\w*|translate\w*|money\w*)$/
    let cheapCount = 0
    tpl.content.split('\n').forEach((line, i) => {
      for (const interp of line.matchAll(/\{\{([^}]*)\}\}/g)) {
        for (const call of interp[1].matchAll(/(^|[^.\w$])([a-zA-Z_$][\w$]*)\s*\(/g)) {
          const name = call[2]
          if (name === 'Math' || name === 'String' || name === 'Number') continue
          if (CHEAP.test(name)) { cheapCount++; continue }
          const lengthOfResult = /\)\s*\.length/.test(interp[1])
          issues.push({
            check: 'P2',
            line: tpl.startLine + i,
            note: lengthOfResult ? `${name}() result's .length in template (likely a filter per render)` : `${name}() called in interpolation`,
            text: line.trim().slice(0, 140),
          })
        }
      }
    })
    if (cheapCount) issues.push({ check: 'P2', line: tpl.startLine, note: `${cheapCount} formatter/translate call(s) in template (usually fine; matters only inside large v-for lists)`, text: '' })
    add('P3', lineHits(tpl.content, tpl.startLine, /\.(filter|sort|find|reduce|map)\(/), 'array operation inside template')
  }
  if (script) {
    add('P5', lineHits(script.content, script.startLine, /deep:\s*true/), 'deep watcher')
    const listeners = (script.content.match(/addEventListener\(/g) || []).length
    const removals = (script.content.match(/removeEventListener\(/g) || []).length
    if (listeners > removals) {
      add('S4', lineHits(script.content, script.startLine, /addEventListener\(/), `addEventListener (${listeners}) without matching removeEventListener (${removals})`)
    }
    const timers = /set(Interval|Timeout)\(/.test(script.content) && !/clear(Interval|Timeout)\(/.test(script.content)
    if (timers) add('S4', lineHits(script.content, script.startLine, /set(Interval|Timeout)\(/), 'timer without clear*')
  }
  if (lines > LARGE_FILE_LINES) issues.push({ check: 'S2', line: 1, note: `large component (${lines} lines)`, text: '' })

  // Facts for cross-file duplication detection
  const watchSources = script
    ? [...script.content.matchAll(/watch\(\s*(\[[^\]]+\])/g)].map(m => m[1].replace(/\s+/g, ''))
    : []
  const functionNames = script
    ? [...script.content.matchAll(/(?:const|function)\s+([a-zA-Z_$][\w$]*)\s*=?\s*(?:\([^)]*\)\s*=>|function|\()/g)].map(m => m[1])
    : []

  return {
    file: rel,
    lines,
    scriptStyle,
    issues,
    _css: cssRules(style),
    _watchSources: watchSources,
    _functionNames: functionNames,
  }
}

function crossFile(results) {
  const dup = []

  // Identical CSS rule bodies under the same selector in 2+ files
  const css = new Map()
  for (const r of results) for (const rule of r._css) {
    const k = `${rule.selector}::${rule.body}`
    if (!css.has(k)) css.set(k, [])
    css.get(k).push(`${r.file}:${rule.line}`)
  }
  for (const [k, locs] of css) {
    if (new Set(locs.map(l => l.split(':')[0])).size >= 2) {
      dup.push({ check: 'R5', note: `identical CSS rule "${k.split('::')[0]}"`, locations: locs })
    }
  }

  // Same watch([...]) source list in 2+ files -> shared data-loading composable
  const watches = new Map()
  for (const r of results) for (const w of r._watchSources) {
    if (!watches.has(w)) watches.set(w, [])
    watches.get(w).push(r.file)
  }
  for (const [w, files] of watches) {
    if (files.length >= 2) dup.push({ check: 'R2', note: `same watch sources ${w}`, locations: files })
  }

  // Same helper function name in 2+ files (likely duplicated helper)
  const ignore = new Set(['setup', 'load', 'loadData', 'close', 'open', 'handleClose', 't'])
  const fns = new Map()
  for (const r of results) for (const f of new Set(r._functionNames)) {
    if (ignore.has(f)) continue
    if (!fns.has(f)) fns.set(f, [])
    fns.get(f).push(r.file)
  }
  for (const [f, files] of fns) {
    if (files.length >= 2) dup.push({ check: 'R1', note: `function "${f}" defined in ${files.length} files`, locations: files })
  }

  return dup.sort((a, b) => b.locations.length - a.locations.length)
}

const files = targets.flatMap(t => collectVueFiles(t))
const results = files.map(f => analyze(f))
const duplication = crossFile(results)

if (asJson) {
  const clean = results.map(({ _css, _watchSources, _functionNames, ...r }) => r)
  console.log(JSON.stringify({ files: clean, duplication }, null, 2))
  process.exit(0)
}

console.log(`Scanned ${results.length} .vue file(s)\n`)
console.log('FILE'.padEnd(50), 'LINES'.padStart(6), ' SCRIPT'.padEnd(15), 'LEADS')
for (const r of [...results].sort((a, b) => b.lines - a.lines)) {
  console.log(r.file.padEnd(50), String(r.lines).padStart(6), ' ' + r.scriptStyle.padEnd(14), r.issues.length)
}

const styles = new Set(results.map(r => r.scriptStyle))
if (styles.size > 1) console.log(`\n[S1] mixed script styles: ${[...styles].join(', ')}`)

console.log('\n== Per-file leads ==')
for (const r of results) {
  if (!r.issues.length) continue
  console.log(`\n${r.file}`)
  for (const i of r.issues) console.log(`  [${i.check}] L${i.line} ${i.note}${i.text ? `: ${i.text}` : ''}`)
}

console.log('\n== Cross-file duplication leads ==')
if (!duplication.length) console.log('  none')
for (const d of duplication) {
  console.log(`\n  [${d.check}] ${d.note}`)
  for (const l of d.locations) console.log(`      ${l}`)
}
