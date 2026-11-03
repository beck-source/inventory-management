<template>
  <header class="topbar">
    <button
      type="button"
      class="icon-button menu-button"
      :aria-label="t('nav.openNavigation')"
      aria-controls="app-sidebar"
      :aria-expanded="String(mobileOpen)"
      @click="openMobile"
    >
      <AppIcon name="menu" />
    </button>

    <h1 class="topbar-title" :title="title">
      <slot name="title">{{ title }}</slot>
    </h1>

    <div class="topbar-actions">
      <slot name="actions" />
      <button
        type="button"
        class="icon-button"
        :aria-label="themeLabel"
        :title="themeLabel"
        @click="cycleTheme"
      >
        <AppIcon :name="themeIcon" />
      </button>
      <slot name="account" />
    </div>
  </header>
</template>

<script>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'
import { useSidebar } from '../composables/useSidebar'
import { useTheme } from '../composables/useTheme'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'AppTopbar',
  components: { AppIcon },
  props: {
    title: { type: String, default: '' }
  },
  setup() {
    const { mobileOpen, openMobile } = useSidebar()
    const { preference, cycleTheme } = useTheme()
    const { t } = useI18n()

    // The icon shows the current preference; the label says what a click does next.
    const themeIcon = computed(() => ({ system: 'monitor', light: 'sun', dark: 'moon' })[preference.value])
    const themeLabel = computed(() => {
      const next = { system: 'light', light: 'dark', dark: 'system' }[preference.value]
      return t('theme.toggle', {
        current: t(`theme.${preference.value}`),
        next: t(`theme.${next}`)
      })
    })

    return { t, mobileOpen, openMobile, cycleTheme, themeIcon, themeLabel }
  }
}
</script>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--content-padding);
  /* Translucent surface + blur so content scrolling under the bar stays readable. */
  background: color-mix(in srgb, var(--color-surface) 85%, transparent);
  backdrop-filter: saturate(180%) blur(8px);
  border-bottom: 1px solid var(--color-border);
}
.topbar-title {
  flex: 1;
  min-width: 0;
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.topbar-actions { display: flex; align-items: center; gap: var(--space-2); flex-shrink: 0; }

.icon-button {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease), color var(--duration-fast) var(--ease);
}
.icon-button:hover { background: var(--color-surface-hover); color: var(--color-text); }

/* The menu button only exists for the off-canvas drawer (< 1024px). */
.menu-button { display: none; margin-left: calc(var(--space-2) * -1); }
@media (max-width: 1023px) {
  .menu-button { display: inline-grid; }
  .topbar { padding: 0 var(--space-4); }
}
</style>
