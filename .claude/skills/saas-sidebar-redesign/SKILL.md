---
name: saas-sidebar-redesign
description: Use this skill when you need to redesign a Vue 3 app's UI from a horizontal top-nav layout into a modern SaaS-style interface — a vertical left navigation sidebar, a consistent design-token system for spacing/color/radius, and an overall polished, professional look. Use it for requests like "redesign this into a SaaS dashboard layout", "convert the top nav to a sidebar", "give this app a modern SaaS look", or "add design tokens and clean up spacing/consistency".
---

# SaaS Sidebar Redesign

This skill converts a Vue 3 app's horizontal top-nav shell into a modern SaaS-style vertical sidebar layout, backed by a real design-token system and a deliberate card-elevation hierarchy. It's a general, reusable procedure — it doesn't assume any particular app's file names, only common Vue 3 conventions (a root layout component, `<router-link>` nav, scoped or global `<style>` blocks).

## When to use / when not to use

Use this for shell/nav redesigns and visual-consistency passes: "convert the top nav to a sidebar," "make this look more like a modern SaaS dashboard," "clean up the spacing," "add design tokens." Don't use it to add new features or views, and don't introduce a UI framework (Tailwind, Vuetify, etc.) unless the user asks for one — this skill works with whatever the app already uses (plain scoped/global CSS in most Vue 3 apps).

> **This skill produces a plan and a design-system checklist — it never edits `.vue` files itself.** If the project's own CLAUDE.md (or equivalent guidance) mandates delegating `.vue` edits to a specialized subagent, follow that: identify every file that needs changes, then hand the concrete instructions (full template + CSS, not a vague summary) to that subagent via the Task tool. Don't use Edit/Write on `.vue` files directly from this skill.

## Step 1 — Audit & discovery

Before touching anything, understand what's actually there:

- **Find the layout entry point.** Usually the root component mounted in `main.js` (often `App.vue`). Look for the current nav markup: `grep -rn "top-nav\|navbar\|<nav" src/App.vue src/components`.
- **Check for an existing design-token system.** `grep -rn "^\s*--[a-z-]" src` for a `:root { --... }` block. If none exists, you'll derive one from the app's current hardcoded values (see Step 2) — never invent a new palette.
- **Inventory sticky/fixed elements with header-height magic numbers.** Search for `position: sticky` / `position: fixed` plus a hardcoded `top: <N>px`. Anything positioned relative to the old horizontal header's height will break once that header becomes a sidebar — this is the single easiest thing to miss.
- **Find secondary header chrome.** Search bars, profile/account menus, locale switchers, filter bars — anything currently living inside the horizontal nav that will need a new home.
- **Confirm views don't hardcode header offsets themselves.** Route-level components should only consume shared/global classes (page headers, cards, etc.), not reference the nav directly. Flag any that do rather than silently changing them.

## Step 2 — Establish a design-token system

Derive tokens from the app's *existing* palette — don't invent a new one. Pull the actual hex/rem values you found in Step 1 into a `:root` block:

```css
:root {
  /* Color — use the exact values already in use across the app */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text-primary: #0f172a;
  --color-text-muted: #64748b;
  --color-brand: #2563eb;
  --color-brand-light: #eff6ff;
  --color-success: #059669;
  --color-warning: #ea580c;
  --color-danger: #dc2626;

  /* Spacing — 4px scale; reuse the app's existing rem values, don't renumber them */
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem;
  --space-4: 1rem; --space-5: 1.25rem; --space-6: 1.5rem; --space-8: 2rem;

  /* Radius / shadow */
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 10px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,.06);

  /* Layout */
  --sidebar-width: 260px;
  --topbar-height: 64px;
}
```

Place this block at the top of whatever file is the app's de facto global stylesheet (the root layout component's unscoped `<style>`, or a dedicated CSS file if one exists). Existing rules should keep working unchanged during this pass — only the shell/nav CSS gets a full rewrite in Step 3.

## Step 3 — Convert the shell to a sidebar layout

**Before:** root wrapper is `display: flex; flex-direction: column` with a horizontal `<header>` above the routed content.

**After:** root wrapper becomes `display: flex; flex-direction: row` — a sidebar and a content column (which itself stacks vertically).

Template shape:

```html
<div class="app-shell">
  <aside class="sidebar">
    <div class="sidebar-header"><!-- logo / brand --></div>
    <nav class="sidebar-nav">
      <!-- one router-link per route, icon + label -->
    </nav>
    <div class="sidebar-footer"><!-- optional: locale switcher, settings, etc. --></div>
  </aside>
  <div class="app-main">
    <header class="content-topbar"><!-- profile menu, search, etc. --></header>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</div>
```

Shell CSS:

```css
.app-shell { display: flex; min-height: 100vh; }

.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0.625rem var(--space-4);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  border-radius: var(--radius-sm);
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
}

.sidebar-link:hover {
  color: var(--color-text-primary);
  background: var(--color-border-subtle, var(--color-bg));
}
```

**Active-state indicator:** a bottom-underline `::after` (the standard horizontal-tab pattern) doesn't read correctly in a vertical list. Replace it with a **left-border accent + filled pill background**:

```css
.sidebar-link.active {
  color: var(--color-brand);
  background: var(--color-brand-light);
  border-left-color: var(--color-brand);
  font-weight: 600;
}
```

Preserve whatever active-route detection the app already uses (a `$route.path === '/...'` comparison per link, or the framework's built-in `router-link-active` class) — don't switch mechanisms, just restyle.

## Step 4 — Relocate secondary chrome

Anything that assumed a horizontal header — search bars, filter bars, profile/account menus, locale switchers — moves into a slim in-content topbar inside the content column, not into the sidebar itself:

```css
.content-topbar {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  height: var(--topbar-height);
  padding: 0 var(--space-6);
  gap: var(--space-3);
}
```

**The #1 easy-to-miss bug:** any element that was `position: sticky` with a `top: <old-header-height>px` offset (e.g. a filter bar sitting just below the old nav) must be recomputed against the *new* topbar height (`var(--topbar-height)`), not the old header height, and its `z-index` must sit below the topbar's. Revisit everything flagged in Step 1's sticky/fixed inventory.

## Step 5 — Card elevation hierarchy (not one shadow on everything)

Avoid the generic "identical rounded cards, same flat grey shadow on every one of them" pattern. Differentiate by importance instead:

- Dense, repeated tiles (KPI/stat cards): flat — border only, no shadow, even on hover.
- Primary content cards (tables, charts, detail panels): border + shadow **on hover only** — this signals the card holds interactive content rather than statically decorating it.

```css
.stat-card { border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.stat-card:hover { border-color: var(--color-border-strong); }

.card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: box-shadow 0.2s ease;
}
.card:hover { box-shadow: var(--shadow-md); }
```

## Step 6 — Spacing & consistency pass

Swap ad hoc rem values for the token spacing scale (`var(--space-*)`) across page headers, cards, and the new shell — this pass is mechanical (find/replace) and safe to do broadly, not just in shell files.

## Step 7 — Icons

If the app has no icon library, reuse whatever inline-SVG stroke convention already exists elsewhere in the app (same `stroke-width`, `currentColor`, viewBox proportions) rather than adding a new dependency. A clean text-only link list is an acceptable fallback if no existing icon convention is found, or if the user prioritizes speed over polish.

## Step 8 — Delegate the actual edits

Give the subagent (or yourself, if no delegation rule applies) the concrete file list plus the full template/CSS to apply — not a vague "redesign this" instruction — so the audit doesn't need to be redone. Batch all shell files into one change so the visual result lands consistently rather than in a half-migrated state.

## Step 9 — Verification

- Start the dev server and load every route.
- Confirm active-link styling matches the current route.
- Confirm previously-sticky secondary chrome no longer overlaps or gaps against the new topbar height.
- Check the browser console for errors.
- Confirm layout doesn't break at the app's normal content widths.

## Optional / stretch enhancements

These are **not** applied by default — only build them if the user explicitly asks:

**Collapsible sidebar with icons-only mode.** Add a toggle button (usually in the sidebar header or footer) that shrinks the sidebar to an icon-only rail:

```css
.sidebar { width: var(--sidebar-width); transition: width 0.2s ease; }
.sidebar.collapsed { width: 64px; }
.sidebar.collapsed .sidebar-link span,
.sidebar.collapsed .logo .subtitle,
.sidebar.collapsed .sidebar-footer span { display: none; }
.sidebar.collapsed .sidebar-link { justify-content: center; padding: 0.625rem; }
```

```html
<button class="sidebar-toggle" @click="collapsed = !collapsed" :aria-expanded="!collapsed" aria-label="Toggle sidebar">
  <!-- chevron/hamburger icon -->
</button>
```

Persist the collapsed state per-user if the app already has a place for local UI preferences (e.g. `localStorage`); otherwise a plain reactive `ref` reset on reload is fine. When collapsed, add a `title` attribute to each `.sidebar-link` (or a tooltip) so labels remain discoverable on hover, since only the icon is visible.

Other stretch items in the same spirit — also default-off unless asked: a mobile hamburger fallback (`< 768px` breakpoint that hides the sidebar behind a slide-over toggle), breadcrumbs in the topbar, dark mode via a `[data-theme]` token override.

## Quick-reference checklist

1. Audit: layout entry point, existing tokens (or lack thereof), sticky/fixed header-height assumptions, secondary chrome, view-level header coupling.
2. Design tokens: `:root` block derived from existing values (color, spacing, radius, shadow, `--sidebar-width`, `--topbar-height`).
3. Shell conversion: row-flex `.app-shell`, `<aside class="sidebar">`, active state = left border + filled pill (not underline).
4. Relocate chrome: slim `.content-topbar`; recompute any sticky offsets against the new topbar height.
5. Card hierarchy: flat stat cards, hover-only shadow on content cards.
6. Spacing pass: token-ize ad hoc values.
7. Icons: reuse existing convention or stay text-only.
8. Delegate the actual file edits with concrete instructions.
9. Verify: every route, active state, no console errors, no layout breakage.
10. Stretch (only if asked): collapsible/icons-only sidebar, mobile hamburger, breadcrumbs, dark mode.
