# Design Tokens Reference

Complete CSS custom property system for the SaaS redesign. Add the `:root` block at the top of App.vue's `<style>` section (not scoped). All existing global CSS classes are then updated to reference these tokens instead of hardcoded values.

---

## Complete `:root` Token Block

```css
:root {
  /* ── Layout ─────────────────────────────────── */
  --sidebar-width: 220px;

  /* ── Sidebar (dark variant — default) ───────── */
  --sidebar-bg: #0f172a;
  --sidebar-text: #94a3b8;
  --sidebar-text-hover: #e2e8f0;
  --sidebar-text-active: #ffffff;
  --sidebar-item-active-bg: rgba(59, 130, 246, 0.15);
  --sidebar-accent: #3b82f6;

  /* ── Surface colours ────────────────────────── */
  --surface-bg: #f8fafc;
  --surface-card: #ffffff;
  --surface-border: #e2e8f0;
  --surface-border-strong: #cbd5e1;
  --surface-hover: #f1f5f9;
  --surface-active: #e2e8f0;

  /* ── Text ───────────────────────────────────── */
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --text-inverse: #ffffff;

  /* ── Brand / accent ─────────────────────────── */
  --color-blue: #2563eb;
  --color-blue-bg: #eff6ff;
  --color-blue-border: #bfdbfe;

  /* ── Status colours ─────────────────────────── */
  --color-success: #059669;
  --color-success-bg: #d1fae5;
  --color-success-text: #065f46;

  --color-warning: #d97706;
  --color-warning-bg: #fef3c7;
  --color-warning-text: #92400e;

  --color-danger: #dc2626;
  --color-danger-bg: #fecaca; /* kept for badge.danger; use --color-danger-surface for large areas */
  --color-danger-surface: #fef2f2;
  --color-danger-text: #991b1b;

  --color-info: #2563eb;
  --color-info-bg: #dbeafe;
  --color-info-text: #1e40af;

  /* ── Trend badges ───────────────────────────── */
  --color-increasing-bg: #d1fae5;
  --color-increasing-text: #065f46;
  --color-stable-bg: #e0e7ff;
  --color-stable-text: #3730a3;
  --color-decreasing-bg: #fecaca;
  --color-decreasing-text: #991b1b;

  /* ── Spacing ────────────────────────────────── */
  --space-page: 1.75rem;      /* outer padding of .page-content */
  --space-card: 1.25rem;      /* .card internal padding */
  --space-gap: 1.25rem;       /* gaps between cards / grid items */
  --space-section: 1.5rem;    /* margin-bottom between sections */

  /* ── Shape ──────────────────────────────────── */
  --radius-card: 10px;
  --radius-badge: 6px;
  --radius-btn: 8px;
  --radius-input: 6px;

  /* ── Shadows ────────────────────────────────── */
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-modal: 0 20px 60px rgba(0, 0, 0, 0.15);

  /* ── Typography ─────────────────────────────── */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;

  --text-xs: 0.75rem;     /* 12px */
  --text-sm: 0.813rem;    /* 13px */
  --text-base: 0.875rem;  /* 14px  ← default body size */
  --text-md: 0.938rem;    /* 15px */
  --text-lg: 1.125rem;    /* 18px */
  --text-xl: 1.375rem;    /* 22px */
  --text-2xl: 1.875rem;   /* 30px */

  /* ── Transitions ────────────────────────────── */
  --transition-fast: 0.15s ease;
  --transition-base: 0.2s ease;
}
```

---

## Global Component Styles (Token-updated)

Replace the corresponding blocks in App.vue's `<style>` section. Classes must be **preserved** — only property values change.

### Body and base

```css
body {
  font-family: var(--font-sans);
  background: var(--surface-bg);
  color: var(--text-primary);
  font-size: var(--text-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Page header

```css
.page-header {
  margin-bottom: var(--space-section);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-md);
}
```

### Stats grid + stat card

```css
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-gap);
  margin-bottom: var(--space-section);
}

.stat-card {
  background: var(--surface-card);
  padding: var(--space-card);
  border-radius: var(--radius-card);
  border: 1px solid var(--surface-border);
  box-shadow: var(--shadow-card);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.stat-card:hover {
  border-color: var(--surface-border-strong);
  box-shadow: var(--shadow-card-hover);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger  .stat-value { color: var(--color-danger);  }
.stat-card.info    .stat-value { color: var(--color-info);    }
```

### Card

```css
.card {
  background: var(--surface-card);
  border-radius: var(--radius-card);
  padding: var(--space-card);
  border: 1px solid var(--surface-border);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--space-gap);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--surface-border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}
```

### Table

```css
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-bg);
  border-top: 1px solid var(--surface-border);
  border-bottom: 1px solid var(--surface-border);
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--surface-hover);
  color: var(--text-secondary);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--surface-hover);
}
```

### Badges

```css
.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-badge);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success    { background: var(--color-success-bg);    color: var(--color-success-text);    }
.badge.warning    { background: var(--color-warning-bg);    color: var(--color-warning-text);    }
.badge.danger     { background: var(--color-danger-bg);     color: var(--color-danger-text);     }
.badge.info       { background: var(--color-info-bg);       color: var(--color-info-text);       }
.badge.increasing { background: var(--color-increasing-bg); color: var(--color-increasing-text); }
.badge.stable     { background: var(--color-stable-bg);     color: var(--color-stable-text);     }
.badge.decreasing { background: var(--color-decreasing-bg); color: var(--color-decreasing-text); }
.badge.high       { background: var(--color-danger-bg);     color: var(--color-danger-text);     }
.badge.medium     { background: var(--color-warning-bg);    color: var(--color-warning-text);    }
.badge.low        { background: var(--color-info-bg);       color: var(--color-info-text);       }
```

### Loading and error states

```css
.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-size: var(--text-md);
}

.error {
  background: var(--color-danger-surface);
  border: 1px solid var(--color-danger-bg);
  color: var(--color-danger-text);
  padding: 1rem;
  border-radius: var(--radius-input);
  margin: 1rem 0;
  font-size: var(--text-md);
}
```

---

## Dark Mode Variant

Add after the `:root` block. Overrides surface and text tokens; sidebar tokens are already dark and unchanged.

```css
@media (prefers-color-scheme: dark) {
  :root {
    --surface-bg: #0f172a;
    --surface-card: #1e293b;
    --surface-border: #334155;
    --surface-border-strong: #475569;
    --surface-hover: #1e293b;
    --surface-active: #334155;

    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;

    --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2);
    --shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.3);

    /* Status bg slightly darkened for dark surfaces */
    --color-success-bg: rgba(6, 95, 70, 0.25);
    --color-warning-bg: rgba(146, 64, 14, 0.25);
    --color-danger-bg: rgba(153, 27, 27, 0.25);
    --color-danger-surface: rgba(153, 27, 27, 0.15);
    --color-info-bg: rgba(30, 64, 175, 0.25);
    --color-increasing-bg: rgba(6, 95, 70, 0.25);
    --color-stable-bg: rgba(55, 48, 163, 0.25);
    --color-decreasing-bg: rgba(153, 27, 27, 0.25);
  }
}
```

> **Implementation note:** This app doesn't have a dark mode toggle — the `@media` block is optional and only activates for users with a system dark preference. Safe to omit if keeping scope minimal.

---

## Typography Scale Quick Reference

| Token | Value | Use |
|---|---|---|
| `--text-xs` | 12px | Badge text, table headers (uppercase) |
| `--text-sm` | 13px | Secondary labels, footnotes |
| `--text-base` | 14px | Default body, table cells |
| `--text-md` | 15px | Nav items, prominent body text |
| `--text-lg` | 18px | Card titles |
| `--text-xl` | 22px | Logo / brand name |
| `--text-2xl` | 30px | Page `h2`, stat values |

---

## Spacing Quick Reference

| Token | Value | Use |
|---|---|---|
| `--space-page` | 1.75rem | Outer page padding |
| `--space-card` | 1.25rem | Card internal padding |
| `--space-gap` | 1.25rem | Grid gaps, card margins |
| `--space-section` | 1.5rem | Between major page sections |
