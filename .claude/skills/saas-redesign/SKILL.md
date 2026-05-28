---
name: saas-redesign
description: Redesigns the inventory-management Vue 3 app shell from a horizontal top-nav into a modern SaaS layout with a fixed vertical left sidebar, and introduces CSS design tokens (:root custom properties) that the existing global classes are migrated to use. Use this skill when the user asks to "redesign the UI", "convert to a sidebar layout", "make it look like a SaaS app", "modernize the layout", "add a left nav", or "introduce design tokens / CSS variables". Project-specific to client/src/App.vue and client/src/components/FilterBar.vue.
---

# SaaS Sidebar Redesign

This skill converts the current horizontal `top-nav` layout in `client/src/App.vue`
into a two-column SaaS shell:

    ┌──────────┬──────────────────────────────┐
    │          │  FilterBar (sticky top:0)    │
    │ Sidebar  ├──────────────────────────────┤
    │ 240px    │  .main-content               │
    │          │  (router-view)               │
    └──────────┴──────────────────────────────┘

It also introduces a `:root` design-token block and migrates the existing global
classes (`.card`, `.stat-card`, `.badge`, `table`, `.page-header`, etc.) to use them.

**Hard rules (from CLAUDE.md):**
- Any edit to a `.vue` file MUST be delegated to the `vue-expert` subagent via the Task tool. Do not edit `.vue` files directly.
- Browser verification MUST use Playwright MCP tools (`mcp__playwright__*`) against `http://localhost:3000`.
- No emojis or icons in UI. Slate/gray palette only.

---

## Step 1: Ensure servers are running

The redesign is verified visually, so both servers must be up.

```bash
lsof -ti:3000,8001 | xargs kill -9 2>/dev/null || true
(cd server && uv run python main.py &)
(cd client && npm run dev &)
```

Poll until the frontend responds:

```bash
for i in $(seq 1 20); do curl -sf http://localhost:3000 >/dev/null && break; sleep 1; done
```

If servers were already running, skip the restart and just confirm reachability.

---

## Step 2: Capture the "before" state

Use Playwright MCP to record the current top-nav layout for comparison:

1. `mcp__playwright__browser_navigate` → `http://localhost:3000/`
2. `mcp__playwright__browser_take_screenshot` → save as `before-redesign.png`
3. `mcp__playwright__browser_snapshot` → confirm the DOM has `header.top-nav > .nav-container > nav.nav-tabs` with 6 horizontal links.

Do not proceed until the "before" screenshot is captured.

---

## Step 3: Define design tokens

The current `<style>` block in `client/src/App.vue` uses hard-coded hex values.
The redesign introduces a single `:root` block at the **top** of that `<style>` tag
(immediately after the `* { … }` reset). All values are lifted from the existing
file — this is a refactor, not a re-theme.

```css
:root {
  /* Palette (lifted from existing App.vue hex codes) */
  --color-bg:            #f8fafc;
  --color-surface:       #ffffff;
  --color-surface-muted: #f1f5f9;
  --color-border:        #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-ink:           #0f172a;
  --color-text:          #1e293b;
  --color-text-muted:    #64748b;
  --color-text-subtle:   #475569;
  --color-primary:       #2563eb;
  --color-primary-soft:  #eff6ff;
  --color-success:       #059669;
  --color-warning:       #ea580c;
  --color-danger:        #dc2626;

  /* Spacing scale (rem) */
  --space-1: 0.25rem;   /*  4px */
  --space-2: 0.5rem;    /*  8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;

  /* Layout */
  --sidebar-width: 240px;
  --content-max:   1600px;
}
```

This block is **passed verbatim** to `vue-expert` in Step 4 — do not write it to the file yourself.

---

## Step 4: Delegate App.vue restructure to vue-expert

Use the Task tool with `subagent_type: vue-expert`. Pass this prompt:

> Restructure `client/src/App.vue` from a horizontal top-nav into a vertical-sidebar SaaS shell. Make ONLY the changes below; preserve the entire `<script>` block, all imports, both modals, and all event wiring exactly as-is.
>
> **A. Template** — replace the current `<header class="top-nav">` / `<FilterBar />` / `<main>` siblings with:
>
> ```html
> <div class="app">
>   <aside class="sidebar">
>     <div class="sidebar-logo">
>       <h1>{{ t('nav.companyName') }}</h1>
>       <span class="subtitle">{{ t('nav.subtitle') }}</span>
>     </div>
>
>     <nav class="sidebar-nav">
>       <router-link to="/">{{ t('nav.overview') }}</router-link>
>       <router-link to="/inventory">{{ t('nav.inventory') }}</router-link>
>       <router-link to="/orders">{{ t('nav.orders') }}</router-link>
>       <router-link to="/spending">{{ t('nav.finance') }}</router-link>
>       <router-link to="/demand">{{ t('nav.demandForecast') }}</router-link>
>       <router-link to="/reports">Reports</router-link>
>     </nav>
>
>     <div class="sidebar-footer">
>       <LanguageSwitcher />
>       <ProfileMenu
>         @show-profile-details="showProfileDetails = true"
>         @show-tasks="showTasks = true"
>       />
>     </div>
>   </aside>
>
>   <div class="content">
>     <FilterBar />
>     <main class="main-content">
>       <router-view />
>     </main>
>   </div>
>
>   <!-- ProfileDetailsModal and TasksModal stay here, direct children of .app -->
> </div>
> ```
>
> Drop the manual `:class="{ active: $route.path === ... }"` bindings — vertical nav uses vue-router's automatic `.router-link-active` instead.
>
> **B. Style** — at the TOP of the `<style>` block, immediately after the `* { … }` reset, insert the `:root` design-token block (see Step 3 of the saas-redesign skill for the exact block).
>
> **C. Style** — DELETE these selectors entirely: `.top-nav`, `.nav-container`, `.nav-container > .nav-tabs`, `.nav-container > .language-switcher`, `.nav-tabs`, `.nav-tabs a`, `.nav-tabs a:hover`, `.nav-tabs a.active`, `.nav-tabs a.active::after`, `.logo`, `.logo h1`, `.subtitle` (the old one). REPLACE `.app` and ADD the new shell rules:
>
> ```css
> .app {
>   display: grid;
>   grid-template-columns: var(--sidebar-width) 1fr;
>   min-height: 100vh;
> }
>
> .sidebar {
>   background: var(--color-surface);
>   border-right: 1px solid var(--color-border);
>   display: flex;
>   flex-direction: column;
>   position: sticky;
>   top: 0;
>   height: 100vh;
>   padding: var(--space-6) var(--space-4);
>   gap: var(--space-6);
> }
>
> .sidebar-logo h1 {
>   font-size: 1.25rem;
>   font-weight: 700;
>   color: var(--color-ink);
>   letter-spacing: -0.025em;
> }
>
> .sidebar-logo .subtitle {
>   display: block;
>   margin-top: var(--space-1);
>   font-size: 0.813rem;
>   color: var(--color-text-muted);
> }
>
> .sidebar-nav {
>   display: flex;
>   flex-direction: column;
>   gap: var(--space-1);
> }
>
> .sidebar-nav a {
>   padding: var(--space-2) var(--space-3);
>   color: var(--color-text-muted);
>   text-decoration: none;
>   font-weight: 500;
>   font-size: 0.938rem;
>   border-radius: var(--radius-sm);
>   border-left: 3px solid transparent;
>   transition: all 0.15s ease;
> }
>
> .sidebar-nav a:hover {
>   color: var(--color-ink);
>   background: var(--color-surface-muted);
> }
>
> .sidebar-nav a.router-link-active {
>   color: var(--color-primary);
>   background: var(--color-primary-soft);
>   border-left-color: var(--color-primary);
> }
>
> .sidebar-footer {
>   margin-top: auto;
>   display: flex;
>   flex-direction: column;
>   gap: var(--space-3);
>   padding-top: var(--space-4);
>   border-top: 1px solid var(--color-border);
> }
>
> .content {
>   display: flex;
>   flex-direction: column;
>   min-width: 0;
> }
>
> .main-content {
>   flex: 1;
>   width: 100%;
>   max-width: var(--content-max);
>   padding: var(--space-6) var(--space-8);
> }
> ```
>
> **D. Style** — update `body` to use tokens: `background: var(--color-bg); color: var(--color-text);` (keep the font stack).
>
> Do not touch any view files. Do not add icons or emojis. Return when Vite HMR compiles cleanly.

Wait for the subagent to complete before continuing.

---

## Step 5: Migrate global classes to design tokens

Second `vue-expert` delegation. Mechanical 1:1 substitutions in the remaining global selectors of `client/src/App.vue` `<style>` — no behaviour change.

Pass this prompt:

> In `client/src/App.vue` `<style>`, replace hard-coded values with the `:root` tokens already defined. Apply exactly these substitutions and nothing else:
>
> | Selector(s) | Replace | With |
> |---|---|---|
> | `.page-header h2`, `.card-title`, `.stat-value` | `color: #0f172a` | `color: var(--color-ink)` |
> | `.page-header p`, `.stat-label`, `.loading` | `color: #64748b` | `color: var(--color-text-muted)` |
> | `.stat-card`, `.card` | `border: 1px solid #e2e8f0` | `border: 1px solid var(--color-border)` |
> | `.stat-card`, `.card` | `border-radius: 10px` | `border-radius: var(--radius-lg)` |
> | `.stat-card`, `.card` | `padding: 1.25rem` | `padding: var(--space-5)` |
> | `.stat-card:hover` | `border-color: #cbd5e1` | `border-color: var(--color-border-strong)` |
> | `.card-header` | `border-bottom: 1px solid #e2e8f0` | `border-bottom: 1px solid var(--color-border)` |
> | `thead` | `#f8fafc` / `#e2e8f0` | `var(--color-bg)` / `var(--color-border)` |
> | `th` | `color: #475569` | `color: var(--color-text-subtle)` |
> | `td` | `border-top: 1px solid #f1f5f9` | `border-top: 1px solid var(--color-surface-muted)` |
> | `tbody tr:hover` | `background: #f8fafc` | `background: var(--color-bg)` |
> | `.badge` | `border-radius: 6px` | `border-radius: var(--radius-sm)` |
> | `.error` | `border-radius: 8px` | `border-radius: var(--radius-md)` |
> | `.stat-card.info .stat-value` | `#2563eb` | `var(--color-primary)` |
> | `.stat-card.success .stat-value` | `#059669` | `var(--color-success)` |
> | `.stat-card.warning .stat-value` | `#ea580c` | `var(--color-warning)` |
> | `.stat-card.danger .stat-value` | `#dc2626` | `var(--color-danger)` |
>
> Leave the badge background/foreground pairs (`#d1fae5`/`#065f46` etc.) as literal hex — they are not part of the core token set.

---

## Step 6: Fix FilterBar for the new shell

`client/src/components/FilterBar.vue` currently assumes a 70px top-nav above it (`.filters-bar { position: sticky; top: 70px }`) and self-centres at 1600px.

Third `vue-expert` delegation:

> In `client/src/components/FilterBar.vue` scoped styles only (no template changes):
> - `.filters-bar`: change `top: 70px` → `top: 0`; change `background` → `var(--color-surface)`; change `border-bottom` colour → `var(--color-border)`.
> - `.filters-container`: remove `max-width: 1600px` and `margin: 0 auto` (the content column now constrains width); set `padding: 0 var(--space-8)`.

---

## Step 7: Verify with Playwright

Use Playwright MCP against `http://localhost:3000`:

1. `mcp__playwright__browser_navigate` → `http://localhost:3000/`
2. `mcp__playwright__browser_snapshot` → confirm:
   - an `aside.sidebar` element exists as a sibling of `div.content`
   - `nav.sidebar-nav` contains 6 `<a>` elements stacked vertically
   - the first link (Overview) carries `class="router-link-active"`
   - NO `header.top-nav` element remains
3. `mcp__playwright__browser_take_screenshot` → save as `after-redesign.png`
4. `mcp__playwright__browser_navigate` → `http://localhost:3000/inventory`, then `browser_snapshot` → confirm the Inventory link has `router-link-active` and FilterBar is visible at the top of the content column (sticky, `top: 0`).
5. `mcp__playwright__browser_resize` → `{ width: 1280, height: 800 }`, screenshot again → sidebar holds at 240px, `.main-content` does not overflow horizontally.

If any check fails, re-delegate the specific fix to `vue-expert` — never edit `.vue` files directly.

---

## Step 8: Cleanup and report

```bash
rg -n 'top-nav|nav-container|nav-tabs' client/src/App.vue
rg -n '\$route\.path ===' client/src/App.vue
```

Both should return zero matches.

Report to the user:
- Files changed: `client/src/App.vue`, `client/src/components/FilterBar.vue`
- Views untouched (width-agnostic, rely on `.main-content` padding)
- Attach `before-redesign.png` and `after-redesign.png`

---

## Reference: Token map

| Token | Value | Replaces |
|---|---|---|
| `--color-bg` | `#f8fafc` | body bg, thead bg, tr:hover |
| `--color-surface` | `#ffffff` | nav, .card, .stat-card |
| `--color-surface-muted` | `#f1f5f9` | nav hover, td border |
| `--color-border` | `#e2e8f0` | all 1px borders |
| `--color-border-strong` | `#cbd5e1` | .stat-card:hover border |
| `--color-ink` | `#0f172a` | h1/h2, .stat-value |
| `--color-text` | `#1e293b` | body color |
| `--color-text-muted` | `#64748b` | subtitles, labels |
| `--color-text-subtle` | `#475569` | th |
| `--color-primary` | `#2563eb` | active link, .info |
| `--color-primary-soft` | `#eff6ff` | active link bg |
| `--space-1..8` | `0.25–2rem` | paddings/gaps |
| `--radius-sm/md/lg` | `6/8/10px` | .badge / .error / .card |
| `--sidebar-width` | `240px` | grid column |
| `--content-max` | `1600px` | .main-content max-width |

## Reference: DOM before → after

```
BEFORE                                AFTER
.app (flex col)                       .app (grid 240px | 1fr)
├─ header.top-nav                     ├─ aside.sidebar
│  └─ .nav-container                  │  ├─ .sidebar-logo
│     ├─ .logo                        │  ├─ nav.sidebar-nav (6 links, vertical)
│     ├─ nav.nav-tabs (horizontal)    │  └─ .sidebar-footer
│     ├─ LanguageSwitcher             │     ├─ LanguageSwitcher
│     └─ ProfileMenu                  │     └─ ProfileMenu
├─ FilterBar                          └─ .content (flex col, min-width:0)
└─ main.main-content                     ├─ FilterBar  (sticky top:0)
   └─ router-view                        └─ main.main-content
                                            └─ router-view
```

## Reference: Pitfalls

1. **FilterBar sticky offset** — hard-coded `top: 70px`. Forgetting Step 6 leaves a 70px gap above the filters.
2. **`.filters-container` max-width** — its `max-width: 1600px; margin: 0 auto` was for a full-bleed header. Inside the content column it must be removed or filters centre oddly on wide screens.
3. **Active link styling** — old code uses manual `:class="{ active: $route.path === '/' }"` + `::after` underline. New sidebar uses `.router-link-active` with a left-border accent. Do not reintroduce `::after`.
4. **`.main-content` max-width** — keep it (`var(--content-max)`). Views assume a padded, width-capped container.
5. **Modals stay at `.app` root** — `ProfileDetailsModal` and `TasksModal` remain direct children of `.app` so their fixed overlays cover the viewport.
6. **`min-width: 0` on `.content`** — required so wide tables can scroll instead of blowing out the grid column.
7. **No emojis / no icons** — sidebar links are text-only per the design system.
8. **Never edit `.vue` files directly** — every change in Steps 4–6 goes through `vue-expert`.
