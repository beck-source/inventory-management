# Default design tokens

Put these in the global stylesheet (`:root`). If the app already has brand colors, keep them and map them onto these names. Example: an existing slate palette `#0f172a / #64748b / #e2e8f0` maps to `--text / --text-muted / --border`.

```css
:root {
  /* Spacing: 4px base. Use only these values for margin, padding, and gap. */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Type: a few sizes, applied consistently */
  --font-sans: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;   /* SaaS body text is usually 14px */
  --text-lg: 16px;
  --text-xl: 18px;
  --text-2xl: 22px;
  --text-3xl: 28px;    /* KPI numbers */
  --leading: 1.5;

  /* Surfaces & text (slate-based neutral) */
  --bg: #f8fafc;             /* app background behind cards */
  --surface: #ffffff;        /* cards, header */
  --surface-muted: #f1f5f9;  /* table header, hover */
  --border: #e2e8f0;
  --text: #0f172a;
  --text-muted: #64748b;
  --text-subtle: #94a3b8;

  /* Sidebar (dark rail reads as "SaaS"; a light sidebar with a right border also works) */
  --sidebar-bg: #0f172a;
  --sidebar-text: #cbd5e1;
  --sidebar-text-active: #ffffff;
  --sidebar-item-hover: rgba(255, 255, 255, 0.06);
  --sidebar-item-active: rgba(255, 255, 255, 0.10);
  --sidebar-width-expanded: 240px;
  --sidebar-width-collapsed: 64px;
  --header-height: 60px;

  /* Accent & status */
  --accent: #2563eb;
  --accent-soft: #eff6ff;
  --success: #16a34a;  --success-soft: #f0fdf4;
  --info:    #2563eb;  --info-soft:    #eff6ff;
  --warning: #ca8a04;  --warning-soft: #fefce8;
  --danger:  #dc2626;  --danger-soft:  #fef2f2;

  /* Shape & depth */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 999px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.16);
  --focus-ring: 0 0 0 3px rgba(37, 99, 235, 0.35);

  /* Motion */
  --ease: cubic-bezier(0.2, 0, 0, 1);
  --duration: 180ms;

  /* Layering: modals must stay above the drawer */
  --z-sidebar: 30;
  --z-header: 20;
  --z-backdrop: 40;
  --z-drawer: 50;
  --z-modal: 100;
}

@media (prefers-reduced-motion: reduce) {
  :root { --duration: 0ms; }
}

body {
  margin: 0;
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading);
  color: var(--text);
  background: var(--bg);
  -webkit-font-smoothing: antialiased;
}
```

Only load Inter from Google Fonts if the project already loads web fonts. Otherwise the system stack is fine.

## Shared component classes (upgrade existing ones, don't duplicate)

```css
.page { padding: var(--space-6) var(--space-8); }
.page-header { display: flex; align-items: flex-start; justify-content: space-between;
  gap: var(--space-4); margin-bottom: var(--space-6); }
.page-header h1 { font-size: var(--text-2xl); font-weight: 600; margin: 0; }
.page-header p { color: var(--text-muted); margin: var(--space-1) 0 0; }

.card { background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); padding: var(--space-6); }
.card-title { font-size: var(--text-lg); font-weight: 600; margin: 0 0 var(--space-4); }

.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-4); margin-bottom: var(--space-6); }
.stat-label { font-size: var(--text-sm); color: var(--text-muted); }
.stat-value { font-size: var(--text-3xl); font-weight: 600; font-variant-numeric: tabular-nums; }

table { width: 100%; border-collapse: collapse; }
th { text-align: left; font-size: var(--text-xs); font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--text-muted); background: var(--surface-muted);
  padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--border); }
td { padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--border); }
tbody tr:hover { background: var(--surface-muted); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }

.badge { display: inline-flex; align-items: center; padding: 2px var(--space-2);
  border-radius: var(--radius-full); font-size: var(--text-xs); font-weight: 500; }
.badge.success { background: var(--success-soft); color: var(--success); }
.badge.info    { background: var(--info-soft);    color: var(--info); }
.badge.warning { background: var(--warning-soft); color: var(--warning); }
.badge.danger  { background: var(--danger-soft);  color: var(--danger); }

:focus-visible { outline: none; box-shadow: var(--focus-ring); }

@media (max-width: 1023px) { .page { padding: var(--space-4); } }
```

Rename these to match the class names the views already use (e.g. `.stat-card`, `.kpi`, `.status-badge`), so existing markup picks up the new look without template edits.
