---
name: sidebar-shell-redesign
description: Redesign this app's shell — the top nav bar and header in App.vue — into a modern SaaS-style vertical left sidebar, with consistent spacing and a polished professional look, while preserving every route, header control, and shared style token the views depend on. Use when the user asks to add a sidebar or left nav, modernize/redesign the navigation, restyle the app shell, or make the UI look more like a professional SaaS product.
---

The **shell** is the persistent chrome around every page — right now that's the `<header class="top-nav">` block in `client/src/App.vue` plus the global `<style>` block beneath it. The shell is not scoped: `.card`, `.stat-card`, `.badge`, `table`/`th`/`td`, `.page-header`, `.loading`, `.error` are all defined there and consumed, unscoped, by every view in `client/src/views/`. Redesigning the shell means touching the one file every page silently depends on — the steps below exist to keep that dependency intact while the chrome changes shape.

## Steps

### 1. Inventory the current shell
Read `App.vue` end to end and list, explicitly:
- every nav route and label (`/`, `/inventory`, `/orders`, `/spending`, `/demand`, `/reports` — labels come from `t('nav.*')` via `useI18n`, except "Reports" which is hardcoded)
- every header control (`LanguageSwitcher`, `ProfileMenu`, and the two modals `ProfileMenu` triggers: `ProfileDetailsModal`, `TasksModal`)
- every global style rule below the template (`.top-nav`, `.nav-container`, `.logo`, `.nav-tabs`, `.main-content`, `.page-header`, `.stats-grid`, `.stat-card`, `.card`, table rules, `.badge*`, `.loading`, `.error`)

Completion criterion: you can name, without re-reading the file, which of those rules are shell-only (safe to rewrite freely) versus shared content tokens consumed by views (must survive unchanged or be updated everywhere they're used).

### 2. Design the new layout skeleton
Target shape — sidebar and content sit side by side, not stacked:

```
.app (flex row, min-height: 100vh)
├── aside.sidebar (flex column, fixed width ~260px, full height)
│     logo/product name → vertical nav links → spacer → profile + language controls
└── div.content-column (flex column, flex: 1)
      ├── FilterBar (or a slim top bar hosting it) — sticky, spans content-column width only
      └── main.main-content → <router-view/>
```

Decisions to make explicitly, not by default:
- **FilterBar** moves into `.content-column`, above `main`, not into the sidebar — filters are page-level controls, the sidebar is global navigation. Keep it sticky the way `.top-nav` is today.
- **ProfileMenu + LanguageSwitcher** relocate to the bottom of the sidebar (standard SaaS pattern) — keep their existing emitted events (`@show-profile-details`, `@show-tasks`) untouched, only their position in the template changes.
- Active-route highlighting (`:class="{ active: $route.path === '/...' }"`) carries over unchanged — it's a vertical list now, not a horizontal one.

Completion criterion: you can draw the skeleton above with this app's actual component names slotted in, and have answered where FilterBar and ProfileMenu/LanguageSwitcher land.

### 3. Reuse this app's existing spacing and color scale — don't invent one
The current shell already sits on a consistent scale; snap every new sidebar rule to it so old and new chrome don't visibly disagree:

- **Spacing:** `0.25rem 0.375rem 0.5rem 0.625rem 0.75rem 1rem 1.25rem 1.5rem 1.875rem 2.25rem`
- **Radius:** `6px` (buttons/badges/nav items), `10px` (cards)
- **Border:** `1px solid #e2e8f0`
- **Text:** headings `#0f172a`, muted `#64748b`, body `#334155`/`#475569`
- **Brand/active:** `#2563eb` on `#eff6ff`
- **Surface:** app background `#f8fafc`, card/sidebar background `#ffffff`
- **Type:** `Inter` stack already loaded on `body`; weights 500 (nav), 600 (labels/th), 700 (headings) are already in use — keep them

A "polished professional" sidebar means disciplined reuse of this palette at the new geometry (vertical padding on nav items, sidebar width, active-state left-border or filled-pill), not new colors or a new radius scale.

### 4. Build it through vue-expert
Per this repo's root `CLAUDE.md`, any creation or modification of a `.vue` file must be delegated to the **vue-expert** subagent — this applies here without exception, since the entire change is inside `App.vue`. Hand vue-expert the skeleton from step 2 and the token list from step 3 directly; don't let it re-derive spacing/color choices from scratch.

Completion criterion: `App.vue`'s template is a sidebar + content-column layout, and every rule identified as a shared content token in step 1 still exists and still renders identically on every view.

### 5. Verify nothing else broke
- Grep `client/src` for `top-nav`, `nav-container`, `nav-tabs` outside `App.vue` — should return nothing; if it does, something depended on the old shell's class names directly.
- Confirm every view (`Dashboard`, `Inventory`, `Orders`, `Spending`, `Demand`, `Reports`, `Backlog`) still renders its `.stat-card`/`.card`/`.badge`/table markup correctly — these are unscoped and inherited from `App.vue`, not redefined per-view.
- With the dev server running (`/start`, or `npm run dev` from `client/`), use the Playwright MCP tools against `http://localhost:3000` to click through every sidebar nav link, confirm the active-route highlight moves correctly, and open the profile/tasks modals from their new sidebar position.

Completion criterion: every route is reachable from the new sidebar, the active link highlights correctly on each, and a visual check at both a wide (≥1280px) and narrow (~1024px) viewport shows no overlap or clipping between sidebar and content.
