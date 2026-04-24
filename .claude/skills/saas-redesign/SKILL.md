---
name: saas-redesign
description: Redesign the Vue 3 app UI into a modern SaaS-style interface with a branded blue vertical sidebar, integrated filters, and polished spacing. Modifies App.vue and FilterBar.vue.
---

# SaaS UI Redesign

This skill transforms the inventory management app from a horizontal top-navigation layout into a modern SaaS-style interface. The result is a fixed blue sidebar on the left containing all navigation links and filters, with the content area filling the remaining width.

## What changes

- `client/src/App.vue` — template restructured, global styles overhauled
- `client/src/components/FilterBar.vue` — restyled to render vertically inside the sidebar

No backend changes. No new dependencies.

**Delegation rule:** Per CLAUDE.md, every `.vue` file modification must be delegated to the `vue-expert` subagent. Provide each agent with the complete specs below — exact template HTML, exact CSS, exact script diff.

---

## 1. New Layout Architecture

App.vue's template must become:

```
div.app
  aside.sidebar
    div.sidebar-header        ← logo + subtitle
    nav.sidebar-nav           ← 7 router-links, stacked vertically
    div.sidebar-filters       ← <FilterBar /> component
    div.sidebar-footer        ← <LanguageSwitcher /> + <ProfileMenu />
  div.content-area
    main.main-content
      <router-view />
  <ProfileDetailsModal />     ← unchanged, stays at root
  <TasksModal />              ← unchanged, stays at root
```

The `<header class="top-nav">` and the standalone `<FilterBar />` between header and main are both removed. FilterBar moves inside the sidebar.

---

## 2. App.vue — Complete Template

Replace the entire `<template>` block with:

```html
<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="sidebar-subtitle">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" :class="{ active: $route.path === '/' }">
          {{ t('nav.overview') }}
        </router-link>
        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
          {{ t('nav.inventory') }}
        </router-link>
        <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
          {{ t('nav.orders') }}
        </router-link>
        <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
          {{ t('nav.restocking') }}
        </router-link>
        <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
          {{ t('nav.finance') }}
        </router-link>
        <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
          {{ t('nav.demandForecast') }}
        </router-link>
        <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
          Reports
        </router-link>
      </nav>

      <div class="sidebar-filters">
        <FilterBar />
      </div>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content-area">
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>
```

The script block is **unchanged** — no logic changes needed.

---

## 3. App.vue — Global CSS Replacement

Replace the entire unscoped `<style>` block. The new block must:

### Remove entirely
- All `.top-nav`, `.nav-container`, `.nav-tabs` rules and sub-rules (these are replaced by sidebar)

### Add: Sidebar styles

```css
/* ── Layout ── */
.app {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  min-height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  background: #2563eb;
  color: white;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 1rem;
  z-index: 100;
  overflow-y: auto;
}

.content-area {
  margin-left: 260px;
  flex: 1;
  min-width: 0;
}

.main-content {
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem 2.5rem;
}

/* ── Sidebar Header ── */
.sidebar-header {
  margin-bottom: 2rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-header h1 {
  font-size: 1.125rem;
  font-weight: 700;
  color: white;
  line-height: 1.3;
}

.sidebar-subtitle {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.65);
  display: block;
  margin-top: 0.25rem;
}

/* ── Sidebar Nav ── */
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-nav a {
  display: block;
  padding: 0.625rem 1rem;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 8px;
  transition: background 0.15s, color 0.15s;
}

.sidebar-nav a:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.sidebar-nav a.active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-weight: 600;
}

/* ── Sidebar Filters ── */
.sidebar-filters {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

/* ── Sidebar Footer ── */
.sidebar-footer {
  margin-top: auto;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
```

### Keep exactly as-is (copy verbatim)

All of these rule groups must be preserved without modification:

- `*` (reset)
- `body`
- `.page-header` and `.page-header h2`, `.page-header p`
- `.stats-grid`
- `.stat-card` and all `.stat-card.*` variants
- `.stat-label`, `.stat-value`
- `.card`, `.card-header`, `.card-title` — update `border-radius` to `12px`, add `box-shadow: 0 1px 3px rgba(0,0,0,0.04)`, update `margin-bottom` to `1.5rem`
- `.stats-grid` — update `gap` to `1.5rem`
- `.table-container`, `table`, `thead`, `th`, `td`, `tbody tr`, `tbody tr:hover`
- `.badge` and all `.badge.*` variant rules (success, warning, danger, info, increasing, decreasing, stable, high, medium, low, submitted)
- `.loading`, `.error`

---

## 4. FilterBar.vue — Vertical Sidebar Styles

FilterBar's **template and script are unchanged**. Only the scoped `<style scoped>` block changes.

Replace all scoped styles with:

```css
.filters-bar {
  /* transparent — sidebar provides the background */
}

.filters-container {
  padding: 0;
}

.filters-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-group label {
  font-size: 0.688rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.65);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.filter-select {
  width: 100%;
  padding: 0.375rem 0.625rem;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 6px;
  font-size: 0.813rem;
  color: white;
  cursor: pointer;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='rgba(255,255,255,0.7)' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  padding-right: 1.75rem;
  transition: background 0.15s, border-color 0.15s;
}

.filter-select:hover {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

.filter-select:focus {
  background-color: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.6);
}

.filter-select option {
  background: #1d4ed8;
  color: white;
}

.reset-filters-btn {
  width: 100%;
  margin-top: 0.25rem;
  padding: 0.375rem 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.813rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  transition: background 0.15s;
}

.reset-filters-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.reset-filters-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
```

---

## 5. Execution Steps

When invoked, Claude should:

1. Delegate App.vue changes to `vue-expert` with the complete template from Section 2 and the complete CSS from Section 3
2. Delegate FilterBar.vue style replacement to `vue-expert` with the CSS from Section 4
3. After both agents complete, start the frontend dev server and use Playwright MCP to verify at http://localhost:3000

---

## 6. Verification Checklist

- [ ] Sidebar visible on left with blue (`#2563eb`) background
- [ ] Logo and subtitle visible in sidebar header, white text
- [ ] All 7 nav links present and stacked vertically
- [ ] Active route link highlighted with semi-transparent white background
- [ ] Clicking a nav link routes correctly and updates active state
- [ ] 4 filter dropdowns visible in sidebar below nav links, white text on semi-transparent background
- [ ] Selecting a filter updates the page content
- [ ] Reset Filters button visible and functional
- [ ] Content area fills remaining width to the right of sidebar
- [ ] No horizontal top-nav bar visible
- [ ] All existing cards, tables, badges, and page headers unchanged in style
- [ ] ProfileMenu and LanguageSwitcher visible in sidebar footer
