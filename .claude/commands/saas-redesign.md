---
description: Redesign a Vue 3 app into a modern SaaS UI with a vertical sidebar, consistent spacing, and a polished professional look
---

Redesign this Vue 3 application's UI into a modern SaaS-style interface. The goal is a professional, clean look inspired by tools like Linear, Vercel, and Notion — dark sidebar, light content area, consistent spacing system.

## Phase 1 — Explore the current structure

Before touching any file, read and understand:

1. `client/src/App.vue` — current root layout, nav, global styles
2. `client/src/main.js` — router setup and existing routes
3. All files in `client/src/views/` — understand what each page contains
4. All files in `client/src/components/` — identify reusable components
5. Note the current color palette and design tokens in use

Use the Explore subagent for this phase.

## Phase 2 — Redesign the shell (App.vue)

Replace the top navigation bar with a **vertical sidebar layout**. Delegate to the `vue-expert` subagent.

### Target layout structure:

```
┌─────────────────────────────────────────────┐
│  Sidebar (240px fixed)  │  Main content area │
│  ─────────────────────  │  ─────────────────  │
│  Logo / App name        │  <router-view>      │
│                         │                     │
│  Nav items (vertical):  │  Page header        │
│  • Overview             │  Filter bar (if any)│
│  • Inventory            │  Content            │
│  • Orders               │                     │
│  • Finance              │                     │
│  • Demand Forecast      │                     │
│  • Reports              │                     │
│  • Restocking           │                     │
│                         │                     │
│  ─────────────────────  │                     │
│  User profile (bottom)  │                     │
└─────────────────────────────────────────────┘
```

### Sidebar design specs:
- Width: 240px, fixed, full viewport height
- Background: #0f172a (near-black slate)
- Logo area: 56px tall, app name in white, 600 weight
- Nav items: 36px tall, 12px horizontal padding, 8px vertical padding
- Active item: #1e293b background, white text, left border accent (#3b82f6, 3px)
- Inactive item: #94a3b8 text, hover → #e2e8f0 text + #1e293b background
- Bottom section: user avatar + name + settings icon, separated by a top border
- No icons required — text-only nav is fine

### Main content area:
- Background: #f8fafc
- Left margin: 240px (sidebar width)
- Padding: 32px
- Max content width: 1200px

### Global spacing system (apply via CSS variables in App.vue):
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-6: 24px;
--space-8: 32px;
--space-12: 48px;

--radius-sm: 6px;
--radius-md: 8px;
--radius-lg: 12px;

--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04);

--color-bg: #f8fafc;
--color-surface: #ffffff;
--color-border: #e2e8f0;
--color-text: #0f172a;
--color-muted: #64748b;
--color-accent: #3b82f6;
```

## Phase 3 — Polish the content views

Delegate to `vue-expert`. Apply consistent patterns across all views:

### Card style:
```css
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}
```

### Page header pattern (apply to every view):
```html
<div class="page-header">
  <h1 class="page-title">Page Name</h1>
  <p class="page-subtitle">Short description of this page</p>
</div>
```
```css
.page-header { margin-bottom: var(--space-8); }
.page-title { font-size: 1.5rem; font-weight: 600; color: var(--color-text); }
.page-subtitle { font-size: 0.875rem; color: var(--color-muted); margin-top: var(--space-1); }
```

### Table style:
```css
table { width: 100%; border-collapse: collapse; }
th { font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
     letter-spacing: 0.05em; color: var(--color-muted); padding: var(--space-3) var(--space-4);
     border-bottom: 1px solid var(--color-border); text-align: left; }
td { padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--color-border);
     font-size: 0.875rem; color: var(--color-text); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f8fafc; }
```

### Badge style:
```css
.badge { display: inline-flex; align-items: center; padding: 2px 10px;
         border-radius: 99px; font-size: 0.7rem; font-weight: 600; }
.badge-green  { background: #dcfce7; color: #166534; }
.badge-blue   { background: #dbeafe; color: #1e40af; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-red    { background: #fee2e2; color: #991b1b; }
```

### Stat/KPI card pattern:
```html
<div class="stat-card">
  <div class="stat-label">Total Inventory Value</div>
  <div class="stat-value">$1,234,567</div>
  <div class="stat-change positive">+12.5% vs last month</div>
</div>
```
```css
.stat-card { background: var(--color-surface); border: 1px solid var(--color-border);
             border-radius: var(--radius-lg); padding: var(--space-6); }
.stat-label { font-size: 0.8rem; color: var(--color-muted); font-weight: 500; margin-bottom: var(--space-2); }
.stat-value { font-size: 1.75rem; font-weight: 700; color: var(--color-text); }
.stat-change { font-size: 0.75rem; margin-top: var(--space-1); }
.stat-change.positive { color: #16a34a; }
.stat-change.negative { color: #dc2626; }
```

## Phase 4 — Verify

1. Start the dev server if not running: `cd client && npm run dev`
2. Use Playwright MCP tools to open http://localhost:3000 and take screenshots of:
   - The Dashboard
   - The Inventory page
   - The Orders page
3. Check that:
   - Sidebar is visible and nav links work
   - Content area has correct spacing and background
   - Tables and cards look polished
   - No layout breakage or overlapping elements

## Rules

- MANDATORY: Use `vue-expert` subagent for ALL .vue file edits
- Do NOT use emojis in the UI
- Do NOT use icon libraries unless already present in package.json
- Do NOT change any API calls or backend logic
- Preserve all existing functionality — this is a pure UI redesign
- Use `scoped` styles in each component
- Apply CSS variables from App.vue globally via `:root` or unscoped styles in App.vue
- Keep changes minimal and targeted — no unnecessary refactoring
