---
name: vue-saas-redesign
description: This skill should be used when the user asks to "redesign the UI", "add a sidebar", "switch to vertical navigation", "modernize the interface", "SaaS-style redesign", "replace the top nav bar with a sidebar", "give it a sidebar layout", or wants to transform a Vue 3 app's layout into a professional SaaS aesthetic with consistent spacing and a polished look.
version: 0.1.0
---

# Vue 3 SaaS UI Redesign

Transform a Vue 3 application from a top navigation bar layout into a polished SaaS-style interface with a fixed vertical sidebar, consistent design tokens, and a professional look modeled on tools like Linear, Vercel, and Notion.

## What This Skill Does

1. Replaces the horizontal top nav bar with a fixed vertical sidebar
2. Establishes a CSS design token system (colors, spacing, radius, typography)
3. Updates global component styles (`.card`, `.badge`, `.stat-card`, tables) to use the new tokens
4. Ensures consistent page-level structure and spacing across all views

The change is **contained in `App.vue`** — individual view files are not touched unless a Phase 5 audit reveals a spacing conflict.

---

## Phase 1: Audit the Existing Structure

Read these files before making any changes:

- `src/App.vue` — Current layout structure, nav links, all global CSS classes
- `src/main.js` — Router configuration and route paths
- One representative view (e.g. `src/views/Dashboard.vue`) — How views use global CSS classes

During the audit, identify:
- All navigation routes, their paths, and display labels
- Any i18n translation keys used in the nav (e.g. `t('nav.overview')`) — preserve these exactly
- Global CSS classes views depend on (`.card`, `.badge`, `.stats-grid`, `.loading`, `.error`, `.badge.success`, etc.) — these must survive the rewrite
- Any existing CSS variables or hardcoded color values to migrate

---

## Phase 2: Choose a Design Direction

Before writing any code, choose a sidebar style. The two most common are:

**Dark sidebar** — Slate/navy background with light text. Feels focused and professional (Linear, Vercel).
```
Sidebar bg:  #0f172a  |  Active item: #3b82f6 (blue)
Body bg:     #f8fafc  |  Card bg:     #ffffff
```

**Light sidebar** — White background with a right border. Feels clean and minimal (Notion, Figma).
```
Sidebar bg:  #ffffff + border-right: 1px solid #e2e8f0
Active item: #eff6ff with #2563eb text
Body bg:     #f8fafc
```

Both variants are fully detailed in `references/sidebar-layout.md`. Default to **dark sidebar** unless the existing app uses a light theme throughout.

---

## Phase 3: Implement the Sidebar in App.vue

Replace the existing `<template>` with a two-column grid layout:

```html
<div class="app-shell">
  <aside class="sidebar">
    <div class="sidebar-brand">
      <!-- Logo / app name -->
    </div>
    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="['nav-item', { active: $route.path === item.path }]"
      >
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <!-- Profile menu, language switcher, etc. -->
    </div>
  </aside>

  <div class="main-area">
    <main class="page-content">
      <router-view />
    </main>
  </div>
</div>
```

Define `navItems` as a computed array in `setup()` using the routes from `main.js` and the existing i18n label calls. Move any `ProfileMenu`, `LanguageSwitcher`, or modal components that were in the old top bar into the sidebar footer or a new slim top bar inside `.main-area`.

Core layout CSS:

```css
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
}

.main-area {
  display: flex;
  flex-direction: column;
  background: var(--surface-bg);
  min-height: 100vh;
  overflow-x: hidden;
}

.page-content {
  flex: 1;
  padding: var(--space-page);
  width: 100%;
  max-width: 1400px;
}
```

See `references/sidebar-layout.md` for complete CSS including active state transitions, hover effects, brand header, footer, and the light-sidebar variant.

---

## Phase 4: Establish Design Tokens

Add a `:root` block at the top of the `<style>` section in App.vue (not scoped). These tokens are inherited by all views.

Minimum required token set:

```css
:root {
  /* Layout */
  --sidebar-width: 240px;

  /* Sidebar (dark variant) */
  --sidebar-bg: #0f172a;
  --sidebar-text: #94a3b8;
  --sidebar-text-hover: #e2e8f0;
  --sidebar-text-active: #ffffff;
  --sidebar-item-active-bg: rgba(59, 130, 246, 0.15);
  --sidebar-accent: #3b82f6;

  /* Surfaces */
  --surface-bg: #f8fafc;
  --surface-card: #ffffff;
  --surface-border: #e2e8f0;
  --surface-hover: #f1f5f9;

  /* Text */
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;

  /* Spacing */
  --space-page: 2rem;
  --space-card: 1.25rem;
  --space-gap: 1.25rem;

  /* Shape */
  --radius-card: 10px;
  --radius-badge: 6px;
  --radius-btn: 8px;

  /* Shadows */
  --shadow-card: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.04);
}
```

After adding tokens, update the existing global CSS classes to reference them. For example:

```css
/* Before */
.card { background: white; border-radius: 10px; border: 1px solid #e2e8f0; }

/* After */
.card { background: var(--surface-card); border-radius: var(--radius-card); border: 1px solid var(--surface-border); }
```

See `references/design-tokens.md` for extended palettes, typography scale, component style patterns, and a dark-mode variant.

---

## Phase 5: View-Level Consistency Audit

After the sidebar is in place, scan each view for these common issues:

| Issue | Check | Fix |
|---|---|---|
| Extra top padding | View has `padding-top` compensating for old nav bar height | Remove it |
| Broken page header | `<h2>` is missing or unstyled | Ensure `.page-header h2` styles exist globally |
| Horizontal overflow | Table or chart wider than viewport | Add `overflow-x: auto` to `.table-container` |
| Missing active route | Sidebar item not highlighted on that page | Confirm `$route.path === item.path` logic covers nested paths |

Avoid editing view files for purely visual tweaks — fix via global CSS in App.vue instead.

---

## Phase 6: Verify in Browser

After implementing, check:

1. App loads at `http://localhost:3000` with sidebar visible
2. Every nav item routes correctly — click each one
3. Active state highlights the correct sidebar item on every page
4. Existing functionality (filters, tables, charts, modals) is unaffected
5. No horizontal scroll on any page
6. Global elements (FilterBar, ProfileMenu, LanguageSwitcher) are accessible

---

## Critical Constraints

- **Preserve all existing global CSS classes.** Views use `.card`, `.badge`, `.stats-grid`, `.loading`, `.error`, `.badge.success/warning/danger/info`. Never delete them — only update their property values.
- **Do not modify individual view files** unless Phase 5 reveals a concrete layout break. Sidebar layout changes belong in App.vue.
- **Keep all i18n calls.** Do not hardcode nav labels — keep `t('nav.*')` calls and add any new keys to all locale files.
- **CLAUDE.md rule:** If the project's CLAUDE.md mandates delegating `.vue` file changes to `vue-expert`, follow that rule for App.vue and any modified view.

---

## Additional Resources

### Reference Files

- **`references/sidebar-layout.md`** — Complete App.vue template and CSS for both dark and light sidebar variants, including brand header, nav items with icons, footer section, active states, hover transitions, and FilterBar integration
- **`references/design-tokens.md`** — Extended CSS token system, color palette options, typography scale, component-level styles (cards, tables, badges, buttons, stat cards), animation values, and dark mode variant
