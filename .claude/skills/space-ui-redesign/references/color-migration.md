# Color migration: light theme to Orbital Command tokens

Most Vue apps hardcode light-theme colors in `<style scoped>` blocks and inline SVG. Convert them by **role**, not by exact value. Ask what the color is doing, then pick the token for that job.

## Mapping table

| Role in old code | Typical old values | Token |
|---|---|---|
| Page background | `#f8fafc`, `#f1f5f9`, `#fafafa`, `white` on body | remove (the backdrop shows through) |
| Card / panel background | `#fff`, `white`, `#ffffff` | `var(--surface)` (or just use `.card`) |
| Nested well, table header, input bg | `#f8fafc`, `#f1f5f9`, `#f3f4f6` | `var(--surface-sunken)` |
| Hover background | `#f1f5f9`, `#e2e8f0`, `#f9fafb` | `var(--surface-raised)` |
| Modal / dropdown bg | `#fff` + shadow | `var(--surface-strong)` (or `.modal`, `.dropdown`) |
| Border / divider | `#e2e8f0`, `#e5e7eb`, `#cbd5e1`, `#d1d5db` | `var(--line)`, emphasis `var(--line-strong)` |
| Primary text | `#0f172a`, `#111827`, `#1e293b`, `#334155` | `var(--text)` |
| Secondary text | `#64748b`, `#6b7280`, `#475569` | `var(--text-muted)` |
| Tertiary / placeholder | `#94a3b8`, `#9ca3af` | `var(--text-faint)` |
| Brand / primary / link | `#3b82f6`, `#2563eb`, `#6366f1` | `var(--cyan)`; buttons `.btn-primary` |
| Success (green) | `#10b981`, `#22c55e`, `#16a34a`, `#059669` | `var(--success)` / bg `var(--success-bg)` |
| Info (blue) | `#3b82f6`, `#0ea5e9`, `#dbeafe` (bg) | `var(--info)` / `var(--info-bg)` |
| Warning (amber) | `#f59e0b`, `#eab308`, `#fef3c7` (bg) | `var(--warning)` / `var(--warning-bg)` |
| Danger (red) | `#ef4444`, `#dc2626`, `#fee2e2` (bg) | `var(--danger)` / `var(--danger-bg)` |
| Pale status pill bg | `#dcfce7`, `#dbeafe`, `#fef3c7`, `#fee2e2` | matching `--*-bg` token |
| Dark text on pale pill | `#166534`, `#1e40af`, `#92400e`, `#991b1b` | matching bright status token (neon text on dark) |
| Box shadow | `0 1px 3px rgba(0,0,0,.1)` | `var(--shadow-panel)`; hover glow `var(--glow-cyan)` |
| Focus outline | `outline: 2px solid #3b82f6` | `box-shadow: var(--focus-ring)` |

**Inverted pairs.** Light themes put dark text on pale backgrounds (`#991b1b` on `#fee2e2`). In this theme it flips to neon text on a translucent tint (`--danger` on `--danger-bg`). Don't carry the dark text color over.

**Radii and spacing.** Snap stray values to the nearest step. Spacing is `4 8 12 16 20 24 32 40 48` → `--space-*`. Radii are `6 / 10 / 16 / pill` → `--radius-*`.

**Fonts.** Remove per-component `font-family` declarations. Numbers, IDs, SKUs, dates and labels get `font-family: var(--font-mono)`. Don't use Orbitron outside the brand, page titles and modal titles.

## SVG charts

Hand-built SVG charts need the most care.

1. **Series colors.** Replace hardcoded `fill`/`stroke` with the series tokens in order: `var(--series-1)` … `var(--series-6)`. Inline SVG attributes accept `var()` when set through `:style` or a CSS class, e.g. `:style="{ stroke: 'var(--series-1)' }"`, or `class="series-1"` with `.series-1 { stroke: var(--series-1) }`.
2. **Gradients.** Area fills look best as vertical fades. Add a `<defs>` block once per chart:
   ```html
   <defs>
     <linearGradient id="area-1" x1="0" y1="0" x2="0" y2="1">
       <stop offset="0%"  style="stop-color: var(--series-1); stop-opacity: .45"/>
       <stop offset="100%" style="stop-color: var(--series-1); stop-opacity: 0"/>
     </linearGradient>
     <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
       <feGaussianBlur stdDeviation="3" result="b"/>
       <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
     </filter>
   </defs>
   ```
   Gradient and filter IDs must be unique per component instance if the chart can appear twice on a page. Suffix them with a uid.
3. **Glow only on the primary series**: `filter="url(#glow)"`. Using it on every series turns into mush.
4. **Axes, grid, labels.** Grid lines use `stroke: var(--chart-grid)`. Axis text uses `fill: var(--chart-axis)` plus `font-family: var(--font-mono)` at 10–11 px. Set `fill="currentColor"` on text only if the parent sets `color`.
5. **Donut / ring charts.** Use a `var(--surface-sunken)` track, `stroke-linecap: round` segments in series order, and a center value in mono with the `.text-aurora` treatment through a `<foreignObject>` or overlaid HTML. SVG `<text>` can't use `background-clip`, so use a plain `fill: var(--text)` with a glow filter instead.
6. **Bars.** Vertical gradient from `--series-n` to transparent at 30 %, plus a 2 px bright cap (`rect` height 2 at the top) for a "plasma" look.
7. **Goal / threshold lines.** Dashed `stroke: var(--magenta)` with a small mono label.
8. **Tooltips** are HTML positioned over the chart, styled like `.dropdown`.

## Inline `style="..."` and JS-computed colors

Search the `<template>` and `<script>` too, not just `<style>`. Look for status-to-color maps (`{ Delivered: '#10b981' }`) in JS and change their values to `'var(--success)'` and so on. Most `:style` bindings accept CSS variables directly.

## Done criteria per file
- `audit-colors.sh` reports 0 hits, or only documented exceptions.
- No `white`/`#fff` backgrounds remain. Light surfaces are the most common leftover and break the theme badly.
- Text on every surface is readable. Spot-check muted text on `--surface-sunken`.
