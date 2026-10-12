# Redesign checklist

Use the **audit** section before starting (step 1) and the **acceptance** section to
verify when done (step 7).

## Audit (before)

- [ ] Located the app shell component (where the top nav + `<router-view>` live).
- [ ] Identified how global styles are organized (global `<style>`, scoped, existing
      CSS variables) and whether a CSS framework is in use.
- [ ] Extracted the existing palette (bg, surface, border, text, accent, status) and
      font family.
- [ ] Listed every navigation destination (route + label + any i18n key).
- [ ] Listed header widgets to relocate (search, language, profile, settings).
- [ ] Confirmed the styling decision with the project's conventions (e.g. a
      CLAUDE.md: no emojis, comment non-obvious logic, no new deps without asking).

## Build

- [ ] Added a global design-token stylesheet, seeded from the existing palette,
      imported exactly once.
- [ ] Replaced the top bar with the sidebar + scrollable main shell.
- [ ] Every nav link migrated to the sidebar with its original `to`/label/i18n intact.
- [ ] Secondary widgets pinned to the sidebar footer.
- [ ] Cards/tables/headers re-expressed using the tokens (spacing, radius, color).
- [ ] Responsive collapse implemented (icon rail or drawer).

## Acceptance (after)

- [ ] No remnant of the old top nav (markup or styles).
- [ ] All routes reachable from the sidebar; the active item is highlighted and sets
      `aria-current="page"`.
- [ ] Header widgets (profile, language, filters, search) still function.
- [ ] Spacing is consistent — padding/gaps come from the scale, no one-off pixels.
- [ ] Single accent color; status colors only for status; flat elevation.
- [ ] Visible focus ring on interactive elements; `nav` landmark present.
- [ ] Wide content (tables) does not overflow horizontally (`min-width: 0` on main).
- [ ] Works at a narrow viewport (sidebar collapses, content usable).
- [ ] No view logic changed; app still builds/hot-reloads with no console errors.
- [ ] No emojis used as chrome; non-obvious layout choices are commented.
