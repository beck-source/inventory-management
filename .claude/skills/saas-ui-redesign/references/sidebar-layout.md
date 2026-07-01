# Sidebar Layout — target App.vue shell

This is the reference target for converting `client/src/App.vue` from a sticky **top nav** to a
**left vertical sidebar** SaaS layout. It is a template to adapt, not a verbatim paste — preserve
the app's real component wiring, i18n keys, and events (see the preservation checklist in SKILL.md).

## Current shell (what you are replacing)

```
.app (flex column)
├── header.top-nav (sticky top:0, z 100)  →  .nav-container (max 1600px, 70px)
│     .logo · nav.nav-tabs (horizontal router-links) · <LanguageSwitcher> · <ProfileMenu>
├── <FilterBar />        (sticky top:70px, z 90)
└── main.main-content    (max 1600px, padding 1.5rem 2rem) → <router-view>
```

## Target shell

```
.app (flex row)
├── aside.sidebar (fixed width, full height, z --z-sidebar)
│     .sidebar-brand   → logo + subtitle
│     nav.sidebar-nav  → vertical router-links (icon + label)
│     .sidebar-footer  → <LanguageSwitcher> + <ProfileMenu>
└── .main (flex column, flex:1, min-width:0)
      <FilterBar />           (sticky top:0, z --z-filterbar)
      main.main-content       (max --content-max, centered) → <router-view>
```

## Template

```vue
<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="subtitle">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" :class="{ active: $route.path === '/' }"
                     :aria-current="$route.path === '/' ? 'page' : null">
          {{ t('nav.overview') }}
        </router-link>
        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }"
                     :aria-current="$route.path === '/inventory' ? 'page' : null">
          {{ t('nav.inventory') }}
        </router-link>
        <router-link to="/orders" :class="{ active: $route.path === '/orders' }"
                     :aria-current="$route.path === '/orders' ? 'page' : null">
          {{ t('nav.orders') }}
        </router-link>
        <router-link to="/spending" :class="{ active: $route.path === '/spending' }"
                     :aria-current="$route.path === '/spending' ? 'page' : null">
          {{ t('nav.finance') }}
        </router-link>
        <router-link to="/demand" :class="{ active: $route.path === '/demand' }"
                     :aria-current="$route.path === '/demand' ? 'page' : null">
          {{ t('nav.demandForecast') }}
        </router-link>
        <router-link to="/reports" :class="{ active: $route.path === '/reports' }"
                     :aria-current="$route.path === '/reports' ? 'page' : null">
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

    <div class="main">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- Modals stay at app root, above the sidebar -->
    <ProfileDetailsModal :is-open="showProfileDetails" @close="showProfileDetails = false" />
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

The `<script>` block is unchanged — the same imports, `setup()`, task handlers, and returns.
Only the template and `<style>` change.

## Shell CSS (uses tokens from design-tokens.md)

```css
.app {
  display: flex;
  min-height: 100vh;
}

/* ---- Sidebar ---- */
.sidebar {
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
  width: var(--sidebar-width);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
}

.sidebar-brand {
  padding: var(--space-6) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.sidebar-brand h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-strong);
  letter-spacing: -0.025em;
}
.sidebar-brand .subtitle {
  display: block;
  margin-top: var(--space-1);
  font-size: 0.813rem;
  color: var(--color-text-muted);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
  flex: 1;
  overflow-y: auto;
}
.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  transition: all 0.15s ease;
}
.sidebar-nav a:hover {
  color: var(--color-text-strong);
  background: var(--color-bg);
}
.sidebar-nav a.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-weight: 600;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid var(--color-border);
}

/* ---- Main column ---- */
.main {
  flex: 1;
  min-width: 0;              /* prevents flex overflow of wide tables */
  display: flex;
  flex-direction: column;
}
.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

/* ---- Responsive: collapse to icon rail, then off-canvas ---- */
@media (max-width: 1024px) {
  .sidebar { width: var(--sidebar-width-collapsed); }
  .sidebar-brand .subtitle,
  .sidebar-nav a span.label { display: none; }   /* keep icons if present */
}
```

## FilterBar repositioning

`FilterBar.vue` currently sticks at `top: 70px` (below the old header). In the new layout there
is no top header, so it sticks to the top of the main column:

- Change `.filters-bar { position: sticky; top: 70px; z-index: 90; }`
  → `top: 0; z-index: var(--z-filterbar);`
- Drop the old `max-width: 1600px` centering if the bar should span the main column; otherwise
  align its inner container to `--content-max` to match `.main-content`.

## Dropdown positioning note

`ProfileMenu.vue` and `LanguageSwitcher.vue` open dropdowns with `position: absolute; top:
calc(100% + 0.5rem); right: 0`. In the sidebar footer they should open **upward / rightward** so
they aren't clipped at the bottom-left of the viewport — e.g. `bottom: calc(100% + 0.5rem); left: 0`.
Ensure their `z-index` uses `var(--z-dropdown)` (above the sidebar, below modals).
