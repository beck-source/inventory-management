---
name: saas-redesign
description: Redesign this app's Vue 3 UI into a modern SaaS layout with a left vertical sidebar instead of the top nav, design tokens, shared primitives and consistent spacing. Use when asked to restyle, modernize or re-layout the frontend, or to move navigation to a sidebar. Do NOT use for backend changes, chart/SVG internals, or adding features.
---

# SaaS redesign (inventory-management client)

Restyle `client/` from a top-nav layout to a sidebar layout. This skill is specific to this repo: it names real files and line ranges, so re-read them before editing because line numbers drift.

## Non-negotiables

- **Delegate every `.vue` create or significant edit to the `vue-expert` subagent** (project rule in CLAUDE.md). Give it one step at a time with the exact file list.
- Keep the design system: slate neutrals, green/blue/yellow/red status colors, **no emojis in UI**, custom SVG charts and CSS Grid (no UI or chart libraries, no Tailwind).
- Comment the "why" for non-obvious CSS or logic (z-index choices, sticky offsets, dropdown direction).
- Do not touch `client/.npmrc`, `package-lock.json` or the backend. The repo is public: no internal URLs or credentials.
- The user wants to learn: explain each change briefly and make sure edits show as diffs. Do not batch everything into one giant edit.
- Never guess. If a color has no exact token, leave it and list it in the report.

## Steps

### 1. Preflight
- Run `git status`. If the tree has unrelated changes or you are on `main`, propose a branch (`/demo-branch`) and wait for the user's answer.
- Check `http://localhost:3000` and `http://localhost:8001/docs`. If down, run `/start`.
- Using the Playwright MCP (`mcp__playwright__*`), screenshot every route at 1440px wide as "before": `/`, `/inventory`, `/orders`, `/spending`, `/demand`, `/reports`.
  - Screenshots always land in `.playwright-mcp/` inside the repo (the tool ignores paths outside it). That folder is git-ignored, so this is safe. Use short filenames like `before-orders-1440.png`; a long absolute path gets flattened into an unreadable filename.
  - Take screenshots one at a time, in their own step, after the navigate call returns. Do not batch a navigate and a screenshot in the same step.
  - Verify each image shows the intended route (active nav item and page heading). In the first run a screenshot taken right after navigating to `/inventory` showed Overview and the tab had drifted back to `/`; retaking after a fresh navigate fixed it. Discard any image that does not match.
  - Every navigate call returns a full page snapshot, which is large on table-heavy routes (`/inventory`). Expect this to be the main context cost of the verify steps.
  - Record the baseline console messages before changing anything. This app already logs: a Vue warning that `PurchaseOrderModal` cannot be resolved (Dashboard references a component that does not exist), and 404s from `/api/tasks`. Step 8 should flag only errors that are new compared with this baseline.

### 2. Tokens
- Copy `.claude/skills/saas-redesign/tokens.css` to `client/src/styles/tokens.css`.
- Import it in `client/src/main.js` before `App.vue` styles load.
- Read the existing `.badge.*` and `.stat-card.*` rules in `App.vue`. If they use different status hexes than the token file, update `tokens.css` to match them so step 6 causes no visual change.
- Add the Inter font in `client/index.html`: preconnect plus a Google Fonts stylesheet `<link>` for weights 400, 500, 600. The stack already names Inter but it was never loaded.

### 3. App shell (vue-expert)
Edit `client/src/App.vue`:
- Replace `header.top-nav` (logo, `nav.nav-tabs`, `LanguageSwitcher`, `ProfileMenu`) with `aside.sidebar`:
  - Fixed, full height, `width: var(--sidebar-width)`, `z-index: var(--z-sidebar)`, surface background, right border.
  - Top: logo block (company name and subtitle, existing i18n keys).
  - Middle: nav list.
  - Bottom (footer): `LanguageSwitcher` and `ProfileMenu`.
- Drive the nav from one array of `{ path, labelKey }` and render with `v-for` keyed by `path`. Use `router-link` with `exact-active-class` for `/` so it is not active everywhere. Remove the hand-written `:class="{ active: $route.path === ... }"` bindings.
- Keep the six existing routes only. `Backlog.vue` has no route; do not add one unless the user asks, and mention it in the report.
- Content column: `margin-left: var(--sidebar-width)`, `max-width: var(--content-max-width)`, padding from `--space-*`. `FilterBar` moves inside this column, above `<router-view/>`.
- Keep `ProfileDetailsModal` and `TasksModal` mounted at the bottom of `.app` with their current props and events.
- Narrow screens (below 900px): sidebar becomes an off-canvas drawer opened by a menu button in the content column, with a backdrop that closes it. Close it on route change.

### 4. Sticky and dropdown fixes (vue-expert)
- `FilterBar.vue`: it is `position: sticky; top: 70px` because the old top nav was 70px tall. Change to `top: 0`, drop its own `max-width: 1600px` / full-width container, and use `--z-filterbar`.
- `ProfileMenu.vue` and `LanguageSwitcher.vue`: dropdowns currently open down and right-aligned (`top: calc(100% + .5rem); right: 0`). In a sidebar footer they must open **upward** (`bottom: calc(100% + .5rem); left: 0`) and fit within the sidebar width or extend right over the content. Keep `z-index: var(--z-dropdown)`.
- Remove the `.nav-container > .language-switcher` rule in `App.vue`, which targeted the old header.
- Check that the sidebar's `z-index` stays below dropdowns (1000), `TasksModal` (1000) and the other modals (2000).

### 5. Shared primitives
In the global (unscoped) style block in `App.vue`, using tokens only:
- Add `.btn`, `.btn-primary`, `.btn-secondary`, plus a focus ring.
- Refine `.page-header`, `.card`, `.card-header`, `.stat-card` (and its warning/success/danger/info variants), `.badge.*`, and the global table styles for consistent padding, radius and borders.
- Six modals have their own scoped `.btn-secondary` (Backlog, Cost, Inventory, Product, ProfileDetails, Tasks). Remove a copy only if the shared class renders identically; otherwise leave it and list it in the report.

### 6. Token remap
Replace exact-match hex literals with variables, one file at a time (vue-expert), starting with `App.vue`, then components, then views.

| Hex | Token |
|---|---|
| `#f8fafc` | `var(--color-bg)` |
| `#ffffff` / `#fff` (surfaces only) | `var(--color-surface)` |
| `#e2e8f0` | `var(--color-border)` |
| `#cbd5e1` | `var(--color-border-strong)` |
| `#0f172a` | `var(--color-text-strong)` |
| `#1e293b` | `var(--color-text)` |
| `#64748b` | `var(--color-text-muted)` |
| `#2563eb` | `var(--color-accent)` |
| `#eff6ff` | `var(--color-accent-soft)` |
| `#f1f5f9` | `var(--color-surface-muted)` |
| `#334155` | `var(--color-text-body)` |
| `#475569` | `var(--color-text-secondary)` |
| `#059669` / `#ea580c` / `#dc2626` / `#2563eb` (stat values) | `--color-success` / `--color-warning` / `--color-danger` / `--color-info` |
| `#d1fae5` / `#fed7aa` / `#fecaca` / `#dbeafe` (badge bg) | `--color-success-soft` / `-warning-soft` / `-danger-soft` / `-info-soft` |
| `#065f46` / `#92400e` / `#991b1b` / `#1e40af` (badge text) | `--color-success-text` / `-warning-text` / `-danger-text` / `-info-text` |
| `#fef2f2` | `var(--color-danger-faint)` |
| `#e0e7ff` / `#3730a3` | `var(--color-stable-soft)` / `var(--color-stable-text)` |

Rules:
- `#2563eb` is both the accent and the info color. In shell and navigation code use `--color-accent`; in status contexts (stat values, badges) use `--color-info`. Same value, different intent.
- Status colors map to the status tokens only when the hex matches exactly. Hexes outside this table (for example the Tailwind greens `#10b981` or ambers `#f59e0b` used in charts) are not remapped.
- **Skip** hex values inside SVG attributes and chart fills (`fill=`, `stroke=`, chart series colors). Chart internals are out of scope.
- `#fff` as text on a dark or accent background is not a surface: leave it.
- Spacing: replace off-scale rem values only in shell and shared-primitive code. Do not mass-edit spacing in views.
- Record every skipped hex, with file and count, for the report.

### 7. i18n
- Nav labels use `t('nav.*')`. "Reports" is currently a hardcoded English string: give it a key.
- Any new key goes in **both** `client/src/locales/en.js` and `client/src/locales/ja.js`. Add a menu button label for the mobile drawer.

### 8. Verify (Playwright MCP, `http://localhost:3000`)
For each of the six routes, at 1440px and 800px:
- Screenshot "after" and compare with the "before" shots.
- Sidebar does not overlap content; the content column is not clipped.
- FilterBar sticks at the top of the content column and does not slide under the sidebar.
- `ProfileMenu` and `LanguageSwitcher` dropdowns are fully visible and clickable.
- Open one detail modal and `TasksModal`: both cover the sidebar.
- At 800px the drawer opens, closes on backdrop click and on route change.
- Changing a filter still updates data (the filter flow must be unchanged).
- `browser_console_messages` shows no new errors.

Then run `cd client && npm run build` and `/test`. Fix failures caused by your changes; report unrelated failures as they are.

### 9. Report
Give a per-file summary of what changed and why. Include:
- Hex values skipped, and modal `.btn-secondary` copies left in place.
- Known gap: `Backlog.vue` has no route.
- Anything needing the user's decision.
- Before/after screenshot paths.

## Quality checklist
- [ ] No hardcoded hex remains in shell, FilterBar, ProfileMenu or LanguageSwitcher
- [ ] No emojis, no new dependencies
- [ ] Every `.vue` edit went through `vue-expert`
- [ ] `en.js` and `ja.js` have the same keys
- [ ] Build passes; screenshots cover all six routes at two widths
- [ ] Re-running the skill would not duplicate tokens, the sidebar or the import
