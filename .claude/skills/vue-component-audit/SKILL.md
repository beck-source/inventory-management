---
name: vue-component-audit
description: Analyze Vue 3 component structure and produce a prioritized report of performance and code-reuse optimizations (expensive template calls, index keys, wasteful watchers, duplicated helpers, copy-pasted filter wiring, oversized components, markup that should use existing ui/ primitives), then offer to apply the fixes. Use this whenever the user asks to audit, review, analyze, optimize, refactor, clean up, or de-duplicate Vue components or views, asks why the frontend feels slow or re-renders too much, asks what could be shared or extracted into a component/composable, or wants a health check of client/src, even if they don't say "audit".
---

# Vue component audit

Find the optimizations in a Vue 3 codebase that are actually worth doing, back
each one with evidence from the code, and hand the user a short prioritized
report they can act on. Then offer to make the changes.

The value of this skill is precision. A list of 40 generic "consider using
computed" notes is noise; five confirmed findings with file:line, the reason it
matters, and a concrete fix are useful. Prefer fewer, verified findings.

## Workflow

### 1. Scope

Default to the whole frontend source (`client/src` in this repo). If the user
names files, views, or a feature, audit those, but still read the shared code
they depend on, because reuse findings depend on knowing what already exists.

### 2. Run the scanner

```bash
python3 .claude/skills/vue-component-audit/scripts/scan_vue.py client/src
```

It lists components by size and flags candidates: index keys, missing keys,
function calls in `v-for` sources, empty and deep watchers, hard-coded colors,
helpers defined in several files, repeated watch blocks, and view styles that
re-declare classes owned by `components/ui/`. Add `--json` for machine-readable
output.

Treat every hit as a lead, not a finding. The scanner is regex-based: two
functions with the same name may do different things, and a call in a template
may be trivially cheap.

### 3. Learn what already exists

Before suggesting anything be reused or extracted, read:

- The project's CLAUDE.md for conventions (here: unique `v-for` keys, design
  tokens, date validation, no emojis in UI).
- `components/ui/*` and other shared components: the primitives available.
- `composables/*` and `utils/*`: shared logic already in place.
- The root styles (`App.vue` here) for the design tokens.

A reuse suggestion that points at an existing primitive or composable is far
more useful than one that invents a new abstraction.

### 4. Verify, then look deeper

For each scanner lead, open the code and confirm it. For duplicates, compare
the function bodies and state whether they are identical or how they differ.
Drop anything that does not hold up.

Then read the largest and most central components yourself, using
`references/checklist.md` for what to look for. The checklist covers issues no
regex finds: watchers that should be computeds, refetch races, chart math in
the template, repeated markup with no primitive yet, and natural split points
for oversized components. Read it before this step.

### 5. Prioritize

Rank by real impact times confidence, and be honest about scale. This app runs
on small mock datasets, so most render-performance wins are modest today. Say
so, and explain when they would start to matter (data size, update frequency),
rather than overstating. Correctness-adjacent issues (index keys on filtered
lists, request races) and large reuse wins usually outrank micro-performance.

Use three priorities:
- **High**: causes bugs or visible slowness, or removes substantial duplication.
- **Medium**: clear improvement, moderate effort.
- **Low**: nice to have, small effect.

### 6. Report

Use this structure, so reports are easy to compare from run to run:

```markdown
# Vue component audit: <scope>

## Summary
<2-4 sentences: overall health, the biggest opportunities, rough effort.>

## Findings

| # | Priority | Category | Location | Issue |
|---|----------|----------|----------|-------|
| 1 | High | Reuse | views/Orders.vue:151 (+4 files) | `formatDate` duplicated |

### 1. <Short title>
- **Where:** `path/file.vue:line` (list every location for duplicates)
- **What:** what the code does now, quoting the relevant line or two.
- **Why it matters:** the concrete consequence.
- **Fix:** the specific change, with a short code sketch when it helps.
- **Effort:** S / M / L

## Suggested order
<Which fixes to do first and which ones group together naturally.>

## Checked and fine
<Leads you investigated and rejected, one line each, so the user knows they were looked at.>
```

Categories: Performance, Reuse, Structure, Correctness.

Show the report in chat. If it has more than about ten findings, or the user
asks for a file, also save it as `docs/vue-audit-<YYYY-MM-DD>.md`.

### 7. Offer fixes

End by asking which findings the user wants applied, suggesting a sensible
first batch. Do not edit code before they answer, because refactors touch many
files and they may want to stage them.

When applying:
- This repo's CLAUDE.md requires delegating creation or significant
  modification of `.vue` files to the `vue-expert` subagent. Give it the
  specific findings, files, and the intended end state.
- Keep behavior identical. Extracted helpers must preserve each caller's
  current output; where duplicates differed, say which variant was kept.
- Add a short comment on non-obvious changes (the why), per project style.
- Verify afterwards: run the client build (`npm run build` in `client/`),
  re-run the scanner to confirm the leads are gone, and run the test skill if
  tests cover the changed views.
