# Component patterns

Apply these through each view's scoped CSS and class names. Reuse existing classes where they exist and change their declarations; add new classes only where the markup has no suitable hook. All values come from `design-tokens.md`.

## Page header

Each view opens with a title, an optional one-line description, and actions aligned to the right.

```css
.page-header { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-6); }
.page-title { margin: 0; font-size: var(--text-2xl); line-height: var(--leading-tight); font-weight: 600; letter-spacing: -0.01em; }
.page-subtitle { margin: var(--space-1) 0 0; color: var(--text-muted); font-size: var(--text-base); }
```

## Cards and panels

Border first, shadow rarely. Do not give every block the same treatment: stat tiles, chart panels and tables can share the base card; nested blocks inside a card use a plain divider.

```css
.card { background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-6); }
.card-title { margin: 0 0 var(--space-4); font-size: var(--text-lg); font-weight: 600; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--space-4); }
.card-grid > * { min-width: 0; }
```

Stat tile: a muted label above, a large value, and an optional delta chip. Values use `font-variant-numeric: tabular-nums`.

## Tables

Wrap wide tables in a container with `overflow-x: auto` so the page itself never scrolls sideways.

```css
.table-wrap { background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-md); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
th { position: sticky; top: 0; background: var(--bg-subtle); color: var(--text-muted); font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; text-align: left; padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--border); }
td { padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--border); vertical-align: middle; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: var(--bg-subtle); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
```

## Buttons

Three variants only: primary, secondary, ghost. One primary button per region.

```css
.btn { display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2); height: 36px; padding: 0 var(--space-4); border-radius: var(--radius-sm); border: 1px solid transparent; font: 500 var(--text-base)/1 var(--font-sans); cursor: pointer; }
.btn:focus-visible { outline: none; box-shadow: var(--focus-ring); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn-secondary { background: var(--bg-surface); color: var(--text); border-color: var(--border-strong); }
.btn-secondary:hover:not(:disabled) { background: var(--bg-subtle); }
.btn-ghost { background: transparent; color: var(--text-muted); }
.btn-ghost:hover:not(:disabled) { background: var(--bg-subtle); color: var(--text); }
```

## Badges and status

A badge always carries a text label; color supports it, never replaces it.

```css
.badge { display: inline-flex; align-items: center; height: 22px; padding: 0 var(--space-2); border-radius: var(--radius-sm); font-size: var(--text-xs); font-weight: 600; }
.badge-success { background: var(--success-soft); color: var(--success); }
.badge-warning { background: var(--warning-soft); color: var(--warning); }
.badge-danger  { background: var(--danger-soft);  color: var(--danger); }
.badge-info    { background: var(--info-soft);    color: var(--info); }
.badge-neutral { background: var(--bg-subtle);    color: var(--text-muted); }
```

Map the app's existing statuses (for example order status or stock level) to these classes by editing the existing class names' declarations, not the logic that chooses them.

## Form controls

```css
.input, select.input { height: 36px; padding: 0 var(--space-3); background: var(--bg-surface); color: var(--text); border: 1px solid var(--border-strong); border-radius: var(--radius-sm); font: var(--text-base) var(--font-sans); }
.input:focus-visible { outline: none; border-color: var(--accent); box-shadow: var(--focus-ring); }
.field-label { display: block; margin-bottom: var(--space-1); color: var(--text-muted); font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
```

## Modals

```css
.modal-backdrop { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center; padding: var(--space-4); background: rgb(15 23 42 / 0.5); }
.modal { width: min(560px, 100%); max-height: calc(100vh - 2 * var(--space-4)); overflow-y: auto; background: var(--bg-surface); border-radius: var(--radius-lg); box-shadow: var(--shadow-md); }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-4) var(--space-6); border-bottom: 1px solid var(--border); }
.modal-body { padding: var(--space-6); }
.modal-footer { display: flex; justify-content: flex-end; gap: var(--space-2); padding: var(--space-4) var(--space-6); border-top: 1px solid var(--border); }
```
Modals sit above the drawer (`z-index: 50` against the drawer's 40) so a modal opened from the sidebar footer, such as a profile or tasks modal, is not hidden behind it.

## Charts

If charts are custom SVG, restyle them through tokens: axis and label text in `--text-muted` at `--text-xs`, gridlines in `--border`, series in the accent plus semantic colors. Do not change chart data computations or `viewBox` math.

## Loading, empty and error states

Keep the existing `v-if` structure. Style each state to match: a muted centered message with `--space-12` of vertical padding for empty and loading, and a `--danger-soft` panel with `--danger` text for errors.

## Per-view checklist

- [ ] Page header present and consistent
- [ ] All spacing and colors come from tokens; no stray literals
- [ ] Tables and wide charts scroll inside their own container
- [ ] Buttons, badges and inputs use the shared classes or equivalent declarations
- [ ] Hover, focus-visible and disabled states exist
- [ ] Works at about 390px wide without horizontal page scroll
