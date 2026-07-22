---
name: frontend-design
description: Redesigns a Vue 3 app's top nav into a modern SaaS-style vertical sidebar. Configurable aesthetic (Notion/Craft light, Linear dark, Stripe), sidebar width, collapse behavior, and icon set. Use when converting top-nav to sidebar layout or refreshing overall UI polish.
---

# frontend-design: SaaS Sidebar Skill

Converts a Vue 3 application from a horizontal top-navigation bar to a vertical sidebar layout with collapsible icons-only mode. Produces a polished, modern SaaS aesthetic.

## Parameters (resolve via AskUserQuestion before starting if not provided)

| Parameter | Options | Default |
|---|---|---|
| `aesthetic` | `notion-light` \| `linear-dark` \| `stripe-accent` | `notion-light` |
| `sidebar_expanded_width` | pixels (e.g. `240`, `280`) | `240` |
| `sidebar_collapsed_width` | pixels | `56` |
| `collapse_persist` | `localStorage` \| `session` \| `none` | `localStorage` |

## Aesthetic tokens

### notion-light
```
--sidebar-bg:        #f7f8fa
--sidebar-border:    #e8ecf0
--sidebar-text:      #37352f
--sidebar-muted:     #9b9b9b
--sidebar-active-bg: #e8ecf0
--sidebar-hover-bg:  #eff1f4
--content-bg:        #f8fafc
--accent:            #2563eb
```

### linear-dark
```
--sidebar-bg:        #0f172a
--sidebar-border:    #1e293b
--sidebar-text:      #f1f5f9
--sidebar-muted:     #64748b
--sidebar-active-bg: #1e293b
--sidebar-hover-bg:  #1e293b
--content-bg:        #f8fafc
--accent:            #3b82f6
```

### stripe-accent
```
--sidebar-bg:        #ffffff
--sidebar-border:    #e5e7eb
--sidebar-text:      #111827
--sidebar-muted:     #6b7280
--sidebar-active-bg: #eff6ff
--sidebar-hover-bg:  #f9fafb
--content-bg:        #f9fafb
--accent:            #635bff
```

## Output files

The skill produces exactly **two file changes**:

### 1. `client/src/components/AppSidebar.vue` (new file)
A self-contained sidebar component. Requirements:
- CSS variable `--sidebar-width` on `:root` (expanded) toggled to `--sidebar-collapsed-width` on `.sidebar--collapsed`
- `isCollapsed` ref initialized from `localStorage.getItem('sidebar-collapsed') === 'true'` — persist on toggle
- Each nav item: icon (inline SVG, 18×18, `stroke-width: 1.5`, no fill) + text label hidden when collapsed
- Tooltip on collapsed items (CSS `title` attribute or absolute positioned span)
- Toggle button at bottom of nav section (chevron icon rotates 180° when collapsed)
- User profile area at bottom: avatar initials + name (collapsed: avatar only)
- Emits `@profile-click` and `@tasks-click` so App.vue can open modals — do NOT open modals directly
- Scoped styles only; root CSS vars injected via `:global(:root)` block

### 2. `client/src/App.vue` (modified)
Replace the `.top-nav`/`.nav-container` block with `<AppSidebar>`. Layout changes:
```css
.app {
  display: flex;
  flex-direction: row;   /* sidebar left, content right */
  min-height: 100vh;
}
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;          /* prevents flex overflow */
  background: var(--content-bg, #f8fafc);
}
```
- FilterBar stays inside `.content-area` (above `<router-view>`)
- Remove all `.top-nav`, `.nav-container`, `.nav-tabs`, `.logo`, `.subtitle` CSS
- Keep `.main-content`, `.card`, `.badge`, `.stats-grid`, `.table-container`, `.loading`, `.error` global styles intact — views depend on them

## Nav item icon set

Use these inline SVG paths (viewBox="0 0 24 24", stroke="currentColor", fill="none"):

```
Overview:    M3 3h7v7H3zm11 0h7v7h-7zM3 14h7v7H3zm11 0h7v7h-7z
Inventory:   M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z
Orders:      M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 000 4h6a2 2 0 000-4M9 5a2 2 0 012-2h2a2 2 0 012 2
Finance:     M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6
Demand:      M23 6l-9.5 9.5-5-5L1 18
Reports:     M18 20V10M12 20V4M6 20v-6
Restocking:  M1 4v6h6M23 20v-6h-6M20.49 9A9 9 0 005.64 5.64L1 10M23 14l-4.64 4.36A9 9 0 013.51 15
```

## Step-by-step procedure

1. **Read** `client/src/App.vue` and `client/src/components/ProfileMenu.vue` to understand the current props/emits
2. **Create** `AppSidebar.vue` with the spec above
3. **Modify** `App.vue`:
   - Add `import AppSidebar from './components/AppSidebar.vue'` and register it
   - Replace the `<header class="top-nav">…</header>` block with `<AppSidebar @profile-click="showProfileDetails = true" @tasks-click="showTasks = true" />`
   - Wrap `<FilterBar />` and `<main class="main-content">` in `<div class="content-area">`
   - Update global CSS to new layout (see above)
4. **Verify** with `agent-browser screenshot` that the layout renders correctly

## Quality checks (run before reporting done)

- [ ] Sidebar renders at correct width, right-border visible
- [ ] All 7 nav items present with correct icons
- [ ] Active item highlighted on current route
- [ ] Collapse toggle works, persists on refresh (localStorage)
- [ ] Collapsed mode: icons only, no label overflow
- [ ] FilterBar still visible above content
- [ ] No horizontal scrollbar on content area
- [ ] Existing cards, tables, badges unchanged in content views

## Collapsible iteration (after initial implementation)

If the task includes "collapsible with icons-only mode":
- The toggle button should be at the bottom of the nav items area, not in a header
- Use a `<Transition name="sidebar-label">` with `width`/`opacity` for label animation
- CSS transition: `transition: width 0.2s ease` on the sidebar itself
- `title` attribute on collapsed nav items for native tooltip (no JS needed)
