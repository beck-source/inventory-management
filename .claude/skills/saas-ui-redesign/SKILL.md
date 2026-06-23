# SaaS UI Redesign Skill

Transform Vue 3 applications into modern SaaS-style interfaces with professional layouts, sidebar navigation, and consistent design systems.

## What This Skill Does

Guides the complete redesign of a Vue 3 application's UI from a top-navigation layout to a modern SaaS-style interface featuring:
- Left sidebar navigation (collapsible)
- Vertical navigation with icons and labels
- Professional spacing and typography
- Consistent color system
- Card-based layouts
- Responsive design
- Polished interactions and animations

## When to Use This Skill

- Redesigning an existing Vue 3 application layout
- Creating a new SaaS product UI
- Modernizing an outdated application interface
- Implementing consistent design across multiple views
- Building professional dashboard/admin interfaces

## Key Design Principles

### 1. Sidebar Navigation Pattern
**Benefits:**
- More screen real estate for content
- Better for complex navigation hierarchies
- Standard SaaS pattern (users expect it)
- Supports collapsible state for larger content areas

**Layout Structure:**
```
┌─────────────────────────────────┐
│ Sidebar    │      Main Content  │
│  (fixed    │                    │
│  width)    │  (flexible width)  │
│            │                    │
└─────────────────────────────────┘
```

### 2. Consistent Spacing System
Use a base unit of 4px or 8px for all spacing:
- **4px grid**: Fine-grained spacing
- **8px base**: Primary unit
- **16px**: Common sections
- **24px**: Between major sections
- **32px**: Large breaks
- **48px**: Page-level spacing

### 3. Professional Typography
- **Headings**: Bold, larger size, limited color variation
- **Body text**: Medium weight, high contrast
- **Labels**: Small, slightly muted
- **Line height**: 1.5 for readability, 1.6 for body text

### 4. Color System
**Essential Colors:**
- **Primary**: #3b82f6 (Interactive, buttons, highlights)
- **Background**: #ffffff (Main content)
- **Surface**: #f8fafc (Cards, elevated surfaces)
- **Border**: #e2e8f0 (Dividers, outlines)
- **Text Primary**: #0f172a (Main text)
- **Text Secondary**: #64748b (Muted text)
- **Status**: Green (#10b981), Yellow (#f59e0b), Red (#ef4444), Blue (#3b82f6)

### 5. Component Styling
**Cards:**
- Background: white with subtle shadow
- Border: 1px light border or shadow
- Border-radius: 8px
- Padding: 20px or 24px

**Buttons:**
- Primary: Solid blue, white text
- Secondary: White background, blue text, border
- Hover: Darker or opacity change
- Disabled: Grayed out

**Inputs & Selects:**
- Border: 1px light gray
- Padding: 10px 12px
- Focus: Blue outline or border
- Background: White
- Font: Inherit system font

## Implementation Checklist

### Phase 1: Layout Foundation
- [ ] Create Sidebar.vue component
- [ ] Create SidebarItem.vue for navigation items
- [ ] Modify App.vue to use sidebar layout
- [ ] Add collapse/expand state management
- [ ] Implement responsive breakpoints
- [ ] Set up CSS variables for colors and spacing

### Phase 2: Navigation
- [ ] Move navigation links from top bar to sidebar
- [ ] Add icon support to navigation items
- [ ] Implement active link styling
- [ ] Add "current section" highlighting
- [ ] Create dropdown/submenu pattern (if needed)

### Phase 3: Header Area
- [ ] Create TopHeader.vue component
- [ ] Move user profile menu to top-right
- [ ] Move language switcher to top-right
- [ ] Add breadcrumb navigation (optional)
- [ ] Style consistently with sidebar

### Phase 4: Main Content
- [ ] Adjust main content width and padding
- [ ] Update FilterBar layout
- [ ] Ensure consistent card styling
- [ ] Apply spacing system throughout
- [ ] Update table/list layouts

### Phase 5: Polish & Details
- [ ] Add sidebar collapse animation
- [ ] Implement hover states
- [ ] Add focus states for accessibility
- [ ] Test on mobile/tablet
- [ ] Fine-tune spacing and alignment

### Phase 6: Consistency Pass
- [ ] Audit all colors against system
- [ ] Verify spacing throughout
- [ ] Check typography consistency
- [ ] Review interactive states
- [ ] Test dark mode (if applicable)

## Component Patterns

### 1. Sidebar Component Pattern

**Key Features:**
- Fixed position (left side)
- Configurable width (typically 240-280px)
- Collapsible (toggled state)
- Smooth animations
- Mobile-responsive (slides in/out)

**Structure:**
```vue
<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <img src="logo.svg" alt="Logo" class="logo">
      <button v-if="isMobile" @click="toggleSidebar" class="collapse-btn">
        ✕
      </button>
    </div>
    
    <nav class="sidebar-nav">
      <SidebarItem
        v-for="item in navItems"
        :key="item.path"
        :item="item"
        :active="currentPath === item.path"
      />
    </nav>
    
    <div class="sidebar-footer">
      <p class="text-muted">Version 1.0</p>
    </div>
  </aside>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
  setup() {
    const collapsed = ref(false)
    const isMobile = ref(window.innerWidth < 768)
    const route = useRoute()
    
    const currentPath = computed(() => route.path)
    
    const toggleSidebar = () => {
      collapsed.value = !collapsed.value
    }
    
    return {
      collapsed,
      isMobile,
      currentPath,
      toggleSidebar
    }
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 240px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 1000;
}

.sidebar.collapsed {
  transform: translateX(-100%);
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.logo {
  height: 32px;
  width: auto;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 16px 8px;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  text-align: center;
  font-size: 0.875rem;
  color: #64748b;
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    position: fixed;
    z-index: 1100;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  .sidebar.collapsed {
    transform: translateX(-100%);
  }
}
</style>
```

### 2. Sidebar Item Component

**Interactive Navigation Items:**
```vue
<template>
  <router-link
    :to="item.path"
    class="sidebar-item"
    :class="{ active }"
    :title="item.label"
  >
    <span class="sidebar-item-icon" v-if="item.icon">
      {{ item.icon }}
    </span>
    <span class="sidebar-item-label">
      {{ item.label }}
    </span>
  </router-link>
</template>

<script>
export default {
  props: {
    item: {
      type: Object,
      required: true
      // { path, label, icon }
    },
    active: Boolean
  }
}
</script>

<style scoped>
.sidebar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 4px 0;
  border-radius: 6px;
  color: #475569;
  text-decoration: none;
  transition: all 0.2s ease;
  font-size: 0.9375rem;
  cursor: pointer;
}

.sidebar-item:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.sidebar-item.active {
  background: #dbeafe;
  color: #0369a1;
  font-weight: 600;
}

.sidebar-item-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.sidebar-item-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
```

### 3. Top Header Component

**Header with User Menu:**
```vue
<template>
  <header class="top-header">
    <div class="header-left">
      <button class="toggle-sidebar-btn" @click="$emit('toggle-sidebar')">
        ☰
      </button>
      <div class="breadcrumbs">
        <!-- Optional breadcrumb trail -->
      </div>
    </div>
    
    <div class="header-right">
      <div class="header-actions">
        <LanguageSwitcher />
        <button class="header-icon-btn" title="Notifications">
          🔔
        </button>
      </div>
      <div class="divider"></div>
      <ProfileMenu />
    </div>
  </header>
</template>

<style scoped>
.top-header {
  position: sticky;
  top: 0;
  left: 240px;
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
  transition: left 0.3s ease;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toggle-sidebar-btn {
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 8px;
}

.header-icon-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 8px;
  color: #64748b;
}

.header-icon-btn:hover {
  color: #0f172a;
}

.divider {
  width: 1px;
  height: 32px;
  background: #e2e8f0;
}

@media (max-width: 768px) {
  .top-header {
    left: 0;
  }
  
  .toggle-sidebar-btn {
    display: block;
  }
}
</style>
```

### 4. Main Content Layout

**Adjusted App.vue Structure:**
```vue
<template>
  <div class="app">
    <Sidebar ref="sidebar" />
    
    <div class="main-layout">
      <TopHeader @toggle-sidebar="toggleSidebar" />
      
      <FilterBar />
      
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  min-height: 100vh;
  background: #f9fafb;
}

.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 240px;
  transition: margin-left 0.3s ease;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .main-layout {
    margin-left: 0;
  }
}
</style>
```

## Spacing Guidelines

**Page Structure:**
```
┌──────────────────────────────┐  24px top padding
│ Page Title / Header          │
├──────────────────────────────┤
│                              │  20px vertical between sections
│ Filter Bar (if present)      │
├──────────────────────────────┤
│                              │
│ Content Area                 │
│ - Cards with 20px padding    │
│ - 16px gap between items     │
│ - 24px between sections      │
│                              │
└──────────────────────────────┘  24px bottom padding
```

**Card Layouts:**
- Padding: 20px or 24px
- Gap between cards: 16px (in grid)
- Icon + text gap: 12px
- Border-radius: 8px
- Box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1)

## Typography Scale

```
H1: 2.0rem (32px) - Page titles
H2: 1.5rem (24px) - Section titles
H3: 1.25rem (20px) - Subsection titles
H4: 1.125rem (18px) - Card titles
Body: 0.9375rem (15px) - Normal text
Small: 0.875rem (14px) - Secondary text
Label: 0.8125rem (13px) - Form labels
```

**Line Heights:**
- Headings: 1.2
- Body text: 1.6
- Form inputs: 1.5

## Color Usage Guidelines

**When to Use Each Color:**
- **Primary Blue (#3b82f6)**: Buttons, active states, links, interactive elements
- **Text Primary (#0f172a)**: Main content, headings
- **Text Secondary (#64748b)**: Labels, descriptions, muted text
- **Background (#f9fafb)**: Page background
- **Surface (#f8fafc)**: Card backgrounds, elevated surfaces
- **Border (#e2e8f0)**: Dividers, borders, subtle separators
- **Status Green (#10b981)**: Success, completed, online status
- **Status Yellow (#f59e0b)**: Warning, pending, caution
- **Status Red (#ef4444)**: Error, critical, offline

## Responsive Design

**Breakpoints:**
- Mobile: < 640px (sidebar hidden by default)
- Tablet: 640px - 1024px (sidebar collapsible)
- Desktop: > 1024px (sidebar visible)

**Mobile Considerations:**
- Sidebar becomes overlay/drawer
- Top header becomes more compact
- Touch-friendly button sizes (44px minimum)
- Filter bar may stack vertically
- Increased horizontal padding

## Implementation Steps

### Step 1: Create Layout Components
1. Create `Sidebar.vue` with fixed positioning
2. Create `SidebarItem.vue` for nav items
3. Create `TopHeader.vue` with user menu
4. Create CSS variable system for colors/spacing

### Step 2: Update App.vue
1. Replace `<header>` with new layout structure
2. Add Sidebar component
3. Wrap content in `main-layout` div
4. Adjust router-view placement

### Step 3: Style Main Content
1. Update `main-content` padding
2. Adjust margin/left based on sidebar
3. Update FilterBar styling
4. Ensure responsive behavior

### Step 4: Update Views
1. Apply consistent card styling
2. Update spacing in all views
3. Use CSS variables for colors
4. Test layout responsiveness

### Step 5: Polish & Animation
1. Add smooth transitions for sidebar collapse
2. Implement hover states
3. Add focus states
4. Test accessibility

## Common Pitfalls to Avoid

**❌ Don't:**
- Use arbitrary padding values - stick to spacing system
- Mix colors from different systems
- Create new component styles instead of reusing
- Skip responsive testing
- Ignore accessibility (contrast, focus states)
- Over-animate (keep it subtle, <0.3s)

**✅ Do:**
- Use CSS variables for all colors and spacing
- Create reusable component patterns
- Test on mobile, tablet, desktop
- Ensure sufficient color contrast (WCAG AA)
- Keep animations subtle and purposeful
- Use semantic HTML

## Testing Checklist

**Visual:**
- [ ] Spacing is consistent throughout
- [ ] Colors match the design system
- [ ] Typography hierarchy is clear
- [ ] Sidebar collapse works smoothly
- [ ] Hover/active states are distinct

**Responsive:**
- [ ] Mobile (< 640px) layout works
- [ ] Tablet (640-1024px) layout works
- [ ] Desktop (> 1024px) layout works
- [ ] Sidebar hides on mobile (drawer mode)
- [ ] No horizontal scrolling at any breakpoint

**Accessibility:**
- [ ] Color contrast >= 4.5:1 for text
- [ ] Focus states are visible
- [ ] Keyboard navigation works
- [ ] Links are clearly identifiable
- [ ] Form fields are properly labeled

**Performance:**
- [ ] Animations are smooth (60fps)
- [ ] Sidebar collapse is instant
- [ ] No layout shift issues
- [ ] Images are optimized

## File Organization

```
src/
├── components/
│   ├── Sidebar.vue
│   ├── SidebarItem.vue
│   ├── TopHeader.vue
│   ├── FilterBar.vue
│   └── ... other components
├── styles/
│   ├── variables.css      # CSS custom properties
│   ├── typography.css     # Font scales
│   └── spacing.css        # Spacing utilities
└── App.vue
```

## Example CSS Variables

```css
:root {
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 12px;
  --spacing-lg: 16px;
  --spacing-xl: 24px;
  --spacing-2xl: 32px;
  
  /* Colors */
  --color-primary: #3b82f6;
  --color-primary-dark: #2563eb;
  --color-text-primary: #0f172a;
  --color-text-secondary: #64748b;
  --color-bg: #ffffff;
  --color-bg-secondary: #f8fafc;
  --color-border: #e2e8f0;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  
  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-base: 0.9375rem;
  --line-height-base: 1.6;
  
  /* Transitions */
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

## Next Steps After Redesign

1. **User Testing**: Get feedback on new layout
2. **Performance Audit**: Check bundle size, load times
3. **Accessibility Audit**: WCAG 2.1 AA compliance
4. **Cross-browser Testing**: Chrome, Firefox, Safari, Edge
5. **Mobile Testing**: Real device testing, not just DevTools
6. **Analytics**: Track user behavior with new layout

## Resources & References

- [Tailwind CSS Spacing](https://tailwindcss.com/docs/customizing-spacing)
- [Material Design Spacing](https://material.io/design/layout/spacing-methods.html)
- [Web Content Accessibility Guidelines](https://www.w3.org/WAI/standards-guidelines/wcag/)
- [Vue 3 Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)

## Questions to Ask

When starting a redesign, clarify:
1. Do we need a collapsible sidebar or always visible?
2. Should there be multi-level navigation menus?
3. Do we need breadcrumb navigation?
4. Should we support dark mode?
5. Are there performance constraints?
6. What's the target audience (mobile-first or desktop)?
7. Do we need analytics on navigation usage?

---

**Note**: This skill assumes Vue 3 with Composition API. Adapt as needed for your specific project requirements.
