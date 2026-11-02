<template>
  <router-link :to="to" class="nav-item" :class="{ active: isActive }">
    <span class="nav-accent" v-if="isActive" />
    <span class="nav-label">{{ label }}</span>
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
  }
})

const route = useRoute()
const isActive = computed(() => route.path === props.to)
</script>

<style scoped>
.nav-item {
  display: flex;
  align-items: center;
  position: relative;
  padding: var(--sp-3) var(--sp-6);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-muted);
  transition: color 0.15s ease, background 0.15s ease;
  line-height: 1.5;
}

.nav-item:hover {
  color: var(--ink-inverse);
  background: rgba(255, 255, 255, 0.04);
}

.nav-item.active {
  color: var(--surface-bg);
}

.nav-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent);
  border-radius: 0 var(--r-sm) var(--r-sm) 0;
}

.nav-label {
  flex: 1;
}
</style>
