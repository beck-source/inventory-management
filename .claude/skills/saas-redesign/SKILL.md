---
name: saas-redesign
description: Redesign a Vue 3 application into a modern SaaS-style interface with a vertical left sidebar nav, consistent spacing scale, and polished professional styling. Use when the user asks to modernize the UI, switch from top-nav to sidebar, or apply a SaaS look.
---

# SaaS Redesign Skill

Transform the Vue 3 frontend into a modern SaaS-style interface: **vertical left sidebar navigation**, an **8pt spacing scale**, and a **polished neutral palette**. This skill is layout-and-style only — do not change data logic, API calls, or component behavior.

## Process

### 1. Audit current layout
Read these files to understand the existing shell before editing anything:
- `client/src/App.vue` — current nav + global styles
- `client/src/main.js` — router mount point
- One representative view (e.g. `client/src/views/Dashboard.vue`) — to see how page content is structured

Identify: where nav links are defined, how routes map to labels, what global classes exist.

### 2. Apply design tokens
Copy the contents of `design-tokens.css` (in this skill directory) into the `:root` block of `client/src/App.vue`'s global `<style>`. These define the spacing scale, colors, radii, shadows, and typography used throughout the redesign. **All subsequent CSS must reference these variables — no hard-coded px/hex values.**

### 3. Rebuild the app shell in `App.vue`
Replace the top nav with this two-column grid layout:

```
┌────────────┬──────────────────────────────────┐
│            │  Topbar (page title · actions)   │
│  Sidebar   ├──────────────────────────────────┤
│  240px     │                                  │
│  fixed     │  <router-view> (scrollable)      │
│            │                                  │
└────────────┴──────────────────────────────────┘
```

**Template structure:**
```html
<div class="app-shell">
  <aside class="sidebar">
    <div class="sidebar-brand">...</div>
    <nav class="sidebar-nav">
      <router-link class="nav-item" to="/">Dashboard</router-link>
      <!-- one per route -->
    </nav>
    <div class="sidebar-footer"><!-- ProfileMenu / LanguageSwitcher --></div>
  </aside>
  <div class="main">
    <header class="topbar">
      <h1 class="page-title">{{ $route.name }}</h1>
      <div class="topbar-actions"><!-- FilterBar or page actions --></div>
    </header>
    <main class="content"><router-view /></main>
  </div>
</div>
```

**Layout CSS (use tokens):**
```css
.app-shell { display: grid; grid-template-columns: var(--sidebar-w) 1fr; height: 100vh; }
.sidebar   { background: var(--surface-2); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: var(--space-4) var(--space-3); gap: var(--space-1); }
.sidebar-brand { font-weight: 600; font-size: var(--text-lg); padding: var(--space-2) var(--space-3) var(--space-5); }
.nav-item  { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3); border-radius: var(--radius-md); color: var(--text-2); font-size: var(--text-sm); font-weight: 500; text-decoration: none; }
.nav-item:hover { background: var(--surface-3); color: var(--text-1); }
.nav-item.router-link-active { background: var(--accent-soft); color: var(--accent); }
.sidebar-footer { margin-top: auto; border-top: 1px solid var(--border); padding-top: var(--space-4); }
.main      { display: flex; flex-direction: column; min-width: 0; background: var(--surface-1); }
.topbar    { height: var(--topbar-h); display: flex; align-items: center; justify-content: space-between; padding: 0 var(--space-6); border-bottom: 1px solid var(--border); background: var(--surface-0); }
.page-title { font-size: var(--text-xl); font-weight: 600; }
.content   { flex: 1; overflow-y: auto; padding: var(--space-6); }
```

**Responsive:** below 960px, collapse sidebar to icons-only (`--sidebar-w: 64px`, hide `.nav-item` text via a `.label` span). Below 720px, sidebar becomes an overlay toggled by a hamburger in the topbar.

### 4. Normalize page content
For each view in `client/src/views/`, wrap content in consistent containers without altering logic:
- Top-level sections → `.card` (`background: var(--surface-0); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: var(--space-5); box-shadow: var(--shadow-sm);`)
- Card grids → `display: grid; gap: var(--space-5); grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));`
- Section headings → `var(--text-lg)` weight 600, `var(--space-4)` bottom margin
- Tables → full-width, `var(--text-sm)`, header row `var(--text-2)` uppercase, rows separated by `var(--border)`

### 5. Polish details
- Buttons: primary `background: var(--accent); color: white; border-radius: var(--radius-md); padding: var(--space-2) var(--space-4);` — secondary uses `var(--surface-0)` with border
- Inputs/selects: `border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-2) var(--space-3); font-size: var(--text-sm);` — focus ring `box-shadow: 0 0 0 3px var(--accent-soft)`
- Status pills: `border-radius: 999px; padding: 2px var(--space-2); font-size: var(--text-xs); font-weight: 500;` with semantic bg/fg pairs
- Transitions: `transition: background 120ms ease, color 120ms ease, box-shadow 120ms ease` on interactive elements

### 6. Verify visually
Ensure dev server is running (`/start`), then use Playwright MCP to screenshot `http://localhost:3000` at desktop (1440px) and tablet (820px) widths. Confirm: sidebar renders, active route highlights, content scrolls independently, no horizontal overflow.

## Delegation rule
Per project CLAUDE.md: **any creation or significant modification of `.vue` files must be delegated to the `vue-expert` subagent.** Pass it this skill's layout spec and the token file contents. Do shell/CSS scaffolding yourself; hand `.vue` rewrites to the subagent.

## Constraints
- No new dependencies (no Tailwind, no UI libs) — plain CSS with custom properties only
- No emojis in UI (project design rule)
- Preserve all existing routes, props, emits, and composable usage
- Keep `<style scoped>` in views; only the shell + tokens are global in `App.vue`
