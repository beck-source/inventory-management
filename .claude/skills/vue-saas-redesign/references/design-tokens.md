# Design tokens and shared component styles

Drop into `src/styles/tokens.css` and import once from `main.js`. Replace the accent with the app's brand color if it has one. All sizes sit on a 4px grid.

```css
:root {
  /* Spacing */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px;

  /* Neutrals (slate) */
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-muted: #f1f5f9;
  --border: #e2e8f0;
  --text: #0f172a;
  --text-muted: #64748b;

  /* Accent and status */
  --accent: #2563eb;
  --accent-soft: #eff6ff;
  --success: #16a34a;  --warning: #d97706;  --danger: #dc2626;  --info: #2563eb;

  /* Shape */
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  /* Type */
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --text-xs: 12px; --text-sm: 13px; --text-base: 14px; --text-lg: 16px;
  --text-xl: 20px; --text-2xl: 24px;

  /* Layout */
  --sidebar-w: 240px; --sidebar-w-collapsed: 72px; --topbar-h: 64px;
  --content-max: 1440px;
  --ease: 150ms ease;
}
@media (prefers-reduced-motion: reduce) { :root { --ease: 0ms; } }
```

## Shared patterns (global styles)

- **Page**: padding `var(--space-8)` (mobile `var(--space-4)`); page title `--text-2xl`, weight 600, subtitle `--text-muted`, 24px below.
- **Card**: `background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); padding: var(--space-6)`. Card header: title `--text-lg` weight 600, bottom border, 16px padding below.
- **Stat tile**: card with a `--text-sm` muted label above a `--text-2xl` value; status tint only on the value or a thin left accent.
- **Table**: no outer border inside a card; header row `--surface-muted`, `--text-xs` uppercase muted labels, 12px by 16px cell padding, row separators `1px solid var(--border)`, hover `--surface-muted`.
- **Button**: height 36px, padding 0 `--space-4`, radius `--radius-md`. Primary filled accent; secondary white with border; focus ring `0 0 0 3px var(--accent-soft)` plus accent border.
- **Inputs and selects**: same height and radius as buttons, border `--border`, same focus ring.
- **Badge**: pill, `--text-xs`, weight 500, soft tinted background with the status color as text.
- **Empty and loading states**: centered muted text with 48px vertical padding inside the card.
- **Grid**: `display: grid; gap: var(--space-6)`, `repeat(auto-fit, minmax(240px, 1fr))` for tiles.
