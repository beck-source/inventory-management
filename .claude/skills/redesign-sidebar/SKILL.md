---
name: redesign-sidebar
description: Redesign the Vue 3 app layout from horizontal top navigation to a modern SaaS-style vertical sidebar with icons. Use this skill when asked to add a sidebar, redesign navigation layout, switch to vertical nav, modernize the app layout, or move navigation to the left side.
---

# Sidebar Redesign Skill

Transform the app from a horizontal top-nav layout to a modern SaaS-style vertical sidebar. The sidebar is light-themed (white background, border-right separator), with SVG icons and text labels for each nav item.

## Files to Modify

1. **`client/src/App.vue`** — Major restructure: replace `<header class="top-nav">` with `<aside class="sidebar">`, change layout direction, replace nav CSS. **MANDATORY: delegate all changes to this file to the vue-expert subagent per CLAUDE.md rules.**
2. **`client/src/components/FilterBar.vue`** — Minor: change `top: 70px` to `top: 0` in `.filters-bar` (no top nav consuming 70px anymore).
3. **`client/src/locales/en.js`** — Add `reports: 'Reports'` to the `nav` object.
4. **`client/src/locales/ja.js`** — Add `reports: 'レポート'` to the `nav` object.

Do NOT modify: view components, composables, api.js, main.js, modal components, ProfileMenu.vue, LanguageSwitcher.vue.

## Target DOM Structure

Replace the current vertical `flex-direction: column` app layout with this row-based structure:

```
div.app                    (flex, flex-direction: ROW)
  aside.sidebar            (240px wide, sticky, full viewport height)
    div.sidebar-header     (logo area — company name + subtitle stacked)
    nav.sidebar-nav        (6 router-links, each: SVG icon + text label)
    div.sidebar-footer     (LanguageSwitcher + ProfileMenu, bottom of sidebar)
  div.content-area         (flex: 1, flex-direction: column)
    FilterBar              (sticky, top: 0)
    main.main-content      (router-view)
  ProfileDetailsModal      (unchanged — stays at App.vue root)
  TasksModal               (unchanged — stays at App.vue root)
```

## Step 1 — Update App.vue Template

Replace the entire `<header class="top-nav">...</header>` block and the flat `<FilterBar />` + `<main>` structure with:

```html
<div class="app">
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>{{ t('nav.companyName') }}</h1>
      <span class="subtitle">{{ t('nav.subtitle') }}</span>
    </div>

    <nav class="sidebar-nav">
      <router-link to="/" :class="{ active: $route.path === '/' }">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
          <rect x="11" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
          <rect x="3" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
          <rect x="11" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <span>{{ t('nav.overview') }}</span>
      </router-link>

      <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10 2L17 6V14L10 18L3 14V6L10 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M10 10L17 6" stroke="currentColor" stroke-width="1.5"/>
          <path d="M10 10L3 6" stroke="currentColor" stroke-width="1.5"/>
          <path d="M10 10V18" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <span>{{ t('nav.inventory') }}</span>
      </router-link>

      <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M7 2H5C3.89543 2 3 2.89543 3 4V16C3 17.1046 3.89543 18 5 18H15C16.1046 18 17 17.1046 17 16V4C17 2.89543 16.1046 2 15 2H13" stroke="currentColor" stroke-width="1.5"/>
          <rect x="7" y="1" width="6" height="3" rx="1" stroke="currentColor" stroke-width="1.5"/>
          <path d="M7 9H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M7 13H11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ t('nav.orders') }}</span>
      </router-link>

      <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10 1V19" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M14 5H8C6.34315 5 5 6.34315 5 8C5 9.65685 6.34315 11 8 11H12C13.6569 11 15 12.3431 15 14C15 15.6569 13.6569 17 12 17H6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ t('nav.finance') }}</span>
      </router-link>

      <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 17L8 11L12 14L17 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M14 3H17V6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>{{ t('nav.demandForecast') }}</span>
      </router-link>

      <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 4C4 2.89543 4.89543 2 6 2H11L16 7V16C16 17.1046 15.1046 18 14 18H6C4.89543 18 4 17.1046 4 16V4Z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M11 2V7H16" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M7 11H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M7 14H10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ t('nav.reports') }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="showProfileDetails = true"
        @show-tasks="showTasks = true"
      />
    </div>
  </aside>

  <div class="content-area">
    <FilterBar />
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
```

The `<script>` section is **unchanged** — do not modify any imports, the setup function, reactive state, or methods.

## Step 2 — Replace App.vue Styles

In the `<style>` block (unscoped), make these changes:

**Change `.app`:**
```css
.app {
  display: flex;
  flex-direction: row;   /* was: column */
  min-height: 100vh;
}
```

**Add new sidebar styles:**
```css
.sidebar {
  width: 240px;
  min-width: 240px;
  height: 100vh;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  z-index: 100;
  overflow-y: auto;
}

.sidebar-header {
  padding: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h1 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.sidebar-header .subtitle {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
  margin-top: 0.25rem;
  padding-left: 0;
  border-left: none;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  gap: 0.125rem;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  position: relative;
}

.sidebar-nav a:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.sidebar-nav a.active {
  color: #2563eb;
  background: #eff6ff;
}

.sidebar-nav a svg {
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 0.75rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sidebar-footer :deep(.dropdown-menu) {
  bottom: calc(100% + 0.5rem);
  top: auto;
}

.sidebar-footer :deep(.profile-button) {
  width: 100%;
  justify-content: flex-start;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
```

**Change `.main-content`** (adjust max-width since sidebar takes 240px):
```css
.main-content {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}
```

**Remove these old styles entirely:**
- `.top-nav` (full rule)
- `.nav-container` (full rule)
- `.nav-container > .nav-tabs` (full rule)
- `.nav-container > .language-switcher` (full rule)
- `.logo` (full rule)
- `.logo h1` (full rule)
- `.subtitle` (full rule — replaced by `.sidebar-header .subtitle`)
- `.nav-tabs` (full rule)
- `.nav-tabs a` (full rule)
- `.nav-tabs a:hover` (full rule)
- `.nav-tabs a.active` (full rule)
- `.nav-tabs a.active::after` (full rule)

Preserve all other global styles unchanged: `.page-header`, `.stats-grid`, `.stat-card`, `.card`, `.card-header`, `.card-title`, `.table-container`, `table`, `thead`, `th`, `td`, `tbody tr`, `.badge` and all badge variants, `.loading`, `.error`.

## Step 3 — Update FilterBar.vue

In `client/src/components/FilterBar.vue`, find the `.filters-bar` CSS rule and change one value:

```css
/* Before */
.filters-bar {
  top: 70px;
  ...
}

/* After */
.filters-bar {
  top: 0;
  ...
}
```

No other changes to FilterBar.vue.

## Step 4 — Update Locale Files

In `client/src/locales/en.js`, add `reports` to the `nav` object:
```js
nav: {
  // ... existing keys ...
  reports: 'Reports',
}
```

In `client/src/locales/ja.js`, add `reports` to the `nav` object:
```js
nav: {
  // ... existing keys ...
  reports: 'レポート',
}
```

## Do Not Change

- `<script>` section of App.vue — all logic, imports, setup function, reactive state, methods
- Component imports in App.vue — FilterBar, ProfileMenu, ProfileDetailsModal, TasksModal, LanguageSwitcher
- ProfileDetailsModal and TasksModal — template, script, and styles
- ProfileMenu.vue, LanguageSwitcher.vue — template, script, and styles
- All view files under `client/src/views/`
- All composables under `client/src/composables/`
- `client/src/api.js`
- `client/src/main.js`
- z-index values (modals: 2000, dropdowns: 1000)
- Global utility styles in App.vue: `.page-header`, `.stats-grid`, `.stat-card`, `.card`, table styles, badge styles, `.loading`, `.error`

## Verification Checklist

After applying changes, verify:
1. Sidebar renders on the left with white background and right border
2. All 6 nav links appear vertically with SVG icon + text label
3. Active route shows blue background (`#eff6ff`) on the correct link
4. FilterBar is sticky at `top: 0` of the content area (not top of viewport)
5. LanguageSwitcher dropdown opens upward from the sidebar footer
6. ProfileMenu dropdown opens upward from the sidebar footer
7. Modals (profile, tasks) overlay the full viewport including sidebar
8. Content area fills all remaining width to the right of the sidebar
9. Sidebar remains visible when scrolling long pages
10. Switching between EN and JA shows correct translations for all nav items including Reports
11. No JavaScript console errors
