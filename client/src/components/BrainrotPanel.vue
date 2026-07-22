<template>
  <div class="brainrot-panel">
    <div class="panel-bar">
      <span class="panel-title">⚡ Brainrot Mode</span>
      <button class="panel-exit" @click="$emit('close')" title="Exit Brainrot Mode">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="1" y1="1" x2="13" y2="13"/>
          <line x1="13" y1="1" x2="1" y2="13"/>
        </svg>
        <span>Exit</span>
      </button>
    </div>
    <div class="panel-content">
      <div class="video-slot">
        <iframe
          src="https://www.youtube.com/embed/eRXE8Aebp7s?autoplay=1&mute=1&loop=1&playlist=eRXE8Aebp7s&controls=0&disablekb=1&modestbranding=1&iv_load_policy=3"
          frameborder="0"
          allow="autoplay; encrypted-media"
          allowfullscreen
          class="video-iframe"
          style="pointer-events: none"
          title="Subway Surfers gameplay"
        ></iframe>
      </div>
      <div class="feed-slot">
        <AlertReader />
      </div>
      <div class="video-slot">
        <iframe
          src="https://www.youtube.com/embed/s600FYgI5-s?autoplay=1&mute=1&loop=1&playlist=s600FYgI5-s&controls=0&disablekb=1&modestbranding=1&iv_load_policy=3"
          frameborder="0"
          allow="autoplay; encrypted-media"
          allowfullscreen
          class="video-iframe"
          style="pointer-events: none"
          title="Minecraft gameplay"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script>
import AlertReader from './AlertReader.vue'

export default {
  name: 'BrainrotPanel',
  components: { AlertReader },
  emits: ['close']
}
</script>

<style scoped>
.brainrot-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: #020617;
  border-top: 2px solid #3b82f6;
  box-shadow: 0 -4px 24px rgba(59, 130, 246, 0.2);
}

.panel-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  height: 36px;
  flex-shrink: 0;
  background: #0a0f1e;
  border-bottom: 1px solid #1e293b;
}

.panel-title {
  font-size: 12px;
  font-weight: 600;
  color: #93c5fd;
  letter-spacing: 0.05em;
}

.panel-exit {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  height: 26px;
  background: transparent;
  border: 1px solid #1e293b;
  border-radius: 6px;
  color: #475569;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.panel-exit:hover {
  background: #1e293b;
  border-color: #3b82f6;
  color: #f1f5f9;
}

.panel-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 8px;
  padding: 8px;
  overflow: hidden;
}

.video-slot {
  width: 170px;
  flex-shrink: 0;
  align-self: stretch;
  overflow: hidden;
  border-radius: 8px;
  background: #000;
}

.video-iframe {
  width: 100%;
  height: 100%;
  display: block;
  border: none;
}

.feed-slot {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  border-radius: 8px;
}
</style>
