# Design Tokens Checklist

Use this reference during Step 3 (Establish or consolidate design tokens) to extract scattered colors and spacing into a unified token system, then populate it with values brainstormed via the `frontend-design` skill.

## Detecting the current token state

### No token system (colors/spacing scattered and hardcoded)
**Signs:**
- Hex color literals (`#0f172a`, `#64748b`) repeated throughout CSS (in `App.vue`'s global styles, view-level scoped styles, component styles).
- Spacing defined as pixel literals (`12px`, `16px`, `24px`) without a consistent scale or naming.
- Grep results for `#[0-9a-f]{3,6}` and `\d+px` yield dozens of matches across multiple files.
- No SCSS `$variables`, no CSS custom properties (`:root { --color-primary: ... }`), no Tailwind `theme` config.

**Action:** Build a new token system from scratch (see "Establishing tokens" below).

### Partial token system (some tokens, some hardcoded)
**Signs:**
- CSS custom properties exist in one file (e.g., `tokens.css`) but aren't used everywhere (some views still hardcode hex values).
- SCSS variables exist but are only used in one component/view directory.
- A Tailwind theme is partially configured, but some colors are hardcoded in vanilla CSS blocks.

**Action:** Audit the existing system, extend it to cover the gaps, and migrate hardcoded values to use the existing tokens.

### Full token system (colors/spacing consistently use tokens)
**Signs:**
- All colors use CSS custom properties or SCSS variables, no hardcoded hex literals.
- Spacing uses a consistent scale (e.g., `var(--space-1)` through `var(--space-6)`).
- Tailwind theme or CSS-in-JS configuration covers all colors, type scales, spacing, radii.

**Action:** Add sidebar-specific tokens to the existing system (see "Adding sidebar-specific tokens" below). Invoke `frontend-design` for aesthetic direction on any palette gaps, then integrate its recommendations into the existing token structure.

## Minimal token set for a sidebar redesign

At minimum, a sidebar redesign needs these token categories:

### 1. Color tokens

A minimal palette for a SaaS interface:

| Token name | Purpose | Example value |
|---|---|---|
| `--color-brand` | Primary brand color, used in highlights, links, CTAs | `#2563eb` (blue) |
| `--color-neutral-0` / `--color-neutral-100` / `--color-neutral-200` ... | Neutral grays for text, backgrounds, borders (light to dark) | `#ffffff`, `#f8fafc`, `#e2e8f0`, `#94a3b8`, `#475569`, `#1e293b` |
| `--color-surface-primary` | Primary background color (pages, cards) | `#ffffff` or `#f8fafc` |
| `--color-surface-secondary` | Secondary background (sections, subtle grouping) | `#f1f5f9` |
| `--color-border` | Border color for dividers, input outlines | `#e2e8f0` |
| `--color-text-primary` | Main text color | `#1e293b` (dark) |
| `--color-text-muted` | Secondary/deemphased text | `#64748b` (medium gray) |
| `--color-status-success` | Green, for success/positive states | `#10b981` |
| `--color-status-warning` | Yellow/amber, for warnings | `#f59e0b` |
| `--color-status-danger` / `--color-status-error` | Red, for errors/critical states | `#ef4444` |
| `--color-status-info` | Blue, for informational states | `#3b82f6` |

If you're already using these hex literals in the current codebase, extract them and map them to token names. Then source final *values* from `frontend-design` (invoking the Skill tool) — don't just copy-paste the old hex codes, as the goal is to move away from generic defaults.

### 2. Spacing tokens

Define a spacing scale, typically in multiples (4px, 8px, 16px, etc.):

| Token name | Value | Use case |
|---|---|---|
| `--space-1` | `0.25rem` (4px) | Icon spacing, tight grouping |
| `--space-2` | `0.5rem` (8px) | Small padding, gaps between small elements |
| `--space-3` | `0.75rem` (12px) | Sidebar item padding (vertical) |
| `--space-4` | `1rem` (16px) | Standard padding, gaps between sections |
| `--space-5` | `1.5rem` (24px) | Larger gaps, page margins |
| `--space-6` | `2rem` (32px) | Page-level margins |

Use these consistently for padding, margins, and gaps throughout the sidebar and main layout.

### 3. Sidebar-specific tokens

New tokens for the sidebar structure:

| Token name | Value | Purpose |
|---|---|---|
| `--sidebar-width-expanded` | `240px` or `280px` | Sidebar width when fully open |
| `--sidebar-width-collapsed` | `64px` or `80px` | Sidebar width when collapsed to icon rail |
| `--sidebar-item-height` | `44px` or `48px` | Height of each nav item (touch-friendly) |
| `--sidebar-transition` | `0.3s ease` | Duration/easing for collapse/expand animation |
| `--sidebar-border-color` | `var(--color-border)` or custom | Divider between sidebar and main |

### 4. Typography tokens (if not already in place)

| Token name | Value | Use case |
|---|---|---|
| `--text-xs` | `12px` | Small labels, captions |
| `--text-sm` | `14px` | Body text, secondary content |
| `--text-base` | `16px` | Default body text |
| `--text-lg` | `18px` | Subheadings, larger labels |
| `--text-xl` | `20px` | Section headings |
| `--text-2xl` | `24px` | Page headings |

### 5. Other utilities

| Token name | Value | Use case |
|---|---|---|
| `--radius-sm` | `4px` | Small buttons, badges |
| `--radius-md` | `8px` | Cards, modals |
| `--radius-lg` | `12px` | Larger elements |
| `--shadow-sm` | `0 1px 2px rgba(0, 0, 0, 0.05)` | Subtle elevation |
| `--shadow-md` | `0 4px 6px rgba(0, 0, 0, 0.1)` | Standard elevation |

## Establishing a new token system

### Step 1: Choose a location

Pick **one** approach that matches your project's existing tooling:

#### Approach A: Global CSS custom properties (simplest for most Vue 3 apps)
Create a `src/assets/tokens.css` or `src/styles/tokens.css`:

```css
:root {
  /* Colors */
  --color-brand: #2563eb;
  --color-neutral-0: #ffffff;
  --color-neutral-100: #f8fafc;
  --color-text-primary: #1e293b;
  /* ... more colors ... */
  
  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  /* ... more spacing ... */
  
  /* Sidebar */
  --sidebar-width-expanded: 240px;
  --sidebar-width-collapsed: 64px;
  --sidebar-item-height: 44px;
}

/* Accessible color scheme for dark mode (optional) */
@media (prefers-color-scheme: dark) {
  :root {
    --color-neutral-0: #0f172a;
    --color-text-primary: #f1f5f9;
    /* ... invert palette ... */
  }
}
```

Import globally in `src/main.js`:
```js
import './assets/tokens.css'
```

Then use in any CSS:
```css
.sidebar {
  width: var(--sidebar-width-expanded);
  background: var(--color-surface-primary);
}
```

#### Approach B: SCSS/SCSS variables
If the project already uses SCSS:

Create `src/styles/_tokens.scss`:
```scss
// Colors
$color-brand: #2563eb;
$color-neutral-0: #ffffff;
// ... etc ...

// Spacing scale
$space-1: 0.25rem;
$space-2: 0.5rem;
// ... etc ...

// Convert to CSS custom properties so they work in Vue single-file components too
:root {
  --color-brand: #{$color-brand};
  --color-neutral-0: #{$color-neutral-0};
  // ... etc ...
}
```

Import in `src/main.scss` or the build entry point, and use `$variable` syntax in SCSS files or `var(--variable)` in CSS/Vue templates.

#### Approach C: Tailwind configuration (if Tailwind is already installed)
Extend `tailwind.config.js`:

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: '#2563eb',
        neutral: {
          0: '#ffffff',
          100: '#f8fafc',
          // ... etc ...
        },
        status: {
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
        },
      },
      spacing: {
        1: '0.25rem',
        2: '0.5rem',
        // ... etc ...
      },
      width: {
        'sidebar': '240px',
        'sidebar-collapsed': '64px',
      },
    },
  },
}
```

Then use Tailwind class syntax: `class="w-sidebar bg-neutral-100 text-neutral-900"`.

**Choose Approach A if:** No other CSS tooling is in place; simplest to set up. **Choose Approach B if:** Project already uses SCSS. **Choose Approach C if:** Project already uses Tailwind.

### Step 2: Extract existing colors into tokens

Run a grep to find all hardcoded hex colors:
```bash
grep -r '#[0-9a-f]\{3,6\}' src/ --include="*.vue" --include="*.css" --include="*.scss"
```

Document the unique hex values found (e.g., `#0f172a`, `#64748b`, `#2563eb`, etc.) and group them by role (primary text, borders, brand color, etc.). Map each group to a token name (e.g., `#0f172a` → `--color-text-primary`).

### Step 3: Source values from frontend-design

Before finalizing token values, invoke the Skill tool for `frontend-design` with a brief like:

> Design a modern SaaS sidebar and app interface for an inventory-management application (tracks warehouse stock, orders, spending, demand forecasting). The audience is operations/supply-chain teams who need quick visibility into stock and orders. Brainstorm a token system (color palette, spacing scale, typography) that feels intentional and polished, not generic.

Take the palette and spacing recommendations from `frontend-design` and map them to your token names. This ensures the sidebar isn't a generic SaaS default.

### Step 4: Replace hardcoded values

Once tokens are in place and populated, do a **global find-and-replace**:

1. Replace `#0f172a` with `var(--color-text-primary)` across all `.vue`, `.css`, `.scss` files.
2. Replace `#64748b` with `var(--color-text-muted)`.
3. Replace `16px` padding with `var(--space-4)`.
4. Etc. for each extracted literal.

**Before committing, take a screenshot.** Visually compare the app before and after to ensure nothing broke — colors should look identical since they're the same hex values, just moved to variables.

### Step 5: Add sidebar-specific tokens

With the base token system in place, add the new tokens needed for the sidebar:

```css
:root {
  /* ... existing tokens ... */
  
  /* Sidebar layout */
  --sidebar-width-expanded: 240px;
  --sidebar-width-collapsed: 64px;
  --sidebar-item-height: 44px;
  --sidebar-transition: 0.3s ease;
  --sidebar-bg: var(--color-surface-primary);
  --sidebar-border: 1px solid var(--color-border);
  
  /* Sidebar text */
  --sidebar-text-primary: var(--color-text-primary);
  --sidebar-text-muted: var(--color-text-muted);
  --sidebar-active-bg: var(--color-brand);
  --sidebar-active-text: white;
  --sidebar-hover-bg: var(--color-neutral-100);
}
```

These layer on top of the base tokens and keep sidebar styling DRY.

## Integrating into an existing token system

If the project already has a token system (Tailwind config, existing CSS variables, SCSS variables):

1. **Audit the existing tokens.** Do they cover colors, spacing, typography, radius, shadows? What gaps exist?
2. **Extend, don't duplicate.** Add sidebar-specific tokens to the existing system, not a parallel system.
3. **Invoke frontend-design** for guidance on aesthetic gaps (e.g., should the sidebar use a different color theme? Should it have a distinct visual weight?).
4. **Migrate remaining hardcoded values** from old patterns to the extended token system.

---

**Quick audit template:**

- **Current token system present?** Yes / No / Partial
- **Location:** `_____` (file path or config location)
- **Hardcoded colors found:** `#___, #___, ...` (hex values)
- **Hardcoded spacing found:** `___px, ___px, ...`
- **Gaps in existing system:** `_____`
- **Sidebar-specific tokens to add:** width-expanded, width-collapsed, item-height, transition, ...
