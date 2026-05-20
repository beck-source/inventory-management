---
name: redesign-ui
description: Redesign the Vue 3 app UI from a top navigation bar to a vertical dark sidebar SaaS layout
---

# redesign-ui

Converts the app layout from a horizontal top nav to a fixed vertical dark sidebar. All `.vue` file edits MUST be delegated to `vue-expert` (mandatory per CLAUDE.md rules).

## Goal

Replace the sticky top navigation bar with a 240px fixed sidebar on the left. The FilterBar and main content shift into a right-hand content column. The sidebar uses a dark background (#0f172a) contrasted against the existing light content area (#f8fafc).

## Final layout

```
.app (flex-direction: row)
  aside.sidebar            ← 240px, fixed, dark bg
    .sidebar-logo          ← company name + subtitle
    nav.sidebar-nav        ← router-links
    .sidebar-footer        ← LanguageSwitcher + ProfileMenu
  .content-wrapper         ← margin-left: 240px, flex: 1
    FilterBar              ← sticky top: 0
    main.main-content      ← router-view (unchanged)
```

## Instructions for vue-expert

### 1. `client/src/App.vue` — template

Replace the entire `<template>` block with:

```vue
<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="subtitle">{{ t('nav.subtitle') }}</span>
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
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content-wrapper">
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
</template>
```

### 2. `client/src/App.vue` — CSS (global `<style>` block)

Remove these rule blocks entirely (they belong to the old top nav):
- `.top-nav`
- `.nav-container`
- `.nav-container > .nav-tabs`
- `.nav-container > .language-switcher`
- `.logo`
- `.logo h1`
- `.subtitle`
- `.nav-tabs`
- `.nav-tabs a`
- `.nav-tabs a:hover`
- `.nav-tabs a.active`
- `.nav-tabs a.active::after`

Update `.app`:
```css
.app {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}
```

Update `.main-content` (remove max-width and auto margins — the sidebar handles horizontal constraint):
```css
.main-content {
  flex: 1;
  padding: 1.5rem 2rem;
}
```

Add these new rules at the top of the style block, after the `body` rule:

```css
.sidebar {
  width: 240px;
  min-height: 100vh;
  background: #0f172a;
  border-right: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
}

.sidebar-logo {
  padding: 24px 20px 20px;
  border-bottom: 1px solid #1e293b;
}

.sidebar-logo h1 {
  font-size: 1rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: -0.02em;
}

.sidebar-logo .subtitle {
  display: block;
  font-size: 0.6875rem;
  color: #64748b;
  font-weight: 400;
  margin-top: 4px;
  border-left: none;
  padding-left: 0;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-nav a {
  display: block;
  padding: 9px 12px;
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 6px;
  border-left: 3px solid transparent;
  transition: all 0.15s ease;
}

.sidebar-nav a:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.06);
}

.sidebar-nav a.active {
  color: #ffffff;
  background: rgba(59, 130, 246, 0.15);
  border-left-color: #3b82f6;
}

.sidebar-footer {
  padding: 16px 8px;
  border-top: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.content-wrapper {
  margin-left: 240px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
```

### 3. `client/src/components/FilterBar.vue` — CSS

Change the `top` value in `.filters-bar`:

```css
/* before */
top: 70px;

/* after */
top: 0;
```

No other changes to FilterBar.vue.

## Verification (use Playwright after editing)

1. Navigate to `http://localhost:3000`
2. Confirm the dark sidebar is visible on the left; the content area fills the right
3. Click each nav link — confirm active state (blue left border + white text) and page transition
4. Change a FilterBar dropdown — confirm filters still work and data updates
5. Scroll the content area — confirm FilterBar sticks at the top of the content column and the sidebar stays fixed
6. Take a screenshot to show the final result
