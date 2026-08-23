# Sidebar Redesign

Transform the Vue 3 application's UI from a top navigation bar to a modern SaaS-style interface with a fixed vertical sidebar on the left.

## Phase 1 — Analyse the current layout

Read `client/src/App.vue` in full. Identify:
- All `<router-link>` nav items (route path and label)
- Any utility components in the top nav (language switcher, profile menu, user info, etc.)
- Where `<FilterBar>` or equivalent filter/toolbar components are rendered
- The global CSS layout classes (flex direction, max-width constraints, padding on `.main-content` or equivalent)

Also read `client/src/components/FilterBar.vue` (if it exists) to understand how it is structured and whether it should move into the sidebar or sit above the main content area.

## Phase 2 — Create the Sidebar component

Create `client/src/components/Sidebar.vue`. The sidebar must:

**Structure (top → bottom)**
1. **Logo block** — company name and subtitle (pulled from i18n `t('nav.companyName')` / `t('nav.subtitle')` if available, otherwise hardcode)
2. **Navigation links** — one `<router-link>` per route, each with:
   - A small inline SVG icon (choose a relevant icon per route: grid/dashboard, box/inventory, receipt/orders, chart/finance, trending/demand, file/reports, etc.)
   - The link label
   - Active state highlighted with a solid accent colour background and white text
   - Hover state with a subtle background tint
3. **Bottom utility strip** — LanguageSwitcher (if present) and ProfileMenu (if present) pinned to the bottom with `margin-top: auto`

**Design tokens to use**
- Sidebar background: `#0f172a` (dark slate)
- Active link: `#2563eb` background, `#ffffff` text
- Inactive link: `#94a3b8` text, transparent background
- Hover link: `rgba(255,255,255,0.07)` background
- Sidebar width: `220px`, fixed/sticky, full viewport height
- Typography: `font-size: 0.875rem`, `font-weight: 500`
- Icon size: `18px × 18px`, vertically centred with `gap: 0.625rem`
- Section dividers: `1px solid rgba(255,255,255,0.08)`

**Active route detection**
Use `useRoute()` from `vue-router` to compare `route.path` against each link's `to` prop. For the root route (`/`), match exactly; for all others, use `startsWith`.

## Phase 3 — Rewrite App.vue layout

Modify `client/src/App.vue`:

1. **Remove** the `<header class="top-nav">` block entirely.
2. **Import and register** `<Sidebar>` in place of the removed header.
3. **Update the root template** to a horizontal flex layout:
   ```
   <div class="app">
     <Sidebar />
     <div class="app-body">
       <FilterBar />          <!-- sticky filter strip at top of content area -->
       <main class="main-content">
         <router-view />
       </main>
     </div>
   </div>
   ```
4. **Update global CSS** in the `<style>` block:
   - `.app`: `display: flex; flex-direction: row; min-height: 100vh;`
   - `.app-body`: `flex: 1; display: flex; flex-direction: column; overflow: hidden;`
   - `.main-content`: remove the `max-width` and centre-margin constraints — let the content fill the available width naturally with `padding: 1.5rem 2rem;`
   - Remove all `.top-nav`, `.nav-container`, `.nav-tabs`, `.logo`, `.subtitle` rules — they are now owned by Sidebar.vue's scoped styles.

5. Keep all modal components (`ProfileDetailsModal`, `TasksModal`) and their event wiring exactly as-is.

## Phase 4 — Style the FilterBar for the new layout

If `FilterBar.vue` exists, ensure it renders as a horizontal sticky strip across the top of `.app-body`:
- `background: #ffffff`
- `border-bottom: 1px solid #e2e8f0`
- `padding: 0.75rem 2rem`
- `position: sticky; top: 0; z-index: 50`

Do not move FilterBar into the sidebar — keep it above the main content area.

## Phase 5 — Verify

After all edits:
1. Check that every `<router-link>` from the old top nav exists in Sidebar.vue with the correct `to` prop and a matching SVG icon.
2. Confirm that `ProfileMenu` and `LanguageSwitcher` (if they existed in the old nav) are still mounted and receive the same props/emits.
3. Confirm that modal wiring (`@show-profile-details`, `@show-tasks`) is unchanged.
4. Open `http://localhost:3000` using Playwright MCP (`mcp__playwright__browser_navigate`) and take a screenshot to visually verify the sidebar is rendering correctly.

## Constraints

- Do not change any view files (`client/src/views/*.vue`) — only `App.vue` and the new `Sidebar.vue` (and `FilterBar.vue` styles if needed).
- Preserve all i18n `t()` calls — do not hardcode strings that are already translated.
- Use `<style scoped>` in `Sidebar.vue`.
- Do not install any new npm packages.
- Delegate all `.vue` file creation and editing to the `vue-expert` subagent.
