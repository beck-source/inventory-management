---
name: vue-saas-redesign
description: Use when asked to redesign, modernize, or restyle a Vue 3 app's UI into a SaaS-style layout, replace a top navigation bar with a left vertical sidebar, or make spacing, cards, and tables look consistent and professional.
---

# Vue SaaS Redesign

## Overview

Turn a Vue 3 app with a top nav into a SaaS shell: fixed left sidebar, slim top bar, content area on a spacing scale. **Change the shell and the design tokens first; touch views only to swap hardcoded values for tokens.** Behavior (routes, i18n, filters, modals, API calls) must not change.

## Process

1. **Survey, read-only.** Find the app shell (usually `App.vue`), the router, the global styles, and how many views hardcode colors/spacing (`grep -c "#[0-9a-f]\{3,6\}"` per file). List nav items from the existing `<router-link>`s so none are lost.
2. **Define tokens** in one global stylesheet (`:root`): see Tokens. Reuse the app's existing palette if it has one; do not invent a new brand.
3. **Build the shell**: sidebar + top bar + content. See `shell-example.md`.
4. **Migrate views to tokens**, one view at a time, replacing hardcoded px/hex with variables. Don't restructure view templates.
5. **Verify in a browser** at 1440px, 1024px, and 390px: every route loads, active link highlights, sidebar collapses on mobile, no horizontal page scroll, no console errors.

## Layout Rules

| Part | Spec |
|---|---|
| Sidebar | 240px fixed, full height, `position: sticky; top: 0; height: 100vh`, own scroll |
| Sidebar sections | Brand at top, nav group in middle, user/profile and language at bottom |
| Nav item | 40px high, 12px horizontal padding, 8px gap icon to label, 8px radius |
| Active item | tinted background plus accent text color; never an underline |
| Top bar | 56-64px, page-level actions and filters only, no navigation |
| Content | max-width 1440px, padding `--space-6` (24px), pages stack with `--space-6` |
| Mobile (<900px) | sidebar becomes off-canvas drawer opened by a menu button; content full width |

## Tokens

Spacing is a 4px scale; use only these: `--space-1: 4px`, `-2: 8px`, `-3: 12px`, `-4: 16px`, `-5: 20px`, `-6: 24px`, `-8: 32px`. Radius: `--radius-sm: 6px`, `--radius-md: 8px`, `--radius-lg: 12px`. Define text, surface, border, accent, and status (success/info/warning/danger) colors as variables. One shadow for cards (`0 1px 2px rgba(15,23,42,.06)`), one for popovers.

Type scale: page title 24px/600, section title 16px/600, body 14px/400, caption 12px/500. Tabular numbers (`font-variant-numeric: tabular-nums`) for KPIs and tables.

## Conventions

- Icons are inline SVG components (24px grid, `stroke="currentColor"`, 1.5 stroke width). No emoji, no icon-font dependency unless the app already has one.
- Nav items stay `<router-link>` with `aria-current="page"` on the active one; the sidebar is a `<nav aria-label>`; the mobile toggle is a `<button>` with `aria-expanded`.
- Keep every user-visible string going through the app's i18n; don't hardcode labels while moving them.
- Hover, focus-visible, and disabled states for every interactive element. Transitions 150ms, only on color/background/transform.
- Cards: surface background, 1px border, `--radius-lg`, padding `--space-5`. Tables: 12px vertical cell padding, sticky header, no zebra stripes.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Rewriting view templates "while here" | Only swap values for tokens; structure changes are a separate task |
| New `margin`/`padding` values like 14px, 18px | Round to the scale |
| Sidebar added but `.main-content` keeps `margin: 0 auto` over full width | Make the app a two-column grid: `grid-template-columns: 240px 1fr` |
| Dropping nav items or the active-route logic | Diff the old and new link lists before finishing |
| Filter bar left sticky under the old 70px header | Re-anchor `top` to the new top bar height |
| Only checked desktop | Test 390px; verify the drawer opens, closes on route change |

## Project Notes (inventory-management)

- Shell lives in `client/src/App.vue`; global styles are also in `App.vue`. Palette is slate (`#0f172a`, `#64748b`, `#e2e8f0`) with blue accent `#2563eb`; keep it, and keep "no emojis in UI".
- Per `CLAUDE.md`, significant `.vue` edits go through the `vue-expert` subagent, and browser checks use the Playwright MCP against `http://localhost:3000`.
- Preserve `FilterBar`, `LanguageSwitcher`, `ProfileMenu`, and the two modals; only relocate them.
