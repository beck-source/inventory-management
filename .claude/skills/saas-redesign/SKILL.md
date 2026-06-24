---
name: saas-redesign
description: Redesign this Factory Inventory Management app's UI into a modern SaaS-style interface with a left vertical navigation sidebar (replacing the top nav bar), a consistent design-token system, an 8px spacing rhythm, and a polished professional look. Use when asked to modernize, redesign, restyle, or "make the UI look like a SaaS product," add/convert to a sidebar, or improve visual consistency across the Vue 3 frontend.
---

# SaaS UI Redesign

Transform the current top-nav layout into a modern SaaS shell: a fixed left sidebar for navigation, a clean top bar for global controls, and content pages built on a single, consistent design-token system. This skill is specific to **this** app (Vue 3 + Composition API, Vite, the slate/gray palette). It ships concrete tokens — use them verbatim so the result is cohesive, not approximate.

## Non-negotiable rules

1. **Delegate every `.vue` change to `vue-expert`.** CLAUDE.md mandates it: "ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert." This skill is the design spec; vue-expert does the editing. Paste the relevant token table + component spec into the delegation prompt.
2. **Do not change behavior.** This is a visual/layout redesign only. Routes, `setup()` logic, API calls, i18n keys, and component props/events stay identical. The 7 routes in `client/src/main.js` and their `t('nav.*')` labels must all remain reachable.
3. **No emojis in the UI** (per CLAUDE.md design system). Use inline SVG icons for sidebar items.
4. **Document non-obvious CSS** with a short comment explaining the *why* (e.g. why a `grid-template-columns` value, why a sticky offset).
5. **Verify in the browser** before declaring done (see Verification). The dev servers run on `:3000` (frontend) and `:8001` (API) — use the `start` skill if they're down.

## Where things live

| Concern | File | Notes |
|---|---|---|
| App shell + **global** styles | `client/src/App.vue` | The `<style>` block here is **unscoped/global** — it defines `.card`, `.stat-card`, `table`, `.badge`, `.page-header`, etc. used by every view. This is where the token `:root` block and the new layout go. |
| Nav links (source of truth) | `client/src/App.vue` template (`.nav-tabs`) + `client/src/main.js` routes | 7 links: `/` Overview, `/inventory`, `/orders`, `/spending` (Finance), `/demand`, `/restocking`, `/reports`. |
| Global controls | `client/src/components/LanguageSwitcher.vue`, `ProfileMenu.vue` | Currently live in the top nav. They move to the new top bar. |
| Sub-nav under header | `client/src/components/FilterBar.vue` | The 4-filter bar. Keep it directly under the top bar, inside the content column. |
| Per-page content | `client/src/views/*.vue` | Use scoped styles; consume the global tokens. Don't redefine colors/spacing locally. |

## Design tokens (bake these in verbatim)

Add this `:root` block to the **top** of the global `<style>` in `App.vue`, then refactor existing hardcoded hex values to reference the tokens. The color values are seeded from the app's current palette so nothing shifts unexpectedly — you're formalizing what's already there, then building the sidebar on top.

```css
:root {
  /* Color — neutrals (slate) */
  --bg-app: #f8fafc;        /* page background */
  --bg-surface: #ffffff;    /* cards, sidebar, top bar */
  --bg-subtle: #f1f5f9;     /* hover fills, table thead */
  --bg-muted: #f8fafc;      /* zebra / inset surfaces */
  --border: #e2e8f0;        /* default 1px borders */
  --border-strong: #cbd5e1; /* hover borders */
  --border-faint: #f1f5f9;  /* table row dividers */

  /* Color — text */
  --text-strong: #0f172a;   /* headings, values */
  --text-body: #334155;     /* table cells, body copy */
  --text-muted: #64748b;    /* labels, secondary */
  --text-subtle: #475569;   /* table headers */

  /* Color — brand / primary */
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --primary-soft: #eff6ff;  /* active nav fill */
  --primary-softer: #dbeafe;

  /* Color — status (text / soft-bg pairs) */
  --success: #059669;  --success-bg: #d1fae5;  --success-fg: #065f46;
  --warning: #ea580c;  --warning-bg: #fed7aa;  --warning-fg: #92400e;
  --danger:  #dc2626;  --danger-bg:  #fecaca;  --danger-fg:  #991b1b;
  --info:    #2563eb;  --info-bg:    #dbeafe;  --info-fg:    #1e40af;

  /* Spacing — strict 8px rhythm (use ONLY these steps) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;

  /* Radius */
  --radius-sm: 6px;   /* badges, nav items, buttons */
  --radius-md: 8px;   /* inputs, banners */
  --radius-lg: 10px;  /* cards, stat cards */

  /* Elevation */
  --shadow-sm: 0 1px 3px 0 rgba(0,0,0,0.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06);

  /* Typography scale */
  --text-xs: 0.75rem;    /* table headers, badges */
  --text-sm: 0.875rem;   /* body, table cells */
  --text-base: 0.938rem; /* nav, buttons, descriptions */
  --text-lg: 1.125rem;   /* card titles */
  --text-xl: 1.375rem;   /* logo */
  --text-2xl: 1.875rem;  /* page H2 */
  --text-3xl: 2.25rem;   /* stat values */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

  /* Layout */
  --sidebar-w: 248px;
  --topbar-h: 64px;
  --content-max: 1440px;
}
```

**Spacing rule:** every margin/padding/gap must be a `--space-*` step. No ad-hoc `0.625rem`/`0.813rem` values for layout. (Font sizes use the type scale; only *spacing* is locked to the 8px steps.)

## The structural transformation

### Before (current `App.vue`)
```
.app (flex column)
 ├─ header.top-nav (sticky)  ← logo · nav-tabs · LanguageSwitcher · ProfileMenu
 ├─ FilterBar
 └─ main.main-content        ← router-view, max-width 1600px centered
```

### After (target shell)
```
.app (flex ROW, min-height 100vh)
 ├─ aside.sidebar (fixed width var(--sidebar-w), full height, sticky)
 │    ├─ .sidebar-brand     ← logo + subtitle (stacked)
 │    └─ nav.sidebar-nav    ← 7 router-links, each = icon + label, vertical
 └─ .app-body (flex column, flex:1, min-width:0)
      ├─ header.topbar (sticky, height var(--topbar-h))  ← page context (left) · LanguageSwitcher · ProfileMenu (right)
      ├─ FilterBar
      └─ main.main-content   ← router-view, max-width var(--content-max)
```

Key template moves in `App.vue`:
- Change `.app` from `flex-direction: column` to `flex-direction: row`.
- Replace `<header class="top-nav">…</header>` with `<aside class="sidebar">` (brand + vertical nav) **and** a new `<header class="topbar">` placed inside a new `.app-body` wrapper.
- Move `<LanguageSwitcher />` and `<ProfileMenu>` into `.topbar`.
- Keep `<FilterBar />`, `<router-view />`, and all three modals exactly as-is.
- The `setup()` script and all imports stay byte-for-byte unchanged.

### Sidebar spec
- Width `var(--sidebar-w)`; `background: var(--bg-surface)`; `border-right: 1px solid var(--border)`.
- `position: sticky; top: 0; height: 100vh; align-self: flex-start; overflow-y: auto;` so it stays put while content scrolls.
- Brand block: padding `var(--space-5)`; `h1` at `--text-xl`, weight 700, `--text-strong`, `letter-spacing: -0.025em`; subtitle at `--text-xs`, `--text-muted`, stacked below (not inline).
- Nav items: vertical stack, gap `var(--space-1)`, padding `var(--space-3) var(--space-4)`, `--radius-sm`, `--text-base`, `--text-muted`, `gap: var(--space-3)` between icon and label.
  - Hover: `background: var(--bg-subtle); color: var(--text-strong)`.
  - Active (`router-link-active` / current `:class` pattern): `background: var(--primary-soft); color: var(--primary)`; **left** accent bar `3px` `var(--primary)` (replace the old bottom `::after` underline — accent moves to the inline-start edge for a sidebar).
- Each item gets a 20px inline SVG icon (stroke `currentColor`, `stroke-width: 1.75`) so it tints with the text color. Suggested icons: Overview=grid, Inventory=box, Orders=clipboard/cart, Finance=dollar/chart, Demand=trending-up, Restocking=refresh, Reports=document.

### Top bar spec
- `height: var(--topbar-h)`; `background: var(--bg-surface)`; `border-bottom: 1px solid var(--border)`; `position: sticky; top: 0; z-index: 100`.
- Flex row, `align-items: center`, padding `0 var(--space-6)`, gap `var(--space-4)`; controls (`LanguageSwitcher`, `ProfileMenu`) pushed right with `margin-left: auto`.

## Polish pass (apply to global primitives in `App.vue`)
Refactor the existing primitives to tokens and tighten rhythm:
- `.card` / `.stat-card`: `padding: var(--space-5)`, `--radius-lg`, `1px var(--border)`, hover → `--border-strong` + `--shadow-md`.
- `.stats-grid`: `gap: var(--space-5)`; keep `repeat(auto-fit, minmax(280px, 1fr))`.
- `.page-header`: `margin-bottom: var(--space-5)`; H2 `--text-2xl`/700/`--text-strong`; p `--text-base`/`--text-muted`.
- Tables: `th` `--text-xs`/uppercase/`--text-subtle`; `td` `--text-sm`/`--text-body`; row hover `--bg-muted`; dividers `--border-faint`.
- `.badge.*`, `.stat-card.*` status colors → the `--*-bg`/`--*-fg` token pairs.
- Buttons (`.btn-primary` etc.): `--primary` → hover `--primary-hover`, `--radius-sm`, padding `var(--space-2) var(--space-5)`.

## Process

1. **Read first.** `App.vue` (shell + global styles), `main.js` (routes), `FilterBar.vue`, `ProfileMenu.vue`, `LanguageSwitcher.vue`. Confirm the current nav links and that styles in `App.vue` are global.
2. **Delegate to `vue-expert`** with: (a) this token `:root` block, (b) the before/after shell, (c) the sidebar + top-bar specs. Have it edit `App.vue` only for the shell + tokens + primitives. Views usually need no changes because they consume global classes — touch a view only if it hardcodes layout that fights the new shell.
3. **Responsive:** below ~768px the sidebar should collapse (off-canvas or icon-only rail). If out of scope for the request, say so explicitly rather than leaving it half-done.
4. **Verify** (below), then summarize what changed.

## Verification checklist
- [ ] All 7 nav links render in the sidebar, each with an icon, and route correctly.
- [ ] Active route shows the left accent + `--primary-soft` fill; only one item active at a time.
- [ ] `LanguageSwitcher` and `ProfileMenu` work from the top bar; switching to `ja` still flows (currency `¥`, translated labels).
- [ ] `FilterBar` and all pages (Dashboard, Inventory, Orders, Spending, Demand, Restocking, Reports) render with no layout breakage; content respects `--content-max`.
- [ ] No hardcoded spacing outside the `--space-*` scale in changed CSS; no emojis added.
- [ ] No console errors; no `setup()`/API/i18n behavior changed.
- [ ] Sidebar stays fixed while the content column scrolls.

**How to verify in-browser:** ensure servers are up (`start` skill), open `http://localhost:3000`, click through every nav item, toggle the language switcher, and resize the window to check the responsive behavior. If the Playwright MCP is connected, use it to snapshot each route; otherwise open the routes manually and inspect.
