# Sidebar Patterns Reference

Use this reference during Step 2 (Design the sidebar IA) to make concrete decisions about sidebar anatomy, collapse behavior, and active-state patterns.

## Sidebar anatomy

A typical SaaS sidebar has **four zones**:

```
┌──────────────────┐
│  Header Zone     │  Logo, branding, or fold/collapse toggle
├──────────────────┤
│  Primary Nav     │  Routes as list items with icons + labels
│  (scrollable)    │
│                  │
├──────────────────┤
│  Secondary Nav   │  [Optional] Settings, help, admin—
│  (if any)        │  shown if 7+ primary items, or grouped
├──────────────────┤
│  Footer Zone     │  Profile menu, language switcher, collapse
│  (pinned)        │  toggle — floated to bottom, always visible
└──────────────────┘
```

### Header zone
- Usually a small fixed area (40–60px tall).
- Contains: app logo/wordmark, company branding, or a collapse/expand toggle button if collapse is manual.
- If collapse is automatic (responsive), the manual toggle might not be needed on wide viewports but appears on narrow ones.

### Primary nav (scrollable)
- A `<ul>` or `<nav>` of router-links, one per top-level route.
- Each item has an icon (left side), label text (right side of expanded; hidden in collapsed), and a highlight/active state.
- If you have more than ~7 routes, group related ones under a collapsible category header (e.g., "Sales", "Analytics") rather than a flat list of 10+ items.
- Height/padding per item: typically 44–48px to be touch-friendly and allow breathing room. Labels in a smaller font (12–14px) than page headers (16–18px+).

### Secondary nav (optional)
- Appears if primary nav is grouped or if there are secondary/utility routes (Help, Settings, Admin, etc.).
- Often a lighter visual treatment (smaller text, muted color) to de-emphasize it.
- Can be scrollable independently of primary nav, or below it in the scrollable area.

### Footer zone (pinned)
- Always visible, floated to the bottom of the sidebar with `position: sticky` or flexbox layout.
- Contains: user profile info / avatar, language switcher button, theme toggle (if any), or a "Sign out" link.
- Height: 60–80px typically, depending on what's inside.

## Collapse behavior strategies

Choose **one** of these patterns based on your app's UX goals:

### 1. Icon-rail collapse (recommended for most SaaS)
- On narrow viewports or after a user toggle, the sidebar collapses to a **fixed-width rail** showing only icons.
- Labels are hidden, but a tooltip or a side-sliding panel appears on icon hover to show the full label.
- Collapsed width: ~64–80px (enough for a typical icon + padding). Expanded: 200–280px typical.
- **Breakpoint:** Auto-collapse below ~1024px or ~768px (customize based on your content area's minimum comfortable width — main content shouldn't be crushed to <400px at min).
- **Transition:** Smooth CSS width animation (0.2–0.3s) makes the collapse feel responsive, not jarring.
- **Pro:** Space-efficient on small screens; the main content area grows; users can always see which section is active via the icon highlight.

### 2. Slide-out overlay collapse
- On narrow viewports, the sidebar becomes a **full-height overlay** (drawer/offcanvas) that slides in from the left over the main content.
- In collapsed state, the sidebar is hidden; a hamburger menu button (three horizontal lines, ☰) in the top-left triggers it to slide in.
- The overlay usually has a semi-transparent backdrop that closes the drawer when clicked.
- **Breakpoint:** Auto-collapse below ~768px (tablet).
- **Transition:** Slide-in animation from the left (transform: translateX) or fade-in of the overlay.
- **Pro:** Maximizes main content width on small screens; familiar mobile-app pattern.
- **Con:** Requires a hamburger menu button in the top bar (or a permanent toggle), and an extra click to navigate after the sidebar is collapsed.

### 3. No collapse (fixed width)
- Sidebar stays the same width at all breakpoints; the main content area scales with the viewport.
- Best for apps where the sidebar's content is always essential to navigate (e.g., a project sidebar that shows the current project and related utilities).
- At very narrow viewports (mobile), this often results in main content being too narrow, so this pattern is usually only suitable for tablet+.
- **Pro:** Simplest to implement; no state management for collapse.
- **Con:** Not mobile-friendly without extra work (e.g., hiding the sidebar completely on phones).

### Decision tree
- **Desktop-first app with a main content area that benefits from space?** → Icon-rail collapse.
- **Mobile-first or mobile-heavy usage?** → Overlay collapse.
- **Sidebar is always critical context (e.g., project switcher)?** → No collapse, or no-collapse on desktop + overlay on mobile.

## Vue Router active-state patterns

When a nav item should highlight as "active" when its route is displayed, use vue-router's built-in attributes rather than manually computing the state:

### Pattern 1: Simple routes (no nesting)
```vue
<router-link to="/" active-class="active" exact-active-class="active-exact">
  Overview
</router-link>
```

Use `exact-active-class="active-exact"` for the root `/` route to ensure it's only highlighted when you're exactly on `/`, not when you're on `/inventory` (which would match the `/` prefix).

### Pattern 2: Grouped secondary routes
If you have a "Settings" top-level item that expands to show "Profile Settings", "Account Settings", etc. (routes like `/settings/profile`, `/settings/account`), you want the "Settings" item highlighted whenever any `/settings/*` child route is active:

```vue
<router-link 
  to="/settings" 
  active-class="active"
  exact-active-class="active-exact"
>
  Settings
</router-link>
```

Vue Router's `active-class` matches `/settings/profile` (prefix match), while `exact-active-class` only matches `/settings` exactly. Using both lets you highlight the "Settings" group when any child route is active.

### Pattern 3: Programmatic active state (fallback only)
If router-link's attributes don't suffice (rare), compute active state via a composable:

```js
import { useRoute } from 'vue-router'

export function useActiveNav() {
  const route = useRoute()
  
  const isActive = (routePath) => route.path === routePath
  const isGroupActive = (prefix) => route.path.startsWith(prefix)
  
  return { isActive, isGroupActive }
}
```

Then use it in the template:
```vue
<li :class="{ active: isActive('/inventory') }">
  <router-link to="/inventory">Inventory</router-link>
</li>
```

This is more verbose than using `active-class` but can handle custom logic (e.g., checking route params, not just path).

## Minimal layout wireframe

A typical sidebar + main layout in CSS Grid:

```css
.app {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  grid-template-rows: auto 1fr;
  height: 100vh;
  gap: 0;
}

.sidebar {
  grid-column: 1;
  grid-row: 1 / -1; /* Span all rows */
  width: var(--sidebar-width);
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
}

.main-content {
  grid-column: 2;
  grid-row: 1 / -1;
  overflow-y: auto;
}

/* On narrow viewports, sidebar becomes overlay or hidden */
@media (max-width: 768px) {
  .app {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 1000;
  }
  
  .sidebar.open {
    transform: translateX(0);
  }
}
```

Replace `grid-template-columns: var(--sidebar-width) 1fr` with `grid-template-columns: var(--sidebar-collapsed-width) 1fr` if using icon-rail collapse, and animate the `--sidebar-width` custom property during the collapse transition.

## Icon-sourcing checklist

Before choosing an icon library or hand-drawing icons, answer these:

1. **Is an icon library already installed?** Check `package.json` for `lucide-vue-next`, `heroicons`, `font-awesome`, `material-design-icons`, or similar. If yes, use it — consistency and reduced bundle size.

2. **What icons do you need?** List the icons per nav item: Home, Package, Truck, DollarSign, TrendingUp, FileText, Archive, etc. Check whether your chosen library has all of them in the style you want (outlined, solid, etc.).

3. **Icon size for sidebar:** Typically 20–24px in a 44–48px tall nav item, centered with ~12px padding around it. The text label sits to the right.

4. **Fallback:** If an icon library doesn't have an icon you need, can you use emoji, a Unicode symbol (e.g., ✐ for edit), or an inline SVG stub? Emoji is quickest but may not match your design system.

5. **Collapsed-state visibility:** In icon-only (collapsed) mode, icons must be distinct enough to recognize at a glance. Use color (status colors for alerts, main brand color for primary nav) plus shape. If all nav items are the same color, they become hard to distinguish when labels disappear.

---

**Quick decision template:**

- **Collapse:** Icon rail / Overlay / None
- **Breakpoint:** __ px
- **Primary nav items (routes):** [list]
- **Secondary nav (if any):** [list]
- **Footer zone contents:** Profile / Language Switcher / Other
- **Icon library:** [Library name or "custom SVGs"]
