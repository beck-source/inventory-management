---
description: Redesign the Vue 3 app UI into a modern SaaS-style interface with a vertical navigation sidebar
---

Redesign this Vue 3 application's UI into a modern SaaS-style interface. Replace the top navigation bar with a fixed vertical sidebar on the left, apply consistent spacing and typography, and give the whole app a polished professional look.

## Step 1 — Explore the codebase

Before making any changes, use the Explore subagent to gather:
- The contents of `client/src/App.vue` (full layout, nav, global styles)
- The router configuration in `client/src/main.js` (all routes and their paths)
- The list of all `.vue` files under `client/src/views/` and `client/src/components/`
- Any existing design tokens (colors, fonts) defined in global `<style>` blocks or CSS files

Report back what you found so the design decisions below can be applied accurately.

## Step 2 — Plan the redesign

Based on what you found, identify:
1. The component that owns the top nav bar (usually `App.vue`)
2. Every nav link that needs to move to the sidebar
3. Any modals, overlays, or header-fixed elements that need z-index adjustments
4. Global CSS classes that control layout (`.app`, `.main-content`, `.top-nav`, etc.)

## Step 3 — Execute via vue-expert

**MANDATORY:** Delegate ALL `.vue` file changes to the vue-expert subagent. Pass it the full codebase context you collected in Step 1 so it can make accurate edits without re-reading files.

### Design specification to give vue-expert

The vue-expert must implement the following design system:

---

#### Layout structure

```
┌─────────────────────────────────────────────────┐
│  Sidebar (240px fixed)  │  Main content area     │
│                         │                        │
│  [Logo / Brand]         │  [Page content]        │
│                         │                        │
│  Navigation links       │  (scrollable)          │
│  (one per route)        │                        │
│                         │                        │
│  [User profile]         │                        │
│  (pinned to bottom)     │                        │
└─────────────────────────────────────────────────┘
```

- Sidebar: `position: fixed`, full viewport height, `width: 240px`, left: 0, top: 0
- Main content: `margin-left: 240px`, `min-height: 100vh`, `padding: 28px 32px`
- Sidebar does NOT scroll; main content scrolls independently

#### Sidebar design

```css
/* Sidebar shell */
background: #ffffff;
border-right: 1px solid #e2e8f0;
box-shadow: 1px 0 0 0 #f1f5f9;
display: flex;
flex-direction: column;
```

**Brand section** (top of sidebar, ~64px tall):
```css
padding: 0 20px;
height: 64px;
display: flex;
align-items: center;
border-bottom: 1px solid #f1f5f9;
```
- Company name: `font-size: 15px; font-weight: 700; color: #0f172a; letter-spacing: -0.02em`
- Subtitle/tagline below name: `font-size: 11px; color: #94a3b8; font-weight: 400`

**Nav section** (fills remaining space):
```css
padding: 12px 12px;
flex: 1;
overflow-y: auto;
```

Each nav link:
```css
/* Default state */
display: flex;
align-items: center;
gap: 10px;
padding: 9px 12px;
border-radius: 7px;
font-size: 14px;
font-weight: 500;
color: #475569;
text-decoration: none;
margin-bottom: 2px;
transition: background 0.15s, color 0.15s;

/* Hover */
background: #f8fafc;
color: #0f172a;

/* Active (current route) */
background: #eff6ff;
color: #2563eb;
font-weight: 600;
```

Each nav link must include a small SVG icon (16×16) before the label. Use these inline SVG paths — one per route type:

- Dashboard/Overview: `<path d="M3 13h2v-2H3v2zm0-4h2V7H3v2zm0-4h2V3H3v2zm4 8h10v-2H7v2zm0-4h10V7H7v2zm0-4V3H7v2h10V3H7z"/>`  (or a grid icon: `M3 3h7v7H3zm0 8h7v7H3zm8-8h7v7h-7zm0 8h7v7h-7z`)
- Inventory: `M20 4H4v2l8 5 8-5V4zM4 9.236V20h16V9.236l-8 5z` (box/package)
- Orders: `M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2` (clipboard)
- Finance/Spending: `M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z`
- Demand: `M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z` (trend line)
- Reports: `M9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4zm2.5 2.1h-15V5h15v14.1zm0-16.1h-15c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h15c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z` (bar chart)
- Restocking: `M17 16l-4-4V8.82C14.16 8.4 15 7.3 15 6c0-1.66-1.34-3-3-3S9 4.34 9 6c0 1.3.84 2.4 2 2.82V12l-4 4H3v3h18v-3h-4z` (restock/refresh)
- Backlog: `M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z` (or use a warning icon)
- Settings/generic: `M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.57 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.21.08-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z`

SVG icon wrapper:
```html
<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="flex-shrink:0; opacity:0.7">
  <path d="..."/>
</svg>
```

**User profile section** (pinned to bottom of sidebar):
```css
padding: 12px;
border-top: 1px solid #f1f5f9;
```
Move any existing profile menu / avatar / language switcher here. Show:
- Avatar circle (initials, 32px, `background: #eff6ff; color: #2563eb`)
- Name and role text beside it
- Existing profile dropdown still works

If there's a FilterBar component shown globally, place it **above the page content** (inside the main content area, not in the sidebar), as a horizontal strip with `margin-bottom: 20px`.

#### Main content area

```css
.main-content {
  margin-left: 240px;
  min-height: 100vh;
  padding: 28px 32px;
  background: #f8fafc;
  max-width: none; /* remove max-width constraint */
}
```

Page header style (apply globally to `.page-header h2`):
```css
font-size: 22px;
font-weight: 700;
color: #0f172a;
letter-spacing: -0.02em;
margin-bottom: 4px;
```

#### Card style upgrade

Update global `.card`:
```css
background: white;
border-radius: 12px;
padding: 20px 24px;
border: 1px solid #e8edf4;
box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
margin-bottom: 20px;
```

Update `.stat-card`:
```css
background: white;
padding: 20px 24px;
border-radius: 12px;
border: 1px solid #e8edf4;
box-shadow: 0 1px 3px rgba(0,0,0,0.04);
transition: box-shadow 0.2s;
```

`.stat-card:hover`:
```css
box-shadow: 0 4px 12px rgba(0,0,0,0.08);
border-color: #cbd5e1;
```

#### Remove / replace

- Delete the `.top-nav` / `<header>` bar entirely
- Delete `.nav-container`, `.nav-tabs` global styles (they're replaced by sidebar)
- The `<FilterBar />` component stays but moves to inside `<main>` before `<router-view />`

---

### Preserve all functionality

- Every route, component import, event handler, and composable must remain exactly as-is
- Only layout, positioning, and visual styles change
- The router-links in the sidebar must use the same paths as before
- All modals must still work (ensure z-index: sidebar is z-index 50, modals are z-index 200+)
- No emojis in the UI

### Summary of files to modify

1. `client/src/App.vue` — main layout restructure (top nav → sidebar, move FilterBar into main)
2. Any global CSS that controls `.top-nav`, `.nav-container`, `.nav-tabs` layout — remove/replace in `App.vue`'s `<style>` block
3. Do NOT modify any view components (`views/*.vue`) or other components unless a specific layout fix is needed

After completing all changes, confirm what was changed and suggest running the dev server to verify.
