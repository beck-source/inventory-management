# Design Tokens

The current client hardcodes every color, radius, and spacing value inline throughout
`client/src/App.vue`'s global `<style>` block. The first step of the redesign is to introduce
a single source of truth as CSS custom properties on `:root`, then refactor the existing rules
to consume them.

**Palette is preserved** — these tokens are lifted directly from the values already in
App.vue (slate neutrals, `#2563eb` brand, semantic success/warning/danger/info). The point is
consistency and a spacing scale, not a new color scheme.

## The `:root` block

Add this at the very top of the global `<style>` in `App.vue` (before the `*` reset). Then
replace literal values elsewhere with `var(--token)`.

```css
:root {
  /* ---- Neutrals (slate) ---- */
  --color-bg:            #f8fafc;  /* app background, subtle surfaces */
  --color-surface:       #ffffff;  /* cards, sidebar, nav */
  --color-border:        #e2e8f0;  /* default borders / dividers */
  --color-border-strong: #cbd5e1;  /* hover borders */
  --color-text:          #334155;  /* body text */
  --color-text-strong:   #0f172a;  /* headings */
  --color-text-muted:    #64748b;  /* secondary / labels */
  --color-text-subtle:   #475569;  /* table headers */

  /* ---- Brand ---- */
  --color-primary:       #2563eb;
  --color-primary-dark:  #1e40af;
  --color-primary-soft:  #eff6ff;  /* active nav background */
  --color-focus-ring:    rgba(59, 130, 246, 0.1);

  /* ---- Semantic (text on tinted bg) ---- */
  --color-success:     #059669;  --color-success-bg:  #d1fae5;  --color-success-ink: #065f46;
  --color-warning:     #ea580c;  --color-warning-bg:  #fed7aa;  --color-warning-ink: #92400e;
  --color-danger:      #dc2626;  --color-danger-bg:   #fecaca;  --color-danger-ink:  #991b1b;
  --color-info:        #2563eb;  --color-info-bg:     #dbeafe;  --color-info-ink:    #1e40af;

  /* ---- Spacing scale (4px base, 8px rhythm) ---- */
  --space-1: 0.25rem;  /*  4px */
  --space-2: 0.5rem;   /*  8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-12: 3rem;    /* 48px */

  /* ---- Radius ---- */
  --radius-sm: 6px;    /* buttons, inputs, badges */
  --radius-md: 10px;   /* cards, panels */
  --radius-full: 9999px;

  /* ---- Shadows ---- */
  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);

  /* ---- Typography ---- */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
               Ubuntu, Cantarell, sans-serif;

  /* ---- Layout ---- */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 68px;
  --content-max: 1440px;

  /* ---- Z-index scale ---- */
  --z-sidebar: 50;
  --z-filterbar: 40;
  --z-dropdown: 200;
  --z-modal: 1000;
}
```

## Refactor guidance

When applying tokens, map the existing literals like this (non-exhaustive):

| Current literal | Token |
|---|---|
| `background: #f8fafc` (body) | `var(--color-bg)` |
| `#ffffff` card/nav backgrounds | `var(--color-surface)` |
| `#e2e8f0` borders | `var(--color-border)` |
| `#0f172a` headings | `var(--color-text-strong)` |
| `#64748b` labels/subtitles | `var(--color-text-muted)` |
| `#2563eb` active/brand | `var(--color-primary)` |
| `padding: 1.25rem` (cards) | `var(--space-5)` |
| `padding: 1.5rem 2rem` (main) | `var(--space-6) var(--space-8)` |
| `gap: 1.25rem` (grids) | `var(--space-5)` |
| `border-radius: 10px` | `var(--radius-md)` |
| `border-radius: 6px` | `var(--radius-sm)` |
| header `box-shadow` | `var(--shadow-sm)` |

**Consistency rule:** after refactoring, no spacing value in App.vue's global styles should be
an arbitrary rem literal — round each to the nearest step on the scale (`--space-1`…`--space-12`).
Snap odd values (`0.313rem`, `0.375rem`, `0.625rem`, `0.813rem`, `0.938rem`) to the nearest token;
prefer `--space-2`/`--space-3` over reintroducing one-off decimals.
