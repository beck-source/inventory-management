---
name: saas-sidebar-redesign
description: Redesign a Vue 3 app's top navigation into a modern SaaS-style vertical sidebar with consistent design tokens, spacing, and a polished professional look. Use when the user asks to redesign the UI, add a sidebar nav, modernize the look, or convert a top nav bar to a side nav.
---

# SaaS Sidebar Redesign

Converts a Vue 3 app's top nav bar into a left-hand vertical sidebar (Linear/Stripe-dashboard style), normalizes hardcoded colors/spacing into design tokens, and polishes shared UI classes for a consistent professional look.

## Quick start

Trigger phrases: "redesign the UI", "add a sidebar", "modernize the look", "convert the top nav to a side nav". Target is usually the root layout component (`client/src/App.vue` in this repo) plus any views/components that share its global styles.

## Workflow

1. **Discover current layout** — read the root layout component and router config. Identify: the nav markup, its route links, any global CSS variables vs. hardcoded hex colors, and shared classes used across views (cards, tables, badges, stat grids).
2. **Extract design tokens** — pull the de-facto palette/spacing already in use into `:root` CSS custom properties (`--color-*`, `--space-*`, `--radius-*`, `--shadow-*`). Normalize what exists rather than inventing an unrelated palette, unless the user asked for a new one. See reference palette below as a starting example.
3. **Build the sidebar**:
   - Replace the top `<header class="top-nav">`/horizontal nav with a fixed-width `<aside class="sidebar">`: brand/logo at top, nav links (icon + label) in the middle, secondary items (account/profile, language switcher) pinned to the bottom.
   - Change the root layout from column (nav-on-top) to row: sidebar + main content as flex siblings, sidebar `position: sticky`/`fixed`, main content independently scrollable.
   - Preserve existing routes and router-link targets exactly — only restructure how they render, don't touch the router config's paths.
   - Keep secondary bars/modals (e.g. filter bars, profile/task modals) working — they move into the main content area, not the sidebar.
4. **Polish pass** — apply the new spacing scale consistently to shared classes (page headers, stat cards, data tables, badges, buttons). Add restrained hover/active states, rounded corners, soft shadows. Avoid inconsistent one-off spacing values once tokens exist.
5. **Responsive behavior** — the sidebar must collapse (icon-only rail or an off-canvas overlay) below a reasonable breakpoint (~1024px). Don't ship a fixed-width sidebar with no small-screen fallback.
6. **Flag orphaned views** — if a view file exists but isn't wired into the router (check for this), don't silently add or drop it from the new sidebar nav — ask the user or note it explicitly.

## Delegation

- Any creation or significant modification of `.vue` files MUST be delegated to the **vue-expert** subagent (project-wide rule) — pass it the token list and layout plan from steps 2-4 rather than writing component code directly.
- After vue-expert implements, verify visually with the **frontend-design** skill's screenshot-based QA (or **design-iterator** if it doesn't converge in 1-2 passes), checking the sidebar renders correctly across every routed view, at both desktop and collapsed-sidebar widths.

## Reference palette (example starting point)

Typical values already present in an unstyled top-nav SaaS app, useful as `:root` token seeds:

```css
:root {
  --color-bg: #ffffff;
  --color-border: #e2e8f0;
  --color-border-subtle: #f1f5f9;
  --color-text-primary: #0f172a;
  --color-text-secondary: #64748b;
  --color-accent: #2563eb;
  --color-accent-bg: #eff6ff;
  --color-success: #059669;
  --color-warning: #ea580c;
  --color-danger: #dc2626;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  --radius-md: 8px;
  --shadow-sm: 0 1px 3px 0 rgba(0,0,0,0.05);
}
```

Adjust to whatever palette the target app already uses — this is a shape to normalize into, not a mandatory color set.
