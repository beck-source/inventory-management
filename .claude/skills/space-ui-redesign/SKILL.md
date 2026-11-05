---
name: space-ui-redesign
description: Redesign a Vue 3 application's UI into a futuristic, deep-space SaaS interface. Replaces a top nav bar with a left vertical sidebar, adds a design-token system (spacing, color, glow, type), a starfield/nebula backdrop, glass HUD-style panels and neon data accents. Use when asked to restyle, reskin, modernise or "make futuristic/spacey" a Vue 3 frontend, or to move navigation into a sidebar.
---

# Space UI Redesign (Vue 3)

Turn a conventional Vue 3 app into a **"mission control in deep space"** interface. It should look loud and futuristic, but it must also hold together visually. The theme is free to be wild because every effect comes from one small token set, so the result stays consistent.

## Design concept: "Orbital Command"

| Element | Treatment |
|---|---|
| Backdrop | Near-black void, drifting 3-layer parallax starfield, two slow-breathing nebula glows (violet + cyan), faint perspective grid on the horizon |
| Surfaces | Dark translucent glass (`backdrop-filter: blur`), 1px luminous hairline borders, HUD corner brackets on cards |
| Accent | **One** signature gradient, "aurora" (cyan `#22d3ee` → violet `#8b5cf6` → magenta `#ec4899`). Use it for active states, primary buttons, key numbers, page titles. Nothing else gets gradients |
| Status | Neon green / cyan / amber / red with soft glows, always paired with text (never color alone) |
| Type | `Orbitron` for brand and page titles only (uppercase, tracked). `Space Grotesk` for UI text. `JetBrains Mono` for numbers, IDs, SKUs, labels ("telemetry") |
| Motion | Slow ambient motion (stars drift, nebula breathes, status dot pulses) plus fast 150 ms micro-interactions. All of it is disabled under `prefers-reduced-motion` |
| Layout | Fixed 264 px left sidebar (collapses to 76 px icon rail below 1100 px, off-canvas below 760 px), sticky glass top bar for filters and user controls, content on an 8 px spacing grid |

### Coherence rules (non-negotiable)
1. **Only tokens.** No raw hex, `white` or `rgb()` in components after migration. Everything uses `var(--…)` from `theme.css`.
2. **One gradient, one glow color family.** Don't invent new accent colors per page.
3. **Spacing comes only from the scale** `--space-1…--space-12` (4 px base). Card padding is `--space-6`, grid gaps are `--space-5`, and section gaps are `--space-8`.
4. **Glow is earned.** Only interactive, active or critical elements glow. Static content gets hairlines, not halos.
5. **Readability beats spectacle.** Body text must stay ≥ 4.5:1 contrast on the glass surfaces. The tokens already satisfy this, so don't lower the text opacity.
6. **Numbers are mono + tabular** (`font-variant-numeric: tabular-nums`) so KPIs and tables align.

## Files in this skill

- `references/theme.css`: the complete design system (tokens, backdrop, shell, cards, tables, badges, forms, modals, scrollbars, motion). Copy it verbatim into the target app.
- `references/sidebar-shell.md`: the `App.vue` template, script additions, nav icons and responsive behaviour for the sidebar layout.
- `references/color-migration.md`: how to map typical light-theme hardcoded colors to tokens, plus SVG chart guidance.
- `references/preview.html`: a standalone visual preview of the theme. Open it in a browser to show the user the target look before changing their code.
- `scripts/audit-colors.sh`: lists hardcoded colors per file, for planning the migration and checking it at the end.

## Workflow

Work through these phases in order. After each phase, run the app and look at it in the browser (Playwright MCP if available, otherwise open it and ask the user). Do not batch everything and check only at the end.

### Phase 0: Survey (read-only)
1. Find the app shell (usually `src/App.vue`), router (`src/main.js` or `src/router/`), global styles, views and shared components.
2. Run `bash .claude/skills/space-ui-redesign/scripts/audit-colors.sh <client>/src` to see how many hardcoded colors each file has. That gives the migration order (shell first, then the files with the most hits).
3. Note the existing nav items, their routes, i18n keys (`t('nav.x')`), and any components embedded in the header (filters, language switcher, profile menu). **All of them must survive the redesign.**
4. Check the project's own rules (`CLAUDE.md`). If it says `.vue` edits must go through a specific subagent (e.g. `vue-expert`), delegate each phase's `.vue` work to that agent and pass it this skill's reference files.
5. Work on a branch and tell the user the plan: the phases and the files to be touched.

### Phase 1: Foundation
1. Copy `references/theme.css` to `src/styles/theme.css` and import it once in `src/main.js` (`import './styles/theme.css'`) **before** the app mounts.
2. Add the font `<link>` tags from the top of `theme.css` to `index.html` (fallback stacks are in place if the user is offline or declines external fonts).
3. Delete or neutralise global light-theme rules in the old global stylesheet (often an unscoped `<style>` in `App.vue`) that conflict with the theme: `body` background, `.card`, `.stat-card`, table, badge, button rules. Keep any layout rule that a view depends on and has no equivalent in `theme.css`.

### Phase 2: Shell, top nav → sidebar
Follow `references/sidebar-shell.md`:
1. Replace `<header class="top-nav">` with `<aside class="sidebar">` + `<div class="shell-main">` containing a `<header class="topbar">` and `<main class="main-content">`.
2. Move every nav link into the sidebar with an icon, keeping the `router-link` targets, i18n keys and active logic. Prefer `router-link`'s built-in `exact-active-class`/`active-class` over manual `$route.path` comparisons.
3. Move the filter bar, language switcher and profile menu into the top bar.
4. Add the collapse toggle (persisted to `localStorage`) and the mobile off-canvas behaviour.
5. Check that the app works: every route is reachable, the active state is correct, and modals still open from the profile menu.

### Phase 3: Global components
Restyle shared components (filter bar, dropdowns, profile menu, language switcher, modals) using the token classes (`.glass`, `.btn`, `.input`, `.select`, `.modal-*`). Replace their scoped hex colors with tokens using `color-migration.md`.

### Phase 4: Views, one at a time
For each view, in order of audit hit count:
1. Page header → `.page-header` with a `.page-kicker` (mono, e.g. `SECTOR 02 · INVENTORY`), a `.page-title` (Orbitron + aurora gradient) and a `.page-subtitle`.
2. KPI rows → `.stats-grid` of `.stat-card` (gets HUD brackets + glow on hover automatically). The value goes in `.stat-value`.
3. Content blocks → `.card` (+ `.card-header`, `.card-title`).
4. Tables → wrap in `.table-container`. Status cells use `.badge .badge--success|info|warning|danger|neutral`.
5. Charts → follow the SVG section in `color-migration.md` (use the series tokens, gradient fills via `<defs>`, a glow filter on the primary series only, and `currentColor` for axes).
6. Replace every remaining hex value in that file's `<style scoped>` with tokens.
7. Look at the result in the browser and fix spacing to the scale before moving on.

### Phase 5: Verify
1. `bash scripts/audit-colors.sh <client>/src` should report near-zero hits. Allowed exceptions are SVG `<stop>` colors that already reference tokens and the theme file itself.
2. `npm run build` passes.
3. Screenshot every route at 1440 px, 1024 px (icon rail) and 390 px (off-canvas). Check that text doesn't overflow or get clipped, that it's readable, and that the sidebar active state matches the route.
4. Check keyboard navigation: `Tab` through the sidebar. Focus rings (`--focus-ring`) must be visible.
5. With `prefers-reduced-motion: reduce` (DevTools → Rendering), there should be no animation.
6. Report to the user what changed, with screenshots, and list anything you left unconverted and why.

## Pitfalls
- **Don't break behaviour while restyling.** Keep all `v-if`/`v-for`/`@click`/props/emit wiring intact, and change only templates' class names/structure and styles.
- `backdrop-filter` on many nested elements is expensive. Apply glass to the container (card/sidebar/modal), not to rows or cells.
- `position: fixed` modals inside a transformed ancestor will mis-position. The shell uses no transforms, so keep it that way.
- Gradient text (`background-clip: text`) is invisible if a later rule sets `color`. Use the `.text-aurora` utility, don't hand-roll it.
- Chart text inside SVG doesn't inherit CSS `color` unless you use `fill="currentColor"`.
- Avoid emoji as icons; use the inline SVG icon set from `sidebar-shell.md` (stroke = `currentColor`).
- If the project forbids emojis or has its own design rules in `CLAUDE.md`, those win on conflicts. Tell the user about the conflict.
