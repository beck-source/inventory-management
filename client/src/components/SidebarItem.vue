<template>
  <router-link
    :to="to"
    class="sidebar-item"
    :class="{ active: isActive, collapsed }"
    :title="collapsed ? label : ''"
  >
    <span class="item-icon" aria-hidden="true">
      <slot name="icon">
        <span v-if="icon">{{ icon }}</span>
      </slot>
    </span>
    <span class="item-label" :class="{ hidden: collapsed }">{{ label }}</span>
    <span v-if="badge && !collapsed" class="item-badge">{{ badge }}</span>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  to: {
    type: String,
    required: true
  },
  label: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    default: ''
  },
  badge: {
    type: [String, Number],
    default: null
  },
  collapsed: {
    type: Boolean,
    default: false
  },
  exact: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()

const isActive = computed(() => {
  if (props.exact) {
    return route.path === props.to
  }
  return route.path === props.to || route.path.startsWith(props.to + '/')
})
</script>

<style scoped>
.sidebar-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5625rem 0.75rem;
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s ease;
  white-space: nowrap;
  overflow: hidden;
  position: relative;
}

.sidebar-item:hover {
  color: var(--color-text-primary);
  background: var(--color-surface-alt);
}

.sidebar-item.active {
  color: var(--color-primary-text);
  background: var(--color-primary-soft);
  font-weight: 600;
}

.sidebar-item.active .item-icon {
  color: var(--color-primary);
}

.sidebar-item.collapsed {
  justify-content: center;
  padding: 0.5625rem;
}

.item-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  transition: color 0.15s ease;
}

.sidebar-item:hover .item-icon {
  color: var(--color-text-secondary);
}

.item-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: opacity 0.2s ease;
}

.item-label.hidden {
  opacity: 0;
  width: 0;
  pointer-events: none;
}

.item-badge {
  background: var(--color-primary);
  color: white;
  font-size: 0.6875rem;
  font-weight: 700;
  padding: 0.125rem 0.4375rem;
  border-radius: var(--radius-full);
  min-width: 18px;
  text-align: center;
  flex-shrink: 0;
}
</style>
