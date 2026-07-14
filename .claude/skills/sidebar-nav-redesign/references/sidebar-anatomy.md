# Sidebar anatomy and responsive spec

## Structural slots (top to bottom)

1. **Brand/logo slot** — reuse whatever markup the old top nav's logo used (company name, subtitle, mark/icon). Don't redesign the brand mark itself; this skill's job is the nav shell, not the logo.

2. **Nav item list** — one entry per route from the authoritative route list (Phase 1 discovery). Each item:
   - Icon + label, both visible when expanded
   - Icon only when the sidebar is collapsed (label available via `title` attribute or a hover tooltip so it isn't lost, just hidden)
   - Active state driven by vue-router's own `router-link-active`/`router-link-exact-active` classes — style these, don't reimplement route-matching logic with manual `$route.path === '...'` comparisons
   - Icons: check `package.json` for an existing icon library dependency (e.g. `lucide-vue-next`, `@heroicons/vue`, `vue-feather`) and reuse it. If none exists, fall back to inline SVGs copied from a neutral icon set — never add a new icon package dependency without asking the user first, since that's a footprint decision beyond "redesign the layout."

3. **Collapse/expand toggle** — a button, typically at the bottom of the nav list or top-right corner of the sidebar itself (a chevron that flips direction). Persist the collapsed/expanded boolean in a small composable (name it consistently with the app's existing composable naming convention — e.g. if the app has `useFilters.js`/`useAuth.js`, call this one `useLayout.js` or `useSidebar.js`). Keep the composable to just this one concern; don't fold unrelated layout state into it.

4. **Footer slot** — the profile/account menu relocates here. Since it's now pinned near the viewport bottom, its dropdown must open **upward**:
   ```css
   /* before (top-right of a top nav): */
   .dropdown { top: calc(100% + 0.5rem); right: 0; }

   /* after (sidebar footer): */
   .dropdown { bottom: calc(100% + 0.5rem); left: 0; }
   ```
   Verify it doesn't clip off the top of the viewport when the sidebar is near the bottom of a short window.

## Collapsed state

Collapsing hides labels and shrinks the sidebar to an icon-only rail (roughly 64–72px wide vs. 220–260px expanded). This is a **desktop-only** affordance — see mobile behavior below, where a rail-width sidebar is still too cramped alongside real page content and the sidebar should hide entirely instead.

## Responsive / mobile behavior

Breakpoint: match whatever breakpoint the app already uses elsewhere (grep for existing `@media` queries first); default to ~768px if none exists.

- **Desktop (> breakpoint):** sidebar always visible, full-height, collapsible to the icon-only rail described above. Content area's left margin/grid column adjusts to the sidebar's current width.
- **Mobile (≤ breakpoint):** sidebar becomes an off-canvas drawer — `position: fixed`, translated fully off-screen (`transform: translateX(-100%)`) by default. A slim top bar (just a hamburger toggle + brand mark, not a full nav) triggers it open. An overlay/backdrop behind the open drawer closes it on click, and the drawer itself should close on route navigation (so picking a page doesn't leave the drawer hanging open).
- Prefer CSS `@media` queries for the visual show/hide and width changes; keep JS state to the minimum needed (an `isDrawerOpen` boolean), rather than tracking viewport width in JS if CSS alone can do it.

## What must not change

Filters, language switcher, auth/profile actions, and any other existing functionality in the old nav must all still be reachable after the redesign — this is a relocation of chrome, not a feature cut. If the old nav had a language switcher next to the profile menu, it moves to the sidebar footer alongside the profile menu; it doesn't disappear.
