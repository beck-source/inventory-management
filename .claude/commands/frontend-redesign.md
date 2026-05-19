# Skill: frontend-redesign

You are redesigning a Vue 3 application's UI into a modern SaaS-style interface.

## What This Skill Does
Converts a horizontal top navigation bar into a fixed vertical sidebar on the left, shifts main content to fill the remaining space, and applies polished SaaS-style spacing and typography — without changing any application logic or functionality.

## Steps to Execute

### 1. Inventory the current layout
Read these files before making any changes:
- `client/src/App.vue` — current nav structure and global styles
- `client/src/components/FilterBar.vue` — current sticky positioning

### 2. Rewrite App.vue layout

Replace the `<header class="top-nav">` block with `<aside class="sidebar">`.

**Sidebar structure:**
```html
<aside class="sidebar" :class="{ collapsed }">
  <!-- Top: logo + toggle -->
  <div class="sidebar-header">
    <div class="sidebar-logo" v-if="!collapsed">
      <h1>{{ companyName }}</h1>
      <span class="sidebar-subtitle">{{ subtitle }}</span>
    </div>
    <button class="sidebar-toggle" @click="collapsed = !collapsed">
      <!-- chevron SVG -->
    </button>
  </div>

  <!-- Nav links -->
  <nav class="sidebar-nav">
    <router-link v-for="item in navItems" :to="item.path" :class="{ active: $route.path === item.path }">
      <!-- SVG icon -->
      <span class="nav-label" v-if="!collapsed">{{ t(item.key) }}</span>
    </router-link>
  </nav>

  <!-- Bottom: profile + language -->
  <div class="sidebar-footer">
    <LanguageSwitcher />
    <ProfileMenu @show-profile="showProfileDetails = true" @show-tasks="showTasks = true" />
  </div>
</aside>
```

**Main content shift:**
```html
<div class="app-body" :class="{ 'sidebar-collapsed': collapsed }">
  <FilterBar />
  <main class="main-content">
    <router-view />
  </main>
</div>
```

**CSS rules to add/replace:**
```css
.sidebar {
  position: fixed;
  left: 0; top: 0;
  width: 220px; height: 100vh;
  background: #0f172a;
  display: flex; flex-direction: column;
  transition: width 0.2s ease;
  z-index: 100;
  overflow: hidden;
}
.sidebar.collapsed { width: 64px; }

.app-body {
  margin-left: 220px;
  transition: margin-left 0.2s ease;
  min-height: 100vh;
  display: flex; flex-direction: column;
}
.app-body.sidebar-collapsed { margin-left: 64px; }

.sidebar-nav a {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px;
  color: #94a3b8;
  text-decoration: none;
  border-radius: 6px;
  margin: 2px 8px;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}
.sidebar-nav a:hover { background: #1e293b; color: #e2e8f0; }
.sidebar-nav a.active { background: #2563eb; color: #fff; }

.nav-label { font-size: 0.875rem; font-weight: 500; }
```

### 3. Update FilterBar.vue

Remove sticky positioning — it now renders inline at the top of the content area:

**Remove:**
```css
position: sticky;
top: 70px;
z-index: 90;
```

**Keep everything else unchanged.**

### 4. Nav Icons

Use these inline SVGs for each route (16×16, `currentColor`):

| Route | Icon shape |
|-------|-----------|
| `/` (Overview) | Grid/squares |
| `/inventory` | Box/cube |
| `/orders` | List/clipboard |
| `/spending` | Chart bar |
| `/demand` | Trending up arrow |
| `/reports` | Document |

### 5. Verify

After changes:
- [ ] Sidebar visible on left, content fills right
- [ ] All 6 nav links work with correct active states
- [ ] FilterBar renders inline (not sticky)
- [ ] Collapse toggle works: 220px ↔ 64px, labels hide/show
- [ ] No layout overflow on any page

## Design Tokens (do not change these)
- Sidebar bg: `#0f172a`
- Active nav: `#2563eb` bg, white text
- Inactive nav: `#94a3b8` text
- Content bg: `#f8fafc`
- Border: `#e2e8f0`
