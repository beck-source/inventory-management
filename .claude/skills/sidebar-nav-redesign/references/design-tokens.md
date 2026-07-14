# Design tokens: extract, don't invent

The fastest way to make a redesign feel disconnected from the app it came from is to replace its existing colors and spacing with a generic new palette. Instead, mine the app's current hardcoded values and formalize them into CSS custom properties. The redesign should feel like the same app, tidied up — not a different app wearing the old app's logo.

## Method

1. Grep the shell component and 2–3 representative components/views for hex colors, `rem`/`px`/`em` spacing values, and `border-radius` values:
   ```
   grep -rno "#[0-9a-fA-F]\{3,6\}" src/ | sort | uniq -c | sort -rn
   grep -rno "[0-9.]\+rem\|[0-9]\+px" src/ | sort | uniq -c | sort -rn
   ```
2. Cluster near-duplicates (`#2563eb` and `#2563EB` are the same color; `1.5rem` appearing 40 times is a real spacing unit, `1.37rem` appearing once probably isn't).
3. Name the survivors as tokens by **role**, not by raw value — a future edit to "the primary color" shouldn't require renaming a variable called `--blue-600`.

## Minimal token set to always produce

**Spacing scale** — a 4px or 8px multiple ladder, however many steps the app's actual usage supports (don't invent 10 steps if the app only really uses 4 distinct spacing values):
```css
--space-1: 0.25rem;
--space-2: 0.5rem;
--space-3: 0.75rem;
--space-4: 1rem;
--space-5: 1.5rem;
--space-6: 2rem;
```

**Color roles:**
```css
--color-bg: ...;           /* page background */
--color-surface: ...;      /* card/panel background */
--color-border: ...;       /* dividers, card borders */
--color-text: ...;         /* primary text */
--color-text-muted: ...;   /* secondary/caption text */
--color-primary: ...;      /* brand/action color */
--color-primary-hover: ...;
--color-accent: ...;       /* if the app has a secondary brand color */
```
If the app has status colors (success/warning/danger badges, etc.), extract those too as `--color-success`, `--color-warning`, `--color-danger` — don't leave them as scattered literals.

**Radius scale:**
```css
--radius-sm: ...;
--radius-md: ...;
--radius-lg: ...;
```

**Shadow tokens** (only if the app already uses box-shadow anywhere):
```css
--shadow-sm: ...;
--shadow-md: ...;
```

## Where to put the block

Put the `:root { }` block in whichever file already holds global unscoped styles — usually the shell component's `<style>` block (found in Phase 1 discovery), or an existing `src/styles/`/`src/assets/` global stylesheet if one exists. Don't create a new global CSS file unless the app has zero existing convention for one; introducing a new file pattern is a bigger footprint than the redesign needs.

If the app already uses Tailwind, extend `tailwind.config.js`'s `theme.extend` with these same role names instead of hand-writing CSS custom properties — don't run two token systems side by side.

## Applying tokens

Once defined, the sidebar and its companion pieces (Phases 3–5 in `SKILL.md`) should reference tokens exclusively — no new hardcoded hex/px values introduced by this redesign. Existing components elsewhere in the app do not need to be swept and converted to tokens as part of this task unless the user asks for that separately; scope the token conversion to the chrome being touched.
