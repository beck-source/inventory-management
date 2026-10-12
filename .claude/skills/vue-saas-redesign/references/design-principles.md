# Design principles — the SaaS look

This file defines the visual language. The aim is a calm, dense-but-breathable
interface that reads as a professional product: clear hierarchy, consistent rhythm,
one accent color, restrained elevation.

## Adapt to the existing palette first

Before inventing colors, extract what the app already uses (search the global
stylesheet and a few components for hex values and font families). Map those into
**roles** rather than copying raw hex everywhere:

- `--color-bg` — app background (usually the lightest neutral)
- `--color-surface` — cards/panels (usually white)
- `--color-border` — hairlines and dividers
- `--color-text` / `--color-text-muted` — primary and secondary text
- `--color-accent` (+ `--color-accent-weak` for tinted backgrounds) — the single
  brand/action color, reused for active nav, primary buttons, links
- status roles: `--color-success`, `--color-warning`, `--color-danger`, `--color-info`

Seeding tokens from existing values means the redesign changes *structure and
consistency* without a jarring repaint. Introduce new color only where the app had
none (e.g. a dedicated sidebar surface).

## Spacing scale

Use a single 4px-based scale and reference it everywhere — this is the biggest
lever for a "polished" feel, because inconsistent padding is what makes UIs look
amateur.

```
--space-1: 4px    --space-2: 8px    --space-3: 12px   --space-4: 16px
--space-5: 24px   --space-6: 32px   --space-7: 48px   --space-8: 64px
```

Rules of thumb: card padding `--space-5`; gaps between cards `--space-5`; section
gaps `--space-6`; label↔value `--space-2`; icon↔text `--space-3`. Pick one value per
relationship and reuse it — never hand-tune one-off pixel values.

## Typography

- One font family (keep the app's if it has one). A small type scale:
  `--text-xs 12 / --text-sm 14 / --text-base 15 / --text-lg 18 / --text-xl 24 / --text-2xl 30`.
- Weights: 400 body, 500 emphasis, 600–700 headings/values.
- Use muted text (`--color-text-muted`) and uppercase micro-labels with letter
  spacing for section/stat labels — a hallmark of the SaaS look.
- Tabular numbers for tables/metrics where available.

## Hierarchy & density

- Establish three levels: page title → section/card title → body.
- Generous but consistent whitespace; don't fill every pixel. Whitespace signals
  quality.
- Tables: comfortable row height, subtle zebra or hover, hairline row separators,
  sticky header for long tables.

## Elevation & shape

- Keep it flat. Prefer 1px borders over heavy shadows. Use at most a soft shadow on
  raised/floating elements (menus, modals):
  `--shadow-sm: 0 1px 2px rgba(15,23,42,.06)` and
  `--shadow-md: 0 4px 12px rgba(15,23,42,.08)`.
- One radius scale: `--radius-sm 6 / --radius-md 10 / --radius-lg 14`. Pick one for
  cards and reuse it.

## Color usage discipline

- Exactly one accent color for interactive emphasis (active nav item, primary
  button, links, focus ring). Everything else is neutral + status colors.
- Active/selected states: accent text on an `--color-accent-weak` tint, optionally a
  left or bottom accent bar.
- Always show a visible focus ring (accessibility): `outline: 2px solid var(--color-accent)`.

## What to avoid

- Multiple competing accent colors, heavy drop shadows, gradients as chrome.
- Emojis as icons — use inline SVG.
- One-off magic-number paddings — always reference the spacing scale.
