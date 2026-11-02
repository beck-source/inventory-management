---
name: redesign-saas-ui
description: Redesign the Vue 3 UI into a modern SaaS layout — left sidebar nav, consistent spacing scale, polished shared primitives. Use when the user asks to redesign the UI, give it a modern SaaS look, replace the top nav with a sidebar, or similar.
disable-model-invocation: true
---

# Redesign to modern SaaS UI

Transforms this Vue 3 app from a demo top-nav look into a sidebar-first SaaS interface. Target aesthetic: restrained, slate-palette, dense but breathable — Linear / Vercel / Attio family. The redesign is opinionated: every number below is the number, not a suggestion.

You are the **orchestrator**. Per `CLAUDE.md`, every `.vue` edit goes through the **vue-expert** subagent. Your job is audit → brief → dispatch → verify.

## Design target

### Shell layout
- **Sidebar** — fixed `240px` wide, flush left, full viewport height, surface `#0f172a`.
  - Brand mark at top, `24px` padding.
  - Nav items as rows: `12px` vertical padding, `14px/500` text, `#94a3b8` inactive, `#f8fafc` active, hover lifts to `#e2e8f0`. Active item carries a `3px` inset accent bar on the left (`#3b82f6`).
  - User/profile menu docked at the bottom of the sidebar.
- **Main pane** — fills the rest. Internal padding `32px` top, `40px` left/right, `48px` bottom.
- **Page header strip** — top of each view: page title (`24px/600`) on the left, page actions on the right.
- **Filter bar strip** — directly below the page header, separated by a `1px --line` border, same horizontal rhythm.

### Spacing scale (base-4)
Only these values exist: `4, 8, 12, 16, 20, 24, 32, 40, 48, 64`. Expose as CSS vars `--sp-1` … `--sp-10` in `App.vue :root`. Any pixel value outside this set is a bug.

### Typography scale
Sizes: `11, 12, 13, 14, 16, 20, 24, 32`. Weights: `400, 500, 600, 700`. Line-height: `1.5` body, `1.25` headings. Font stack: system UI. Monospace (`ui-monospace, SFMono-Regular, Menlo`) is reserved for code, IDs, and paths.

### Color tokens (CSS vars in `:root`)
```css
--surface-bg: #f8fafc;
--surface-card: #ffffff;
--surface-muted: #f1f5f9;
--surface-nav: #0f172a;        /* sidebar */
--ink-primary: #0f172a;
--ink-secondary: #334155;
--ink-muted: #64748b;
--ink-inverse: #f8fafc;        /* text on dark */
--line: #e2e8f0;
--line-strong: #cbd5e1;
--accent: #3b82f6;
--success: #10b981;
--warn: #f59e0b;
--danger: #ef4444;
```

### Radius / elevation
- Radius: `6px` buttons & inputs, `10px` cards, `14px` modals.
- Default elevation is borderless. Cards use `1px solid var(--line)` with no shadow. Shadows are reserved for overlays: `0 8px 24px rgba(15, 23, 42, 0.08)` for modals and popovers.

### Density
Table rows `44px` tall. Inputs and buttons `36px` tall. Icons `16px` inline, `20px` standalone.

## Primitives

Create under `client/src/components/ui/`. Each primitive stays under 80 lines and uses the tokens above — no inline literals.

- `Sidebar.vue` — fixed shell; slots for nav list and footer.
- `NavItem.vue` — one row; props `to`, `label`; active state wired to `$route.path`.
- `PageHeader.vue` — slots for `title` and `actions`.
- `Card.vue` — `1px var(--line)`, `10px` radius, `24px` padding; slots for `title` and default body.
- `Button.vue` — variants `primary | secondary | ghost | danger`, sizes `sm | md`.
- `Badge.vue` — variants matching status tokens (`success`, `accent`, `warn`, `danger`, `neutral`).
- `EmptyState.vue` — slots for `icon`, title, description, action.

No external UI library. No new runtime dependencies.

## Steps

### 1. Audit
Start the dev servers if they are not running (`/start`). Load `http://localhost:3000` and walk every route under `/`, `/inventory`, `/orders`, `/spending`, `/demand`, `/reports`.

Produce a flat list of every file the redesign will touch, grouped as **shell / primitive / view**, each with a one-line note of what changes. The list must cover:
- `client/src/App.vue` (shell)
- Every file under `client/src/components/ui/` to be created (primitive)
- Every file under `client/src/views/` (view)
- Any existing component in `client/src/components/` that uses the old top-nav styling (e.g. `FilterBar.vue`, `ProfileMenu.vue`)

**Completion:** every `.vue` file touched by the redesign is on the list with its tag and delta note. If a view is tagged "view" but you have not written what changes, step 1 is not done.

### 2. Brief
Draft a single markdown brief that vue-expert will implement from. Required sections:
1. The entire **Design target** section verbatim from this skill.
2. The entire **Primitives** section verbatim.
3. The audit list from step 1, with explicit per-file deltas.
4. Implementation order (fixed): tokens in `App.vue` → primitives under `components/ui/` → shell rewrite of `App.vue` → one view at a time, in this order: Dashboard, Inventory, Orders, Spending, Demand, Reports.
5. Non-goals: no routing changes, no API changes, no new runtime deps, no dark-mode toggle, no animation framework.
6. Verification checklist (sidebar on every route; filter bar beneath the page header; spacing values restricted to the scale; primitives adopted by every view).

Save the brief at `.claude/skills/redesign-saas-ui/_brief.md`. The leading underscore marks it as scratch output — add `.claude/skills/redesign-saas-ui/_brief.md` to `.gitignore` if it is not already covered.

**Completion:** every section above exists in `_brief.md`, and every file from the audit appears in section 3 with a per-file delta.

### 3. Dispatch
Spawn the **vue-expert** subagent with:
- The absolute path to `_brief.md`.
- Instruction to read the brief end-to-end, then implement in the order specified in brief section 4.
- Instruction to run the Vite dev server after each view migration and visually confirm the view renders cleanly before moving on.
- Explicit demand: **every** view and shell file in the audit list must land in the new look within one dispatch. Half-migrated state is a failure.

Return value: a change list from vue-expert naming every file edited.

**Completion:** the change list covers every file from the audit, with no stragglers. If any audited file is missing, dispatch a follow-up round for the gaps before moving to step 4.

### 4. Verify
Open `http://localhost:3000` and walk every route. For each one, confirm:
- Sidebar renders with the correct active row.
- Page header + filter bar strips render in the stated order.
- Page content fits inside the main pane at `1280px` viewport width.
- Cards, tables, buttons, badges, and empty states come from `components/ui/`.

Then run a scale check on the built CSS:
```bash
grep -nE "padding|margin|gap|width|height" client/src/**/*.vue | \
  grep -oE "[0-9]+px" | sort -u
```
Every value in the output must be in `{4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 240}` (plus `36` and `44` for input/row heights, `1` and `3` for borders, `6`, `10`, `14` for radii, `16` and `20` for icons). Anything else is a scale violation — dispatch vue-expert back to fix it.

**Completion:** every route renders in the new look, the scale check comes back clean, and `_brief.md` is deleted (its purpose is spent).
