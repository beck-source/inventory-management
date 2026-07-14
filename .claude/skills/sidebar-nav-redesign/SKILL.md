---
name: sidebar-nav-redesign
description: Use this skill when redesigning a Vue 3 app's navigation into a modern SaaS-style left sidebar layout, replacing a top nav bar, introducing CSS design tokens, or making an app's chrome (nav, header, sticky bars, profile menu) more consistent and professional-looking.
---

# Sidebar Nav Redesign

Turns a Vue 3 app's top-nav chrome into a modern SaaS-style left sidebar: collapsible, icon-led, with consistent spacing via extracted design tokens. This skill is a **procedure**, not a code generator — it never edits `.vue` files itself. It discovers the app's current chrome, designs the token/sidebar spec, then hands the actual file writes off to a Vue-capable agent (this repo's `vue-expert` subagent, if invoked from here; otherwise whatever frontend-editing agent/tool the host project designates).

Read the reference files as you reach each phase — don't front-load all of them.

## Phase 0 — Scope check

Confirm the target is a Vue 3 SPA: find `package.json` with a `vue` dependency, and a router (`vue-router` or a hand-rolled route table). If it isn't Vue 3, stop and say so — this skill assumes Single File Components and doesn't care whether they use the Options or Composition API.

## Phase 1 — Discover current chrome architecture

Read `references/discovery.md` and apply its heuristics to find: the shell/root component, the nav markup inside it, any companion pieces coupled to nav height/position (sticky bars, dropdowns), and the authoritative route list — then cross-check that list against existing nav links and i18n keys to catch gaps (a view that exists but has no nav entry, a nav label with no translation key, etc.).

## Phase 2 — Design tokens

Read `references/design-tokens.md`. **Extract, don't invent**: pull the app's existing hardcoded colors/spacing/radii into a `:root` CSS custom-property block so the redesign preserves the app's brand feel instead of replacing it wholesale.

## Phase 3 — Sidebar anatomy

Read `references/sidebar-anatomy.md`. Fixed structural slots: brand/logo top, nav item list (icon + label + active-state, icon-only when collapsed), a collapse/expand toggle, and a footer slot for the profile/account menu. Reuse whatever icon approach the app already has; never add a new icon dependency without asking the user first.

## Phase 4 — Responsive / mobile spec

Also in `references/sidebar-anatomy.md`. Desktop keeps the sidebar always visible (collapsible to an icon-only rail); below ~768px (or the app's existing breakpoint) it becomes an off-canvas drawer triggered by a slim top bar with a hamburger toggle.

## Phase 5 — Migrate companion pieces

Using Phase 1's findings: recalculate or remove any sticky/fixed offset that was hardcoded against the old nav's height; flip any dropdown that assumed a top-right, downward-opening position (a footer-anchored menu opens upward instead); fix the nav-link/i18n gaps found in Phase 1 in this same pass, not later.

## Phase 6 — Handoff

Do not write `.vue`, `.js`, or CSS files yourself. Compose one scoped delegation prompt containing:
- The concrete file list from Phase 1
- The exact token names/values from Phase 2
- The anatomy + responsive acceptance criteria from Phases 3–4
- The specific gaps to fix from Phase 5
- An explicit instruction: presentation-layer only, no changes to API calls, data logic, or business logic

Then delegate to the project's designated Vue-editing agent (in this repo, that's `vue-expert` — mandatory per this repo's root `CLAUDE.md`).

## Phase 7 — Verify

Start the dev server and drive the app in a browser (Playwright MCP in this repo, against `localhost:3000`): confirm the sidebar renders, active-route highlighting works, the collapse toggle works, the profile menu opens without clipping off-screen, the mobile drawer opens/closes at the breakpoint, and there are no new console errors.

## Common pitfalls

Read `references/pitfalls.md` before finishing — it's a short generalized do/don't list (sticky-offset coupling, dropdown-direction assumptions, nav/i18n parity drift, inventing tokens instead of extracting them) worth checking your output against regardless of which app you're redesigning.

## Templates

`templates/sidebar.vue.template` and `templates/tokens.css.template` are annotated skeletons, not copy-paste-ready components — adapt class names, exact values, and slot content to the target app before handing them to the editing agent.
