# Design tokens

Define these once on `:root`. If the project already has a palette, keep its hues and map them to these names. If it has none, use the defaults below (a slate neutral scale with a blue accent, which also fits this repository's existing slate palette).

```css
:root {
  /* Spacing: 4px base. Use only these steps. */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* Radius */
  --radius-sm: 6px;   /* inputs, buttons, badges */
  --radius-md: 8px;   /* cards, nav items */
  --radius-lg: 12px;  /* modals, large panels */

  /* Type */
  --font-sans: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, "SFMono-Regular", Menlo, monospace;
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-lg: 16px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 28px;
  --leading-tight: 1.25;
  --leading-normal: 1.5;

  /* Neutrals: slate, slightly blue-biased so they sit well with the accent */
  --bg-app: #f8fafc;        /* page background */
  --bg-surface: #ffffff;    /* cards, tables, sidebar */
  --bg-subtle: #f1f5f9;     /* hover rows, inputs at rest */
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #0f172a;
  --text-muted: #64748b;
  --text-faint: #94a3b8;

  /* Accent */
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-soft: #eff6ff;   /* active nav item background, selected rows */

  /* Semantic status. Always pair with a text label, never color alone. */
  --success: #15803d;  --success-soft: #f0fdf4;
  --warning: #a16207;  --warning-soft: #fefce8;
  --danger: #b91c1c;   --danger-soft: #fef2f2;
  --info: #1d4ed8;     --info-soft: #eff6ff;

  /* Elevation: keep to two levels */
  --shadow-sm: 0 1px 2px rgb(15 23 42 / 0.06);
  --shadow-md: 0 8px 24px rgb(15 23 42 / 0.12);  /* drawers, menus, modals only */

  /* Layout */
  --sidebar-width: 240px;
  --sidebar-width-collapsed: 64px;  /* icon (18px) plus nav padding, centered */
  --content-max: 1280px;
  --focus-ring: 0 0 0 3px rgb(37 99 235 / 0.35);
}
```

## Dark mode (only if the app already supports it)

Redefine the same names. Do not add dark mode to an app that has none unless asked.

```css
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg-app: #0b1120; --bg-surface: #111a2e; --bg-subtle: #172036;
    --border: #243049; --border-strong: #33415f;
    --text: #e2e8f0; --text-muted: #94a3b8; --text-faint: #64748b;
    --accent: #60a5fa; --accent-hover: #93c5fd; --accent-soft: #14213d;
    --success: #4ade80; --success-soft: #0f2a1d;
    --warning: #facc15; --warning-soft: #2a2410;
    --danger: #f87171;  --danger-soft: #2a1414;
    color-scheme: dark;
  }
}
```

## Usage rules

- Component CSS references tokens only: `padding: var(--space-4)`, never `padding: 15px`.
- Page gutters are `--space-6` on desktop and `--space-4` on phone widths.
- Gaps between sibling blocks use flex or grid `gap`, not margins.
- Body text is `--text-base`; table cells `--text-sm`; captions and labels `--text-xs`.
- Uppercase labels get `letter-spacing: 0.06em` and `--text-xs`.
- Load a font through the project's existing method. If none exists, the system stack above is acceptable.
