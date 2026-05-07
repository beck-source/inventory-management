# SaaS UI Redesign

Redesign this Vue 3 application's layout from a horizontal top-nav bar into a modern SaaS-style interface with a fixed vertical sidebar, consistent spacing, and a polished professional look.

---

## Step 1 — Read before touching anything

Read the following files in full before making any changes:
- `client/src/App.vue` — current layout shell, nav, global styles
- `client/src/main.js` — route definitions (to know all nav items)

Identify:
1. Every `<router-link>` currently in the top nav (path + label)
2. Where `<FilterBar />` is rendered
3. Where `<ProfileMenu />` and `<LanguageSwitcher />` are rendered
4. The global CSS classes used by views (`.page-header`, `.card`, `.stat-card`, etc.) — these must not change

---

## Step 2 — Delegate ALL Vue file changes to vue-expert

You MUST delegate every `.vue` file edit to the **vue-expert** subagent. Do not edit `.vue` files yourself.

Give vue-expert the full current content of each file it needs to change, plus the precise spec below.

---

## Redesign Spec for App.vue

Replace the current `<header class="top-nav">` + horizontal nav with a fixed vertical sidebar layout. The rest of the app (`<FilterBar />`, `<router-view />`) moves into a content area to the right of the sidebar.

### Layout structure (replace entire template)

```
<div class="app-shell">

  <!-- ─── Sidebar ─── -->
  <aside class="sidebar">

    <!-- Brand -->
    <div class="sidebar-brand">
      <span class="brand-name">{{ t('nav.companyName') }}</span>
      <span class="brand-sub">{{ t('nav.subtitle') }}</span>
    </div>

    <!-- Nav links -->
    <nav class="sidebar-nav">
      <router-link v-for="item in navItems" :key="item.path"
        :to="item.path"
        :class="['nav-item', { active: $route.path === item.path }]">
        <span class="nav-icon" v-html="item.icon"></span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Bottom actions -->
    <div class="sidebar-footer">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="showProfileDetails = true"
        @show-tasks="showTasks = true"
      />
    </div>

  </aside>

  <!-- ─── Main content ─── -->
  <div class="content-area">
    <div class="content-topbar">
      <FilterBar />
    </div>
    <main class="content-main">
      <router-view />
    </main>
  </div>

</div>
```

### navItems data array (define in setup())

Build `navItems` as a computed or const from the route list. Each item: `{ path, label, icon }`.

Use these inline SVG icons (set `width="16" height="16"` and `fill="currentColor"`):

| Route | Label (call t() for translated labels) | Icon SVG path |
|---|---|---|
| `/` | `t('nav.overview')` | `<svg>…</svg>` — grid/dashboard: `M3 3h7v7H3V3zm0 9h7v7H3v-7zm9-9h7v7h-7V3zm0 9h7v7h-7v-7z` (2×2 grid) |
| `/inventory` | `t('nav.inventory')` | box/cube: `M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z` |
| `/orders` | `t('nav.orders')` | shopping cart / list: `M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 0-2-2h-2` |
| `/spending` | `t('nav.finance')` | dollar/coin: `M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z` |
| `/demand` | `t('nav.demandForecast')` | trend up: `M23 6l-9.5 9.5-5-5L1 18` (polyline, use stroke not fill) |
| `/reports` | Reports | bar chart: `M18 20V10M12 20V4M6 20v-6` (use stroke not fill) |
| `/restocking` | Restocking | refresh/cycle: `M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15` |

For stroke-based icons, use `fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`.

### New CSS (replace the entire `<style>` block with this)

```css
/* ── Shell ── */
.app-shell {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
}

/* ── Sidebar ── */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: #0f172a;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 100;
  border-right: 1px solid #1e293b;
}

.sidebar-brand {
  padding: 24px 20px 20px;
  border-bottom: 1px solid #1e293b;
}

.brand-name {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: -0.2px;
}

.brand-sub {
  display: block;
  font-size: 11px;
  color: #475569;
  margin-top: 2px;
}

/* ── Nav ── */
.sidebar-nav {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}

.nav-item:hover {
  background: #1e293b;
  color: #e2e8f0;
}

.nav-item.active {
  background: #1e293b;
  color: #f1f5f9;
}

.nav-item.active .nav-icon {
  color: #3b82f6;
}

.nav-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon svg {
  width: 16px;
  height: 16px;
}

.nav-label {
  line-height: 1;
}

/* ── Sidebar footer ── */
.sidebar-footer {
  padding: 12px 10px;
  border-top: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* ── Content area ── */
.content-area {
  flex: 1;
  margin-left: 220px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.content-topbar {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.content-main {
  flex: 1;
  padding: 28px;
}
```

### Remove these old CSS rules (they belonged to `.top-nav`)

Delete any rules for: `.top-nav`, `.nav-container`, `.nav-tabs`, `.nav-tabs a`, `.nav-tabs a.active`, `.logo`, `.subtitle`, `.main-content`

---

## Step 3 — Verify global view classes are untouched

After the redesign, confirm these CSS classes still exist unchanged in App.vue (or wherever they live globally):
`.page-header`, `.card`, `.card-header`, `.card-title`, `.stat-card`, `.badge`, `.table-container`, `.loading`, `.error`

If any were accidentally removed, restore them.

---

## Step 4 — Open the browser and verify

Once vue-expert confirms the changes are written:

1. Confirm the frontend dev server is running at `http://localhost:3000`
2. Open `http://localhost:3000` in the browser using `Start-Process`
3. Use Playwright MCP (`mcp__playwright__*`) to screenshot the result and verify:
   - Sidebar is visible on the left, ~220px wide, dark background
   - All nav items are present and legible
   - Dashboard content fills the right side
   - FilterBar appears in the top bar of the content area
   - No layout breakage (content not hidden behind sidebar)
4. Click through at least 2 other routes to confirm active state updates and content renders correctly

If you cannot use Playwright, open the browser manually and describe what to check.

---

## Step 5 — Report

Summarize:
- What was changed (file and key structural changes)
- Any nav labels that fell back to hard-coded strings (no i18n key found)
- Any visual issues noticed during verification
- What the user should test manually (profile menu, language switcher, modals)
