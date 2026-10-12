---
name: redesign-saas-ui
description: Redesign a Vue 3 app's UI into a modern SaaS-style interface — replace top navigation with a left vertical sidebar, apply a consistent spacing/design-token system, and polish to a professional look. Use when asked to modernize, restyle, or redesign a Vue frontend, convert a top nav bar into a sidebar layout, or give an app a SaaS/dashboard feel.
---

# Redesign a Vue 3 App into a Modern SaaS UI

This skill turns an existing Vue 3 application into a modern SaaS-style interface: a **left vertical navigation sidebar** (instead of a top nav bar), a **consistent spacing and design-token system**, and a **polished, professional look**. It is a methodology, not a fixed theme — it discovers the target app first, then adapts.

## When to use

- "Redesign / modernize / restyle this app", "make it look like a SaaS dashboard", "give it a professional look"
- "Move the top nav into a left sidebar", "add a vertical navigation sidebar"
- "Make the spacing/typography consistent", "clean up the layout"

## Guardrails (read first)

1. **Delegate all `.vue` work appropriately.** Check the project's `CLAUDE.md`. If it defines a Vue specialist subagent (e.g. `vue-expert`) or a rule that `.vue` files must be created/modified via that agent, you MUST delegate creating/editing `.vue` files to it. This skill's job is to plan, coordinate, and verify. Pass the agent the concrete design tokens, the app-shell structure, and the per-file changes below.
2. **Preserve behavior.** This is a visual/structural redesign. Do not change routing targets, data loading, API calls, computed logic, or filter behavior unless the redesign strictly requires relocating a control. Every route that worked before must still work.
3. **Match the stack that's already there.** Detect and reuse the app's conventions — Composition API vs Options API, `<script setup>` vs `setup()`, scoped CSS vs a CSS framework, existing icon library vs inline SVG, existing router. Do not introduce a new dependency (Tailwind, a UI kit, an icon package) unless the user asks or the app already uses it.
4. **No emojis in the UI** unless the project already uses them. Prefer inline SVG icons.
5. **Work on a branch.** If on the default branch, create a feature branch before editing.

## Process

### Phase 0 — Discover the current UI

Map the app before changing anything. For a broad sweep, use an `Explore` subagent; capture:

- **Entry & shell:** `main.js`/`main.ts`, the root `App.vue`, and how the layout is currently composed (where the top nav lives, header/footer, `<router-view>`).
- **Routing:** the router config — every route path, its component, and the human label shown in nav. You need this to rebuild the nav.
- **Design language today:** existing colors (hardcoded hex vs CSS variables), fonts, border radius, shadows, spacing values. Grep for repeated hex codes and `px` values to find the de-facto palette and spacing.
- **Views & shared components:** what pages exist, any global controls that sit above `<router-view>` (filter bars, search, profile menus) — these need a deliberate home in the new shell.
- **Styling model:** global stylesheet vs per-component scoped styles; whether global utility classes (cards, badges, tables, grids) already exist and are reused.

Produce a short inventory: routes+labels, the current palette, the current spacing values, and the list of global chrome elements. This drives every later decision.

### Phase 1 — Establish design tokens

Create a single source of truth as CSS custom properties (in the global stylesheet or `:root` of `App.vue` — wherever the app keeps globals). **Derive values from the app's existing palette** so the redesign feels like a refinement, not a foreign theme. If the app has no coherent palette, use a neutral, professional slate/gray base.

Starter token set (tune to the app):

```css
:root {
  /* Neutrals (surfaces, text, borders) */
  --color-bg: #f8fafc;          /* app background */
  --color-surface: #ffffff;      /* cards, sidebar, top bar */
  --color-surface-2: #f1f5f9;    /* subtle fills, hover */
  --color-border: #e2e8f0;
  --color-text: #0f172a;         /* primary text */
  --color-text-muted: #64748b;   /* secondary text */

  /* Brand / accent (reuse the app's primary if it has one) */
  --color-primary: #2563eb;
  --color-primary-weak: #eff6ff; /* active-nav background tint */

  /* Status */
  --color-success: #16a34a;
  --color-info: #2563eb;
  --color-warning: #ca8a04;
  --color-danger: #dc2626;

  /* Spacing scale — use these everywhere; no ad-hoc pixel values */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px;

  /* Radius, shadow, typography */
  --radius-sm: 6px; --radius-md: 10px; --radius-lg: 14px;
  --shadow-sm: 0 1px 2px rgba(15,23,42,.04), 0 1px 3px rgba(15,23,42,.06);
  --shadow-md: 0 4px 12px rgba(15,23,42,.08);
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --text-xs: 12px; --text-sm: 13px; --text-base: 14px; --text-lg: 16px;
  --text-xl: 20px; --text-2xl: 24px;

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 68px;
  --topbar-height: 60px;
  --content-max-width: 1280px;
}
```

Rules once tokens exist: **every spacing, color, radius, and shadow references a token.** Replace hardcoded values as you touch files. Consistent spacing is the single biggest driver of a "polished" feel.

### Phase 2 — Build the app shell (sidebar + content)

Replace the top-nav layout in the root component with a two-region shell: a fixed left **sidebar** and a **main** column containing a slim top bar and a scrollable content area.

Target layout:

```
┌──────────┬───────────────────────────────────────────┐
│          │  Top bar: page title · actions/search      │  <- --topbar-height
│  SIDEBAR ├───────────────────────────────────────────┤
│  --side  │                                             │
│  bar-    │   <router-view />  (padded content region,  │
│  width   │    max-width --content-max-width, centered) │
│          │                                             │
│  brand   │                                             │
│  nav …   │                                             │
│  ────     │                                             │
│  footer  │                                             │
│ (profile)│                                             │
└──────────┴───────────────────────────────────────────┘
```

Root shell CSS pattern:

```css
.app-shell { display: flex; min-height: 100vh; background: var(--color-bg); }
.sidebar {
  width: var(--sidebar-width); flex-shrink: 0;
  background: var(--color-surface); border-right: 1px solid var(--color-border);
  display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh;
}
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar {
  height: var(--topbar-height); flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 var(--space-5);
  background: var(--color-surface); border-bottom: 1px solid var(--color-border);
}
.content { flex: 1; overflow-y: auto; padding: var(--space-5); }
.content-inner { max-width: var(--content-max-width); margin: 0 auto; }
```

**Sidebar contents (top → bottom):**
- **Brand/logo** block at the top (app name or logo), padded with `--space-4`/`--space-5`.
- **Nav list**: one item per route, built from the router config discovered in Phase 0. Each item = an icon + a label. Use `<router-link>` with `active-class` (or `router-link-active`/`router-link-exact-active`) to style the current route: tinted background (`--color-primary-weak`), primary-colored text/icon, optional left accent bar. Add `aria-current="page"` semantics.
- **Footer**: pin profile/user/settings to the bottom (`margin-top: auto`). Relocate any profile menu / language switcher that used to live in the top nav here or into the top bar — don't drop it.

Prefer extracting the sidebar into its own component (e.g. `components/AppSidebar.vue`) and, if useful, `components/AppTopbar.vue`, keeping the root component a thin composition of shell + `<router-view>`.

**Icons:** if the app already uses an icon library, use it. Otherwise use small inline SVGs (16–20px, `stroke="currentColor"`, `stroke-width` ~1.6) so the icon inherits nav text color and needs no new dependency.

**Nav item + active-state pattern:**

```css
.nav-item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3); margin: 2px var(--space-3);
  border-radius: var(--radius-sm); color: var(--color-text-muted);
  font-size: var(--text-sm); font-weight: 500; text-decoration: none;
  transition: background .12s ease, color .12s ease;
}
.nav-item:hover { background: var(--color-surface-2); color: var(--color-text); }
.nav-item.router-link-active {
  background: var(--color-primary-weak); color: var(--color-primary); font-weight: 600;
}
.nav-item svg { width: 18px; height: 18px; flex-shrink: 0; }
```

**Top bar:** show the current page title (derive from route) and give global actions a consistent home. If the app had a global control strip above `<router-view>` (e.g. a filter bar), decide deliberately: keep it as a secondary bar directly under the top bar spanning the content, or move it into the top bar. Keep it visible on the routes that used it.

### Phase 3 — Polish pass

- **Spacing rhythm:** consistent page padding, consistent gaps between cards/sections (`--space-5`), consistent inner card padding (`--space-4`/`--space-5`). Eliminate one-off margins.
- **Cards & surfaces:** unify to one card style — `--color-surface`, `1px solid --color-border`, `--radius-md`, `--shadow-sm`. Reuse a single `.card` class rather than re-styling per view.
- **Typography hierarchy:** clear page title (`--text-2xl`, weight 700), section headings (`--text-lg`), body (`--text-base`), muted metadata (`--text-sm`, `--color-text-muted`). Set a sane global `line-height` (~1.5).
- **Interactive states:** hover, focus-visible (visible focus ring using the primary color), and active states on all clickable elements; subtle transitions (~120ms). Don't animate layout-shifting properties on scroll.
- **Tables/lists:** consistent row height, header styling, zebra or subtle row borders, aligned numeric columns.
- **Empty/loading states:** keep or add tasteful ones so pages never look broken mid-load.

### Phase 4 — Responsive & accessibility

- **Responsive:** below a breakpoint (~900px) collapse the sidebar to icon-only (`--sidebar-width-collapsed`) or an off-canvas drawer toggled by a hamburger in the top bar. Content region stays fluid with `min-width: 0` so tables/charts don't overflow.
- **Accessibility:** nav is a `<nav>` with a list; active link exposes current-page state; all interactive elements are keyboard-reachable with visible focus; icons that convey meaning have `aria-label`/`<title>`; color is never the only signal for status (pair with text/icon); maintain WCAG AA contrast against surfaces.

### Phase 5 — Verify

If the project has a skill/command to start the app, use it; otherwise start the dev server. Then, using Playwright MCP tools if available:

1. Load the app and **visit every route** — confirm each renders and the sidebar marks the correct active item.
2. Take screenshots at desktop and narrow widths; confirm the sidebar collapse/drawer behaves and nothing overflows.
3. Check the browser console — resolve any new errors/warnings introduced by the redesign.
4. Confirm relocated controls (filters, profile menu, etc.) still work.

Report: files created/modified, before/after of the layout, and verification results.

## Anti-patterns to avoid

- Hardcoding colors/spacing instead of using tokens (guarantees inconsistency).
- Rewriting view logic or data flow during a visual redesign.
- Dropping global controls (filter bar, profile menu) when removing the top nav — relocate them.
- Adding a heavy UI framework/icon package the app didn't have, without being asked.
- Sidebar with labels but no active state, or active state driven by manual flags instead of the router.
- Using array index as `v-for` key for nav items — key on route path or a stable id.
- Editing `.vue` files directly when the project requires delegating to a Vue specialist agent.

## Definition of done

- Top nav replaced by a left vertical sidebar with icon+label items, correct router-driven active state, brand at top, profile/utilities at bottom.
- A design-token system exists and is used consistently for color, spacing, radius, shadow, and type.
- Every prior route still works; relocated controls still function.
- Responsive behavior and keyboard/focus accessibility are in place.
- App builds and runs with no new console errors; verified across routes.
