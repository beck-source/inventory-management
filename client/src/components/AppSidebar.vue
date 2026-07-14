<template>
  <div
    v-if="mobileOpen"
    class="sidebar-backdrop"
    @click="setMobileOpen(false)"
  ></div>

  <aside
      class="sidebar"
      :class="{ collapsed: effectiveCollapsed, 'mobile-open': mobileOpen }"
    >
      <div class="sidebar-brand">
        <slot name="brand">
          <span class="sidebar-brand-label">{{ brandLabel }}</span>
          <span v-if="brandSubtitle" class="sidebar-brand-subtitle">{{ brandSubtitle }}</span>
        </slot>

        <button
          v-if="!isCompactViewport"
          type="button"
          class="sidebar-collapse-toggle"
          :aria-expanded="!collapsed"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="toggleCollapsed"
        >
          <span aria-hidden="true">{{ collapsed ? '»' : '«' }}</span>
        </button>
      </div>

      <nav class="sidebar-nav" aria-label="Primary">
        <ul class="sidebar-list">
          <li v-for="item in navItems" :key="item.key">
            <router-link
              :to="item.to"
              class="sidebar-link"
              :class="{ active: isActive(item) }"
              :title="effectiveCollapsed ? item.label : null"
              @click="onNavigate(item)"
            >
              <span class="sidebar-link-icon" aria-hidden="true">
                <NavIcon :name="item.icon" />
              </span>
              <span v-if="!effectiveCollapsed" class="sidebar-link-label">{{ item.label }}</span>
            </router-link>
          </li>
        </ul>
      </nav>

      <div class="sidebar-footer">
        <slot name="footer"></slot>
      </div>
  </aside>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRoute } from 'vue-router'
import NavIcon from './NavIcon.vue'

const props = defineProps({
  navItems: {
    type: Array,
    required: true
  },
  collapsed: {
    type: Boolean,
    default: false
  },
  mobileOpen: {
    type: Boolean,
    default: false
  },
  brandLabel: {
    type: String,
    default: ''
  },
  brandSubtitle: {
    type: String,
    default: ''
  },
  storageKey: {
    type: String,
    default: 'app-sidebar-collapsed'
  }
})

const emit = defineEmits(['update:collapsed', 'update:mobileOpen', 'navigate'])

const route = useRoute()

// Between the mobile drawer breakpoint (768px) and full desktop width, the
// sidebar automatically switches to icon-only mode regardless of the user's
// manual collapse preference — there isn't enough room for a labeled rail
// alongside typical page content at these widths. The collapse toggle is
// hidden in this range since the state isn't user-controlled there.
const COMPACT_MEDIA_QUERY = '(min-width: 769px) and (max-width: 1099px)'
const isCompactViewport = ref(false)
let compactMediaQueryList = null

function updateCompactViewport(event) {
  isCompactViewport.value = event.matches
}

onMounted(() => {
  compactMediaQueryList = window.matchMedia(COMPACT_MEDIA_QUERY)
  isCompactViewport.value = compactMediaQueryList.matches
  compactMediaQueryList.addEventListener('change', updateCompactViewport)
})

onBeforeUnmount(() => {
  compactMediaQueryList?.removeEventListener('change', updateCompactViewport)
})

// On mobile, the sidebar opens as a full-width overlay drawer — collapse
// (icon-only) mode is a desktop-only concept, so ignore `collapsed` while
// the mobile drawer is open. In the compact viewport range, icon-only mode
// is forced regardless of the user's stored preference.
const effectiveCollapsed = computed(() => (props.collapsed || isCompactViewport.value) && !props.mobileOpen)

function isActive(item) {
  if (item.exact || item.to === '/') {
    return route.path === item.to
  }
  return route.path === item.to || route.path.startsWith(item.to + '/')
}

function toggleCollapsed() {
  const next = !props.collapsed
  emit('update:collapsed', next)
  try {
    localStorage.setItem(props.storageKey, String(next))
  } catch (err) {
    // localStorage may be unavailable — collapse still works for the session.
  }
}

function setMobileOpen(value) {
  emit('update:mobileOpen', value)
}

function onNavigate(item) {
  emit('navigate', item)
  if (props.mobileOpen) {
    setMobileOpen(false)
  }
}

onMounted(() => {
  try {
    const stored = localStorage.getItem(props.storageKey)
    if (stored !== null) {
      emit('update:collapsed', stored === 'true')
    }
  } catch (err) {
    // localStorage may be unavailable — fall back to the collapsed prop.
  }
})
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  width: var(--sidebar-width-expanded);
  height: 100vh;
  position: sticky;
  top: 0;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  transition: width var(--sidebar-transition);
  overflow-x: hidden;
  z-index: var(--z-sidebar);
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4);
  min-height: var(--topbar-height);
  flex-shrink: 0;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-brand-label {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-brand-subtitle {
  font-size: 0.75rem;
  color: #64748b;
  white-space: nowrap;
  display: block;
}

.sidebar-collapse-toggle {
  margin-left: auto;
  border: 1px solid #e2e8f0;
  background: white;
  color: #64748b;
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  border-radius: 6px;
  flex-shrink: 0;
}

.sidebar-collapse-toggle:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.sidebar-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: 8px;
  text-decoration: none;
  color: #64748b;
  font-weight: 500;
  font-size: 0.938rem;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.sidebar-link:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.sidebar-link.active {
  color: #2563eb;
  background: #eff6ff;
  font-weight: 600;
}

.sidebar-link-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-link-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar.collapsed .sidebar-link {
  justify-content: center;
  padding-left: var(--space-2);
  padding-right: var(--space-2);
}

.sidebar-footer {
  flex-shrink: 0;
  padding: var(--space-3);
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sidebar-backdrop {
  display: none;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    transform: translateX(-100%);
    transition: transform var(--sidebar-transition);
    width: var(--sidebar-width-expanded);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: var(--z-sidebar-backdrop);
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar-collapse-toggle {
    transition: none;
  }
}
</style>
