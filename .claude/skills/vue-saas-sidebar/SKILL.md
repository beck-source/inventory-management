---
name: vue-saas-sidebar
description: Redesigns a Vue 3 application's layout from a top navigation bar into a polished, modern SaaS-style interface with a vertical left sidebar. Use when asked to "add a sidebar", "convert to a left nav", "redesign this Vue app's layout", "make this look like a SaaS product", or "modernize the navigation" in a Vue 3 codebase. Handles IA planning for the sidebar, consolidating scattered hardcoded colors into CSS custom-property design tokens, relocating header chrome (filters, profile menus, language switchers) into the new layout, and preserving i18n. Pairs with the frontend-design skill for aesthetic direction — invoke both together when the user wants a full visual overhaul, not just a structural nav change.
---

# Vue SaaS Sidebar Redesign

## When to use this

Use this skill for a structural layout transformation: moving a Vue 3 app from a top-navigation-bar pattern to a modern SaaS interface with a vertical left sidebar. This is not for purely cosmetic tweaks to an already-sidebar layout (use the `frontend-design` skill for that alone), nor for adding a sidebar to a completely different framework.

The skill orchestrates the full redesign: sidebar IA design, design-token consolidation or creation, relocating global chrome (filters, profile menus, locale switchers), and preserving i18n across all changes.

## Relationship to frontend-design

This skill owns *structure*: where the navigation lives, what design tokens exist, how page chrome is arranged.

The `frontend-design` skill owns *aesthetic direction*: color palette, typography pairing, signature visual elements, and a restraint/self-critique pass (responsive, focus states, reduced motion, screenshot review).

To build a polished SaaS sidebar that doesn't read as a generic AI default, **invoke both skills together**. Concretely:

1. **Early (Step 3 below):** Before finalizing design-token values, call the Skill tool for `frontend-design`. Frame the brief as "left sidebar navigation for [your app's subject and audience]" so the palette brainstorm is grounded in the actual design context, not generic defaults.

2. **Late (Step 7 below):** At verification, reuse `frontend-design`'s restraint/self-critique checklist (responsive behavior, focus states, reduced-motion animation, screenshot comparison) rather than inventing a separate checklist. This ensures both skills reinforce each other.

## Workflow

### Step 1: Locate and analyze the current layout

Find the top-level shell component that renders the entire page's chrome (commonly `src/App.vue`, `src/Layout.vue`, or something under `src/layouts/`). This component will be the primary target for restructuring.

Identify:
- **Current nav items:** List every nav link. How is "active" state computed? Look for manual `:class="{ active: ... }"` logic, vue-router's built-in `active-class`/`router-link-active`, or other patterns.
- **Header-level chrome:** Search for filter bars, search inputs, profile menus, language/locale switchers, notification bells, or other chrome that lives alongside the nav in the header area. Note their responsibilities (do they affect the entire page, or just the current view?).
- **Page structure:** How is the main content area laid out relative to the header? Is there a `<main>`, a `<router-view>`, or a `<section>` wrapping the view content?

Read the router config (typically `src/main.js`, `src/router/index.js`, or `src/router.ts`) and list every route. Cross-check against the `src/views/` directory: are there view files that exist but have no route entry? (These are candidates to add to the sidebar later — ask the user about them.)

Grep for repeated hex-color literals (`#[0-9a-f]{3,6}`) and px-based spacing (`\d+px`) across the shell and a sample of view files. This tells you whether a design-token system already exists (CSS custom properties, a Tailwind theme, SCSS variables) or whether colors/spacing are scattered and hardcoded.

### Step 2: Design the sidebar IA

See `references/sidebar-patterns.md` for the full checklist. Quick summary:

- **Nav items:** One sidebar item per top-level route. If you have more than ~7 items, group related routes under collapsible sections.
- **Active state:** Use vue-router's built-in `active-class` and `exact-active-class` attributes on `router-link` instead of re-deriving active state with manual `:class="{...}"` logic. This is more maintainable and less bug-prone.
- **Collapse behavior:** Decide now: Should the sidebar collapse into an icon-only rail on narrow viewports, or hide completely, or stay fixed-width? At what viewport width should auto-collapse kick in? Does the user manually toggle collapse, or does it toggle automatically?
- **Icons:** Check `package.json` to see if an icon library is already installed (e.g. `lucide-vue-next`, `heroicons`, `font-awesome`). Do not add a new icon dependency without confirmation — reuse what's already there if possible.

Document your sidebar design (which items appear, grouping, collapse strategy, icon strategy) so Step 4 can implement it correctly.

### Step 3: Establish or consolidate design tokens

See `references/design-tokens-checklist.md` for the full checklist. Summary:

If colors and spacing are hardcoded hex/px literals scattered across the shell and view files:
- Extract them into **CSS custom properties** in a centralized location (a `:root` block in your global stylesheet, or a dedicated `tokens.css` / `tokens.scss` file imported globally).
- For the token *values*, invoke the Skill tool for `frontend-design` now, framing the brief as "modern SaaS sidebar for [your app description, audience, purpose]." Use the palette/spacing directions it brainstorms rather than inventing your own — this is the key to avoiding generic defaults.
- Start with a minimal token set: colors (brand, neutral surfaces, borders, status indicators), a spacing scale, a border radius, and sidebar-specific widths (expanded and collapsed).

If tokens already exist, **do not invent a parallel system.** Audit the existing tokens, add the new sidebar-specific tokens to the same system, and source aesthetic direction from `frontend-design` to inform any palette gaps.

### Step 4: Relocate header chrome into the sidebar layout

Header-level controls like filter bars, profile menus, language switchers, and search inputs need a new home when the nav moves to a sidebar:

- **Filter bars / view-specific controls:** move to the top of the main content area (sometimes a "toolbar" just inside the main content wrapper), or to a sidebar's secondary utility slot if they apply globally.
- **Profile menus, language switchers, notification bells (global controls):** move to a pinned footer area of the sidebar, or to a header slot in the sidebar, depending on your IA design from Step 2.
- **Search bars:** decide whether they're page-specific (top of main content) or global (sidebar header / top bar retained just for search).

**Preserve existing components' contracts.** Do not delete and rewrite `<LanguageSwitcher/>` — move it as-is into a new parent, adjust the CSS layout and positioning, and ensure it still emits and receives the same props/events. This keeps other code that depends on it working without surprises.

Rebuild the main layout as a **sidebar + main content grid/flex shell**, with the sidebar on the left and the main content area (containing `<router-view>`) to the right.

### Step 5: Preserve i18n and avoid hardcoded strings

If the app has an i18n layer (vue-i18n, a custom composable with a `t()` function, or similar), every nav label and relocated header label must be **run through the i18n layer**, not hardcoded in the template.

- For nav items based on routes, ensure there's a translation key for each (e.g. `nav.overview`, `nav.inventory`, etc.). Add any missing keys to **all locale files**, not just the default language, so no locale silently falls back to an untranslated string.
- If you found unrouted views in Step 1 and the user decided to add them to the nav, create i18n keys for them too (e.g. `nav.backlog`).
- Check for any hardcoded English strings in relocated headers or footers — wrap them in `t()` calls or add them to the locale files.

### Step 6: Implement

**If the target repo's CLAUDE.md (or equivalent setup instructions) mandates that Vue components (.vue files) be created/modified only by a specific subagent (e.g. `vue-expert`), delegate all `.vue` creation and modification to that subagent. Check the repo's instructions before writing any code.**

Otherwise, follow the project's existing patterns:
- Match the component style (Options API vs Composition API vs `<script setup>`).
- Reuse existing composables and utilities rather than inventing new ones.
- Follow the project's scoped/global CSS conventions and naming.

### Step 7: Verify

- **Routing:** Every route in the router config is reachable from the sidebar and highlights with the correct active state. No dead links.
- **Responsive:** Collapse/hide behavior works at a narrow viewport (test at ~375px width for mobile, ~768px for tablet breakpoint, per your design in Step 2).
- **i18n:** Switch to a non-default locale (if available) and confirm all nav labels and relocated header controls translate correctly.
- **Aesthetic critique:** Invoke the Skill tool for `frontend-design` again, requesting its restraint/self-critique pass: Does the sidebar look responsive? Are focus states clear and visible? Does reduced-motion preference affect animations? Take a screenshot of the expanded and collapsed sidebar (and each locale if i18n is present) for visual comparison before/after.
- **Browser testing:** If a browser tool (Playwright, etc.) is available, navigate to each route from the sidebar in both expanded and collapsed states, and screenshot for a final visual check.

## Anti-patterns to avoid

1. **Don't invent a palette independently of `frontend-design`.** This produces the "generic AI SaaS" look the user is trying to escape. Always invoke `frontend-design` first to brainstorm tokens grounded in the actual subject and audience.

2. **Don't manually recompute nav "active" state.** Vue Router provides `active-class` and `exact-active-class` — use them. Manual `:class="{ active: $route.path === '/...' }"` logic is fragile and repeats across nav items.

3. **Don't leave a locale's translation dictionary out of sync.** If you add `nav.newPage` to English, add it to every other locale too, even if the translation is just a stub. Silent fallback to English (or worse, untranslated key names) breaks the i18n guarantee.

4. **Don't bypass the repo's subagent-delegation rule for `.vue` files.** If the repo explicitly mandates that Vue component changes go through a specific subagent, follow that rule — the restriction exists for good reasons (team consistency, code review, skill validation).
