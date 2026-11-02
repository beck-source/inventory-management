<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <slot name="brand" />
    </div>
    <nav class="sidebar-nav">
      <slot name="nav" />
    </nav>
    <div class="sidebar-footer">
      <slot name="footer" />
    </div>
  </aside>
</template>

<script setup>
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 240px;
  height: 100vh;
  background: var(--surface-nav);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

.sidebar-brand {
  padding: var(--sp-6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.sidebar-nav {
  flex: 1;
  padding: var(--sp-2) 0;
  overflow-y: auto;
}

.sidebar-footer {
  padding: var(--sp-3) var(--sp-4);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}
</style>
