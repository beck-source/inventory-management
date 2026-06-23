# Sidebar app-shell pattern

The structural heart of the redesign: move navigation from a horizontal top bar to
a fixed vertical sidebar, and give the content its own scrollable region.

## Shell architecture

```
.app                      (flex row, min-height: 100vh)
├── aside.sidebar         (fixed width e.g. 248px; column; full height; own surface)
│   ├── .sidebar-brand    (logo / product name, top)
│   ├── nav.sidebar-nav   (the vertical link list, scrolls if long; flex: 1)
│   └── .sidebar-footer   (profile, language, settings — pinned bottom)
└── .app-main            (flex: 1; min-width: 0; column; the scrollable area)
    ├── .app-topbar       (optional slim bar: filters, page context, search)
    └── main.content      (router-view; padding from the spacing scale)
```

Why this shape: a persistent left rail is the dominant pattern for tools with many
destinations — it scales to more nav items than a top bar, keeps navigation visible
while scrolling content, and gives a natural home (the footer) for account/settings
widgets. `min-width: 0` on the main column is essential so wide tables don't blow out
the layout.

## Sidebar anatomy

- **Brand** at top: product name (+ small mark). Keep it compact.
- **Nav list**: one item per destination. Each item = inline SVG icon + label,
  comfortable hit area (`padding: var(--space-3) var(--space-4)`), `--radius-md`,
  `gap: var(--space-3)`.
- **Active state**: accent text on `--color-accent-weak`; optionally a left accent
  bar. Drive it from the router (`router-link-active`, or compare `$route.path`).
- **Footer**: profile menu, language switch, settings — pinned to the bottom with
  `margin-top: auto`.

## Migrating existing top-nav links

Map each existing top-bar `<router-link>` to a sidebar item one-to-one. **Preserve
the original `to`, label text, and any i18n call** (e.g. `t('nav.orders')`) — this is
a restyle, not a rename. Add an icon per item. If the app had header widgets
(language, profile), relocate them into the sidebar footer rather than deleting them.

## Accessibility

- Wrap links in a `<nav aria-label="Primary">` landmark.
- Active item: set `aria-current="page"`.
- Keep a visible focus ring on every interactive element.
- Icons are decorative when paired with a text label — mark `aria-hidden="true"`.

## Collapsible / responsive behaviour

Make the rail collapsible to an **icons-only** mode. The recommended model (see
`templates/AppSidebar.vue`) combines a manual toggle with responsive forcing:

- Drive a single `collapsed` boolean. Bind it to a `.collapsed` class that narrows
  the rail to `--sidebar-width-collapsed` (~64–68px) and hides the brand text and
  nav labels. Animate `width` for a smooth transition.
- **Force collapse on small screens.** Watch a media query
  (`window.matchMedia('(max-width: 1024px)')`); when it matches, `collapsed` is true
  regardless of preference, so phones/tablets always get the compact rail. Add the
  listener in `onMounted` and remove it in `onBeforeUnmount`.
- **Toggle + persist on large screens.** A toggle button flips a `manualCollapsed`
  ref and saves it to `localStorage`; `collapsed = isSmall || manualCollapsed`. Hide
  the toggle when the small-screen force is active (it would be a no-op).
- **Keep destinations discoverable when collapsed.** Add a native `title` (tooltip)
  on each nav item showing its label, and keep an accessible name on the toggle
  (`aria-label` for collapse/expand, `aria-expanded`).

Alternative for true mobile: a **drawer** — hide the rail off-canvas and reveal it
with a hamburger + backdrop. Prefer the icon rail when desktop-first; the drawer
when mobile is the primary target. Either way the main region must stay fully usable
with the sidebar collapsed (`min-width: 0` on the main column).

## Common pitfalls

- Forgetting `min-width: 0` on the main column → horizontal overflow from tables.
- Sidebar that scrolls with content instead of staying fixed → use full-height
  column with its own overflow.
- Losing active state because the old top-nav active CSS was removed — re-implement
  it on the sidebar item.
