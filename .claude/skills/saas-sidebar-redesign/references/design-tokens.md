# Design tokens

Define these once on `:root`, then use them everywhere. Values below are a sensible default; map them onto the app's existing palette (keep its brand and status colors where they exist) instead of introducing a new look.

## Contents

- Spacing, radius, elevation
- Typography
- Color (light, dark)
- Layout and layering
- Usage rules

## Spacing, radius, elevation

A 4px base keeps everything on a grid. Use only these steps; if a value you need is not here, pick the nearest step.

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;

  --radius-sm: 6px;   /* inputs, badges, buttons */
  --radius-md: 10px;  /* cards, table containers */
  --radius-lg: 14px;  /* modals */

  --shadow-sm: 0 1px 2px rgb(15 23 42 / 0.06);
  --shadow-md: 0 4px 12px rgb(15 23 42 / 0.08);
  --shadow-lg: 0 12px 32px rgb(15 23 42 / 0.16);
}
```

## Typography

```css
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-lg: 16px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
}
```

Page titles use `--text-2xl` semibold, section/card titles `--text-lg` semibold, body `--text-base`, captions and table headers `--text-xs`/`--text-sm` in the muted color.

## Color

Name colors by role, not by hue, so the dark theme only has to redefine the values.

```css
:root {
  --color-bg: #f8fafc;            /* page background */
  --color-surface: #ffffff;       /* cards, modals */
  --color-surface-muted: #f1f5f9; /* table headers, hover rows */
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-muted: #64748b;

  --color-primary: #2563eb;
  --color-primary-soft: #eff6ff;
  --color-success: #16a34a;
  --color-warning: #ca8a04;
  --color-danger: #dc2626;

  /* Sidebar has its own colors so it can differ from the page (a dark sidebar on a light page is common) */
  --sidebar-bg: #0f172a;
  --sidebar-text: #cbd5e1;
  --sidebar-text-active: #ffffff;
  --sidebar-item-hover: rgb(255 255 255 / 0.06);
  --sidebar-item-active: rgb(255 255 255 / 0.12);
  --sidebar-border: rgb(255 255 255 / 0.08);
}

:root[data-theme="dark"] {
  --color-bg: #0b1120;
  --color-surface: #111827;
  --color-surface-muted: #1f2937;
  --color-border: #263244;
  --color-text: #e5e7eb;
  --color-text-muted: #94a3b8;
  --color-primary: #60a5fa;
  --color-primary-soft: rgb(96 165 250 / 0.14);
  --color-success: #4ade80;
  --color-warning: #facc15;
  --color-danger: #f87171;
  --sidebar-bg: #060a14;
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.4);
  --shadow-md: 0 4px 12px rgb(0 0 0 / 0.45);
  --shadow-lg: 0 12px 32px rgb(0 0 0 / 0.6);
}
```

When no theme is saved, set the initial `data-theme` from `window.matchMedia('(prefers-color-scheme: dark)')`. Verify text/background pairs reach at least 4.5:1 contrast in both themes.

## Layout and layering

```css
:root {
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 72px;
  --content-max-width: 1280px;
  /* Drawer breakpoint is 900px. Custom properties cannot be used inside @media, so there is no token; repeat the literal and comment it. */

  --z-sticky: 10;
  --z-sidebar: 30;      /* desktop sidebar; the mobile drawer uses --z-backdrop + 1 so it stays above its backdrop */
  --z-backdrop: 40;
  --z-modal: 50;       /* grep the app's existing modals first and match their z-index (this app used 1000/2000) */
  --z-popover: 60;
}
```

Fixed content width is a judgment call: 1280px suits text-heavy pages, but dense dashboards and wide tables may need around 1600px. Pick based on the widest existing view.

## Usage rules

- Page padding: `--space-5` on desktop, `--space-4` on mobile. Gap between cards and between sections: `--space-4` or `--space-5`, pick one per layout and keep it.
- Card padding `--space-5`; compact tables and list rows `--space-3` vertical, `--space-4` horizontal.
- One border color (`--color-border`), 1px. Prefer a border over a shadow for resting cards; reserve shadows for things that float (menus, drawers, modals).
- Interactive elements share a 36px minimum height (44px touch target on mobile) and the same focus ring: `outline: 2px solid var(--color-primary); outline-offset: 2px`.
- Status colors mean the same thing everywhere (success, warning, danger, info). Reuse them for badges, stat cards and chart accents rather than inventing per-view colors.
- Do not use emojis as icons or decoration.
