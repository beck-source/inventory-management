---
name: vue-saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface — replace a top navigation bar with a left vertical sidebar, introduce a consistent spacing/design-token system, and give the app a polished, professional look. Use this whenever the user wants to modernize, restyle, or "make a Vue app look professional", add a sidebar/left-nav layout, fix inconsistent spacing, improve visual hierarchy, or move navigation out of a top bar — even if they don't use the exact word "redesign".
license: MIT
metadata:
  author: Michał
  version: "1.0.0"
---

# Vue 3 SaaS Redesign

Turn an existing Vue 3 app into a modern SaaS-style interface: a fixed **left
sidebar** for navigation, a **design-token system** for consistent spacing and
color, and a **polished, calm visual hierarchy**. The goal is a focused structural
+ stylistic upgrade, not a rewrite of business logic.

A guiding principle runs through everything below: **adapt to the app you are
given.** Read its current colors, fonts, and component styles first, then extend
them into a token system — don't impose an unrelated theme or a new CSS framework
unless the user asks. A redesign that respects the app's existing identity feels
intentional; one that replaces it wholesale feels like a different product.

## When this applies

Reach for this skill when the user wants to modernize a Vue app's look, move
navigation from a top bar to a left sidebar, make spacing/typography consistent, or
generally "make it look like a real SaaS product." It assumes Vue 3 (Options or
Composition API, Vue Router). It does **not** change routes, data flow, or backend.

## The method

Work in this order. Each step has detail in a bundled reference file — read the
referenced file before doing that step the first time.

1. **Audit.** Find the app shell (usually `App.vue`) and how global styles are
   organized (scoped vs a global `<style>`, any existing CSS variables, a color
   palette, the nav markup, the router links). Note the framework in use so you can
   adapt rather than replace. Inventory the nav destinations and any header widgets
   (search, language switch, profile menu).

2. **Establish design tokens.** Add one global stylesheet of CSS custom properties
   for spacing, color roles, radius, elevation, and typography — seeded from the
   app's *existing* values so nothing visually jumps. See
   `references/design-principles.md` and start from `templates/design-tokens.css`.
   Import it once, globally.

3. **Build the app shell.** Replace the top bar with a two-area layout: a fixed
   left **sidebar** and a scrollable **main** region. See
   `references/sidebar-pattern.md` and start from `templates/AppSidebar.vue`.

4. **Migrate navigation.** Move every top-nav link into the sidebar as a vertical
   list with clear active states; pin secondary widgets (profile, language, settings)
   to the **bottom** of the sidebar. Preserve existing router links, labels, and i18n
   calls exactly — you are restyling, not renaming.

5. **Apply spacing & polish.** Re-express the app's cards, tables, and headers in
   terms of the tokens so vertical rhythm and padding are consistent everywhere.
   Favor calm neutrals, one accent color, generous whitespace, and restrained
   elevation. Details in `references/design-principles.md`.

6. **Make it responsive.** Collapse the sidebar to icons (or a drawer) below a
   breakpoint so the app still works on narrow screens. See
   `references/sidebar-pattern.md`.

7. **Verify.** Walk `references/redesign-checklist.md`: every route reachable and
   active state correct, header widgets still function, no dead top-nav remnants,
   spacing consistent, responsive behavior works, and nothing in the views broke.

## How to use the bundled files

- `references/design-principles.md` — the spacing scale, color roles, typography,
  density and elevation rules that define the "SaaS look", plus how to derive tokens
  from an existing palette. Read before step 2.
- `references/sidebar-pattern.md` — the app-shell architecture, the sidebar anatomy,
  active-state and accessibility guidance, and responsive collapse. Read before
  steps 3–6.
- `references/redesign-checklist.md` — the audit + acceptance checklist. Use in
  steps 1 and 7.
- `templates/AppSidebar.vue` — a literal starting point for the sidebar component
  (logo, nav list with inline SVG icons, profile slot). Adapt its labels/links to
  the target app; keep its structure.
- `templates/design-tokens.css` — a drop-in token sheet. Re-seed the color values
  from the target app's palette before using it.

## Boundaries

- Don't add a CSS framework or other dependency unless the user explicitly asks.
- Don't rename routes or rewrite view logic — restyle the shell and global styles;
  per-view polish should flow from the shared tokens.
- No emojis as UI chrome; use inline SVG icons for a professional feel.
- Comment any non-obvious layout decision so the next maintainer understands the why.
