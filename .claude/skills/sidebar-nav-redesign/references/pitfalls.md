# Common pitfalls

Generalized lessons, not tied to any one app — check the redesign against these before calling it done.

- **Don't hardcode sticky offsets to another element's height.** A `top: 70px` on a filter bar because "that's the nav's height" breaks the moment the nav's shape changes — which is exactly what this redesign does. Prefer `top: 0` in the new sidebar+content layout, or let a flex/grid container handle the offset structurally instead of a magic number.

- **Don't assume a dropdown's open-direction is inherent to the component.** A menu opening downward from the top-right is a function of where its anchor currently sits in the viewport, not a property of "how dropdowns work" — always re-derive open-direction when relocating an anchor (e.g., sidebar footer → opens upward).

- **Don't let route/nav-link/i18n parity drift.** Every route should have a nav entry and a translation key in every locale, or an explicit, deliberate reason it's hidden (e.g., an admin-only route). Treat "does every route have a nav link and an i18n key" as a mandatory checklist item on any change that touches navigation — not just something to get right at initial creation and never revisit.

- **Don't invent a new visual language.** Extract design tokens from the app's existing hardcoded values first (see `design-tokens.md`); only introduce genuinely new values when there's a real gap (e.g., no existing "danger" color anywhere for a destructive action that needs one).

- **Don't add a new dependency silently.** No icon library in `package.json`? Use inline SVGs, or ask the user before adding one. The same applies to any other new package a "polish" pass might tempt you to reach for.

- **Do preserve all existing functionality.** Filters, language switchers, auth actions, notifications — everything reachable in the old nav must still be reachable after. A redesign relocates UI; it does not remove features.

- **Mobile sidebar is off-canvas, not a shrunken rail.** An icon-only collapsed rail is a desktop affordance for reclaiming horizontal space next to content that's already visible. On a phone-width viewport there's no spare width to reclaim from — hide the sidebar entirely and trigger it via a drawer instead of trying to keep a permanently-visible rail.

- **Don't skip verification because "it's just CSS."** Layout changes are exactly the kind of change that looks fine in the diff and breaks in the browser (overlapping elements, clipped dropdowns, a drawer that doesn't close). Always drive the app in a real browser at both desktop and mobile widths before calling the redesign done.
