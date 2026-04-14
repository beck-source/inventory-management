# Sidebar Layout Reference

Complete App.vue template and CSS for both dark and light sidebar variants. All code is grounded in the actual `client/src/App.vue` — preserve every existing global CSS class and i18n call.

---

## Dark Sidebar (Default)

### Complete `<template>` Replacement

```html
<template>
  <div class="app-shell">
    <!-- ═══════════════════════════════════════════════════
         SIDEBAR
         ═══════════════════════════════════════════════════ -->
    <aside class="sidebar">
      <!-- Brand -->
      <div class="sidebar-brand">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-sub">{{ t('nav.subtitle') }}</span>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <router-link to="/" :class="['nav-item', { active: $route.path === '/' }]">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M2 4a2 2 0 012-2h3a2 2 0 012 2v3a2 2 0 01-2 2H4a2 2 0 01-2-2V4zm9 0a2 2 0 012-2h3a2 2 0 012 2v3a2 2 0 01-2 2h-3a2 2 0 01-2-2V4zM2 13a2 2 0 012-2h3a2 2 0 012 2v3a2 2 0 01-2 2H4a2 2 0 01-2-2v-3zm9 0a2 2 0 012-2h3a2 2 0 012 2v3a2 2 0 01-2 2h-3a2 2 0 01-2-2v-3z"/>
          </svg>
          <span>{{ t('nav.overview') }}</span>
        </router-link>

        <router-link to="/inventory" :class="['nav-item', { active: $route.path === '/inventory' }]">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z"/>
            <path fill-rule="evenodd" d="M3 8h14v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8zm5 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" clip-rule="evenodd"/>
          </svg>
          <span>{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link to="/orders" :class="['nav-item', { active: $route.path === '/orders' }]">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4zm7 5a1 1 0 10-2 0v1H8a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V9z" clip-rule="evenodd"/>
          </svg>
          <span>{{ t('nav.orders') }}</span>
        </router-link>

        <router-link to="/spending" :class="['nav-item', { active: $route.path === '/spending' }]">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z"/>
            <path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd"/>
          </svg>
          <span>{{ t('nav.finance') }}</span>
        </router-link>

        <router-link to="/demand" :class="['nav-item', { active: $route.path === '/demand' }]">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd"/>
          </svg>
          <span>{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link to="/reports" :class="['nav-item', { active: $route.path === '/reports' }]">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm2 10a1 1 0 10-2 0v3a1 1 0 102 0v-3zm2-3a1 1 0 011 1v5a1 1 0 11-2 0v-5a1 1 0 011-1zm4-1a1 1 0 10-2 0v7a1 1 0 102 0V8z" clip-rule="evenodd"/>
          </svg>
          <!-- "Reports" is hardcoded in the original App.vue — no i18n key exists -->
          <span>Reports</span>
        </router-link>

        <router-link to="/restocking" :class="['nav-item', { active: $route.path === '/restocking' }]">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
          </svg>
          <span>{{ t('nav.restocking') }}</span>
        </router-link>
      </nav>

      <!-- Footer: language + profile -->
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <!-- ═══════════════════════════════════════════════════
         MAIN AREA
         ═══════════════════════════════════════════════════ -->
    <div class="main-area">
      <!-- Filter bar sits as a sticky top strip -->
      <div class="content-topbar">
        <FilterBar />
      </div>

      <main class="page-content">
        <router-view />
      </main>
    </div>

    <!-- Modals (unchanged) -->
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

> **`<script>` is unchanged.** No additions needed in `setup()` — the template uses `t()`, `$route`, and the same event handlers as before.

---

### Dark Sidebar CSS

Replace the `.app`, `.top-nav`, `.nav-container`, `.logo`, `.subtitle`, `.nav-tabs`, `.main-content` blocks with the following. Keep all other global CSS classes (`.card`, `.badge`, etc.) intact — only update their property values to use tokens (see `design-tokens.md`).

```css
/* ─────────────────────────────────────────────
   Shell layout
   ───────────────────────────────────────────── */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
}

/* ─────────────────────────────────────────────
   Sidebar
   ───────────────────────────────────────────── */
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  border-right: 1px solid rgba(255, 255, 255, 0.04);
  z-index: 50;
}

.sidebar-brand {
  padding: 1.25rem 1rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.brand-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-sub {
  font-size: 0.7rem;
  color: var(--sidebar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ─────────────────────────────────────────────
   Nav items
   ───────────────────────────────────────────── */
.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.625rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
  white-space: nowrap;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--sidebar-text-hover);
}

.nav-item.active {
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-text-active);
}

.nav-item.active .nav-icon {
  color: var(--sidebar-accent);
}

.nav-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  opacity: 0.8;
}

.nav-item.active .nav-icon {
  opacity: 1;
}

/* ─────────────────────────────────────────────
   Sidebar footer
   ───────────────────────────────────────────── */
.sidebar-footer {
  padding: 0.75rem 0.625rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

/* ─────────────────────────────────────────────
   Main area
   ───────────────────────────────────────────── */
.main-area {
  display: flex;
  flex-direction: column;
  background: var(--surface-bg);
  min-height: 100vh;
  overflow-x: hidden;
}

.content-topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--surface-bg);
  border-bottom: 1px solid var(--surface-border);
  padding: 0.5rem 1.5rem;
}

.page-content {
  flex: 1;
  padding: var(--space-page);
  width: 100%;
  max-width: 1400px;
}
```

---

## Light Sidebar Variant

Switch these token values and the sidebar border rule. Everything else is the same.

### Token overrides (replace in `:root`)

```css
:root {
  --sidebar-bg: #ffffff;
  --sidebar-text: #64748b;
  --sidebar-text-hover: #0f172a;
  --sidebar-text-active: #1d4ed8;
  --sidebar-item-active-bg: #eff6ff;
  --sidebar-accent: #2563eb;
}
```

### CSS change

Replace `border-right: 1px solid rgba(255, 255, 255, 0.04)` on `.sidebar` with:

```css
.sidebar {
  border-right: 1px solid var(--surface-border);
}
```

And replace `.sidebar-brand` and `.sidebar-footer` border colours:

```css
.sidebar-brand {
  border-bottom: 1px solid var(--surface-border);
}
.sidebar-footer {
  border-top: 1px solid var(--surface-border);
}
```

Active item uses a left accent bar instead of a background pill:

```css
/* Light sidebar only — add inside active overrides */
.nav-item.active {
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-text-active);
  box-shadow: inset 3px 0 0 var(--sidebar-accent);
  border-radius: 0 6px 6px 0;
  padding-left: calc(0.75rem - 3px); /* compensate for box-shadow inset */
}
```

---

## FilterBar Integration Notes

The existing `FilterBar` component sits as a block-level element in the new `.content-topbar`. No changes are needed inside `FilterBar.vue` itself — only its wrapping context changes.

If FilterBar has its own background or border styles that conflict, override via:

```css
.content-topbar .filter-bar {
  background: transparent;
  border: none;
  padding: 0;
}
```

---

## LanguageSwitcher and ProfileMenu in the Footer

Both components were previously positioned with flex margins in `.nav-container`. In the sidebar footer they naturally share the `.sidebar-footer` flex row. If either component has hard-coded dark/light assumptions (e.g. hardcoded `color: #0f172a`), you may need to pass a `variant="sidebar"` prop or override via:

```css
/* Dark sidebar variant — force light text on footer components */
.sidebar-footer .language-switcher,
.sidebar-footer .profile-menu {
  color: var(--sidebar-text);
}
```
