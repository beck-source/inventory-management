<template>
  <div class="brainrot-bar">
    <div class="brainrot-runner" aria-hidden="true">
      <span class="runner-emoji">🏃</span>
    </div>

    <div class="ticker-viewport">
      <div class="ticker-track" :style="tickerStyle">
        <span
          v-for="(event, index) in doubledEvents"
          :key="index"
          class="ticker-event"
          :class="event.type"
        >
          <span class="event-icon">{{ event.icon }}</span>
          {{ event.text }}
          <span class="ticker-sep">|</span>
        </span>
      </div>
    </div>

    <button class="brainrot-close" @click="$emit('close')" title="Disable Brainrot Mode">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <line x1="1" y1="1" x2="11" y2="11"/>
        <line x1="11" y1="1" x2="1" y2="11"/>
      </svg>
    </button>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'BrainrotTicker',
  emits: ['close'],
  setup() {
    const events = ref([])
    const tickerDuration = ref(40)

    const doubledEvents = computed(() => {
      // Duplicate so the scroll loops seamlessly
      return [...events.value, ...events.value]
    })

    const tickerStyle = computed(() => ({
      animationDuration: `${tickerDuration.value}s`
    }))

    const buildEvents = (inventory, orders) => {
      const items = []

      // Low-stock items (qty < 100)
      const lowStock = inventory
        .filter(item => item.quantity < 100)
        .slice(0, 5)
      lowStock.forEach(item => {
        items.push({
          type: 'warning',
          icon: '⚠',
          text: `Low Stock: ${item.name} (${item.quantity} units)`
        })
      })

      // Restock items (qty >= 100 but listed under reorder_point)
      const needsRestock = inventory
        .filter(item => item.quantity < item.reorder_point)
        .slice(0, 4)
      needsRestock.forEach(item => {
        items.push({
          type: 'info',
          icon: '↑',
          text: `Restock Alert: ${item.sku} — ${item.name}`
        })
      })

      // Delivered orders
      const delivered = orders
        .filter(o => o.status === 'delivered')
        .slice(0, 4)
      delivered.forEach(order => {
        items.push({
          type: 'success',
          icon: '✓',
          text: `Delivered: ${order.id}`
        })
      })

      // Shipped orders
      const shipped = orders
        .filter(o => o.status === 'shipped')
        .slice(0, 3)
      shipped.forEach(order => {
        items.push({
          type: 'success',
          icon: '→',
          text: `Shipped: ${order.id}`
        })
      })

      // Backordered orders
      const backordered = orders
        .filter(o => o.status === 'backordered')
        .slice(0, 3)
      backordered.forEach(order => {
        items.push({
          type: 'danger',
          icon: '✗',
          text: `Backordered: ${order.id}`
        })
      })

      // Revenue snippet
      const totalRevenue = orders
        .filter(o => typeof o.total === 'number')
        .reduce((sum, o) => sum + o.total, 0)
      if (totalRevenue > 0) {
        items.push({
          type: 'neutral',
          icon: '$',
          text: `Total Revenue: ${totalRevenue.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}`
        })
      }

      // Shuffle slightly to vary order
      items.sort(() => Math.random() - 0.5)

      // Scale animation duration based on number of events
      tickerDuration.value = Math.max(25, items.length * 3)

      return items
    }

    onMounted(async () => {
      try {
        const [inventory, orders] = await Promise.all([
          api.getInventory({}),
          api.getOrders({})
        ])
        events.value = buildEvents(inventory, orders)
      } catch (err) {
        // Fallback static events if API fails
        events.value = [
          { type: 'warning', icon: '⚠', text: 'Low Stock: Micro Servo Motor (45 units)' },
          { type: 'success', icon: '✓', text: 'Delivered: ORD-2025-0012' },
          { type: 'info', icon: '↑', text: 'Restock Alert: MTR-304' },
          { type: 'danger', icon: '✗', text: 'Backordered: ORD-2025-0047' },
          { type: 'neutral', icon: '$', text: 'Revenue Today: $48,320' }
        ]
        console.error('BrainrotTicker: failed to load events', err)
      }
    })

    return {
      events,
      doubledEvents,
      tickerStyle
    }
  }
}
</script>

<style scoped>
.brainrot-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 44px;
  background: #0f172a;
  border-top: 2px solid #3b82f6;
  display: flex;
  align-items: center;
  gap: 0;
  z-index: 9999;
  overflow: hidden;
  box-shadow: 0 -4px 20px rgba(59, 130, 246, 0.15);
}

/* ─── Runner ──────────────────────────────────────────── */
.brainrot-runner {
  flex-shrink: 0;
  width: 40px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f172a;
  border-right: 1px solid #1e3a5f;
  position: relative;
  z-index: 1;
}

.runner-emoji {
  font-size: 18px;
  display: inline-block;
  animation: runner-bob 0.5s steps(2, end) infinite;
  transform-origin: bottom center;
}

@keyframes runner-bob {
  0%   { transform: translateY(0px) scaleX(1); }
  50%  { transform: translateY(-3px) scaleX(1); }
  100% { transform: translateY(0px) scaleX(1); }
}

/* ─── Ticker ──────────────────────────────────────────── */
.ticker-viewport {
  flex: 1;
  overflow: hidden;
  height: 100%;
  display: flex;
  align-items: center;
  mask-image: linear-gradient(to right, transparent 0%, black 3%, black 97%, transparent 100%);
  -webkit-mask-image: linear-gradient(to right, transparent 0%, black 3%, black 97%, transparent 100%);
}

.ticker-track {
  display: flex;
  align-items: center;
  white-space: nowrap;
  animation: ticker-scroll linear infinite;
  will-change: transform;
}

@keyframes ticker-scroll {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.ticker-event {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: 'Menlo', 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 12px;
  color: #94a3b8;
  padding: 0 4px;
}

.ticker-event.warning { color: #fbbf24; }
.ticker-event.success { color: #34d399; }
.ticker-event.danger  { color: #f87171; }
.ticker-event.info    { color: #60a5fa; }
.ticker-event.neutral { color: #a78bfa; }

.event-icon {
  opacity: 0.85;
  font-style: normal;
}

.ticker-sep {
  margin-left: 12px;
  margin-right: 4px;
  color: #1e3a5f;
  font-size: 14px;
}

/* ─── Close button ────────────────────────────────────── */
.brainrot-close {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  margin-right: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  color: #4b5563;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.brainrot-close:hover {
  background: #1e293b;
  border-color: #3b82f6;
  color: #f1f5f9;
}

/* ─── Mobile ──────────────────────────────────────────── */
@media (max-width: 640px) {
  .ticker-event {
    font-size: 10px;
  }
}
</style>
