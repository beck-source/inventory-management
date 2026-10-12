# Discovery: finding chrome in an unfamiliar Vue 3 app

Don't assume the shell component is called `App.vue`, or that nav classes are named `.nav`/`.header`. Find things by structural signal, not naming convention — the app you're pointed at may call things anything.

## 1. Find the shell component

Grep the whole `src/` tree for `router-view`:

```
grep -rl "router-view" src/
```

Whichever file contains `<router-view` (usually exactly one, sometimes wrapped in a `<transition>` or `<keep-alive>`) is the chrome/shell component, regardless of its filename. Everything outside that `<router-view>` in its template is persistent chrome — nav, header, global modals, footers.

## 2. Find the nav markup

Inside the shell component, look for:
- A `<nav>` or `<header>` element
- Containing multiple sibling `<router-link>` or `<a>` elements
- Or an element whose class name contains `nav`, `header`, `menu`, `tabs`, `sidebar` (the last one may mean a sidebar already partially exists — check before assuming a top-nav-only layout)

Note whether the nav is currently horizontal (top bar) or already vertical — this skill's job is to end at a left vertical sidebar either way, but a partial sidebar may already have components worth reusing (icons, active-state logic).

## 3. Find companion pieces coupled to nav position/height

Grep for layout coupling that will break once the nav's shape changes:

```
grep -rn "sticky\|position: *fixed\|top: *[0-9]" src/
```

Any hardcoded `top:` value that isn't `0` is a candidate for recalculation — it's very likely keyed to the current nav's height so that some other element (a filter bar, a secondary toolbar) stays visible just below it.

## 4. Find profile/account menus

Search component names and template content for `dropdown`, `menu`, `profile`, `account`, `avatar`. Note its current anchor position (usually top-right of the nav) and open-direction (`top: calc(100% + Xpx)` = opens downward). This will need to flip when relocated to a sidebar footer.

## 5. Enumerate the authoritative route list

Read the router config (wherever `createRouter`/`createWebHistory` is called, typically `src/main.js`, `src/router.js`, or `src/router/index.js`). The `routes` array is ground truth for "what pages exist." Cross-check:

- Does every route have a corresponding nav link in the shell component? (A view file existing in `src/views/` with no route or no nav link is a common gap — flag it.)
- If the app has i18n (look for `vue-i18n`, a custom `useI18n` composable, or a `locales/` directory), does every nav label have a translation key in every locale file? Flag any nav label that's hardcoded in one language while everything else goes through the translation function.

Carry these gaps forward into Phase 5 (migrate companion pieces) of `SKILL.md` — fix them in the same pass rather than leaving them for later, since you're already touching the nav.

## 6. Check for an existing design system

Before assuming there are no design tokens, check for:
- A `:root { }` block with `--`-prefixed custom properties anywhere in the codebase
- Tailwind config (`tailwind.config.js`) — if present, the app already has a token system (Tailwind's theme) and this skill's token work should map onto Tailwind theme extension, not a parallel CSS variable system
- A `src/styles/` or `src/assets/` directory with shared stylesheets

If Tailwind or an existing token system is present, adapt Phase 2 of `SKILL.md` to extend it rather than introducing a competing one.
