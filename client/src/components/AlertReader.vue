<template>
  <div class="alert-reader">
    <!-- Header -->
    <div class="reader-header">
      <span class="reader-badge">LIVE</span>
      <span class="reader-title">Inventory Intel</span>
      <span class="reader-counter" v-if="alerts.length">{{ currentIndex + 1 }} / {{ alerts.length }}</span>
    </div>

    <!-- Main reading area -->
    <div class="reader-body" v-if="current">
      <!-- Severity + warehouse -->
      <div class="reader-meta">
        <span class="severity-badge" :class="current.severity">{{ current.severity.toUpperCase() }}</span>
        <span class="reader-warehouse">{{ current.warehouse }}</span>
        <span class="reader-sku">{{ current.sku }}</span>
      </div>

      <!-- The text being read, word by word highlighted -->
      <div class="reader-text">
        <span
          v-for="(word, i) in currentWords"
          :key="i"
          class="reader-word"
          :class="{ highlight: i === currentWordIndex }"
        >{{ word }} </span>
      </div>

      <!-- Progress bar (fills over the duration of the utterance) -->
      <div class="reader-progress">
        <div class="reader-progress-bar" :style="{ width: progress + '%' }"></div>
      </div>

      <!-- Up next -->
      <div class="reader-next" v-if="next">
        <span class="next-label">UP NEXT</span>
        <span class="next-text">{{ next.text.slice(0, 60) }}…</span>
      </div>
    </div>

    <div class="reader-loading" v-else>Loading alerts…</div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../api'

export default {
  name: 'AlertReader',
  setup() {
    const alerts = ref([])
    const currentIndex = ref(0)
    const currentWordIndex = ref(-1)
    const progress = ref(0)
    let utterance = null
    let progressTimer = null
    let startTime = 0
    let estimatedDuration = 0

    const current = computed(() => alerts.value[currentIndex.value] || null)
    const next = computed(() => alerts.value[currentIndex.value + 1] || alerts.value[0] || null)
    const currentWords = computed(() => current.value ? current.value.text.split(' ') : [])

    const buildAlerts = (inventory, orders) => {
      const result = []
      // Low-stock items: quantity_on_hand <= reorder_point
      const lowStock = inventory.filter(i => i.quantity_on_hand <= i.reorder_point)
      lowStock.slice(0, 6).forEach(item => {
        const sev = item.quantity_on_hand < 50 ? 'critical' : 'warning'
        result.push({
          sku: item.sku,
          warehouse: item.warehouse || 'HQ',
          severity: sev,
          text: `${sev === 'critical' ? 'Critical alert!' : 'Stock warning!'} ${item.name} is running low with only ${item.quantity_on_hand} units remaining in ${item.warehouse || 'the warehouse'}. Immediate restocking action required. SKU ${item.sku}.`
        })
      })
      // Backordered orders
      const backordered = orders.filter(o => o.status === 'backordered').slice(0, 3)
      backordered.forEach(order => {
        const firstItem = order.items?.[0]?.name || 'product'
        result.push({
          sku: order.order_number || order.id,
          warehouse: order.warehouse || 'HQ',
          severity: 'danger',
          text: `Order backlog alert! Order ${order.order_number || order.id} for ${firstItem} is backordered. Customer ${order.customer || 'unknown'} is waiting. Total value ${order.total_value ? '$' + Math.round(order.total_value).toLocaleString() : 'pending'}.`
        })
      })
      if (result.length === 0) {
        result.push({ sku: 'OK', warehouse: 'ALL', severity: 'info', text: 'All systems nominal. Inventory levels are healthy across all warehouses. No critical alerts at this time. Stay tuned for live updates.' })
      }
      return result
    }

    const speak = (text, wordCb, endCb) => {
      if (typeof window === 'undefined' || !window.speechSynthesis) return
      window.speechSynthesis.cancel()
      utterance = new window.SpeechSynthesisUtterance(text)
      utterance.rate = 1.1
      utterance.pitch = 1.0
      utterance.onboundary = (e) => {
        if (e.name === 'word') wordCb(e.charIndex)
      }
      utterance.onend = endCb
      window.speechSynthesis.speak(utterance)
    }

    const charIndexToWordIndex = (charIndex, words) => {
      let pos = 0
      for (let i = 0; i < words.length; i++) {
        if (charIndex <= pos + words[i].length) return i
        pos += words[i].length + 1
      }
      return words.length - 1
    }

    const startReading = () => {
      if (!current.value) return
      currentWordIndex.value = -1
      progress.value = 0
      clearInterval(progressTimer)
      const words = currentWords.value
      const approxMs = (current.value.text.length / 14) * 1000 // rough estimate
      estimatedDuration = approxMs
      startTime = Date.now()
      progressTimer = setInterval(() => {
        const elapsed = Date.now() - startTime
        progress.value = Math.min(100, (elapsed / estimatedDuration) * 100)
      }, 100)
      speak(
        current.value.text,
        (charIndex) => {
          currentWordIndex.value = charIndexToWordIndex(charIndex, words)
        },
        () => {
          clearInterval(progressTimer)
          progress.value = 100
          setTimeout(() => {
            currentWordIndex.value = -1
            currentIndex.value = (currentIndex.value + 1) % alerts.value.length
          }, 800)
        }
      )
    }

    watch(currentIndex, () => {
      setTimeout(startReading, 300)
    })

    onMounted(async () => {
      try {
        const [inventory, orders] = await Promise.all([
          api.getInventory({}),
          api.getOrders({})
        ])
        alerts.value = buildAlerts(inventory, orders)
        setTimeout(startReading, 500)
      } catch {
        alerts.value = [{ sku: 'ERR', warehouse: 'N/A', severity: 'info', text: 'Unable to load inventory data. Please check your connection and try again.' }]
        setTimeout(startReading, 500)
      }
    })

    onUnmounted(() => {
      if (typeof window !== 'undefined' && window.speechSynthesis) window.speechSynthesis.cancel()
      clearInterval(progressTimer)
    })

    return { alerts, currentIndex, currentWordIndex, progress, current, next, currentWords }
  }
}
</script>

<style scoped>
.alert-reader {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0a0f1e;
  border-radius: 8px;
  overflow: hidden;
  font-family: inherit;
}

.reader-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: #020617;
  border-bottom: 1px solid #1e293b;
  flex-shrink: 0;
}

.reader-badge {
  background: #ef4444;
  color: white;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.1em;
  animation: pulse-red 1.5s ease-in-out infinite;
}

@keyframes pulse-red {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.reader-title {
  font-size: 12px;
  font-weight: 700;
  color: #93c5fd;
  letter-spacing: 0.05em;
  flex: 1;
}

.reader-counter {
  font-size: 11px;
  color: #475569;
  font-variant-numeric: tabular-nums;
}

.reader-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 14px 16px 10px;
  gap: 10px;
  overflow: hidden;
}

.reader-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.severity-badge {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.08em;
}
.severity-badge.critical { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.4); }
.severity-badge.warning  { background: rgba(245,158,11,0.2); color: #fbbf24; border: 1px solid rgba(245,158,11,0.4); }
.severity-badge.danger   { background: rgba(168,85,247,0.2); color: #c084fc; border: 1px solid rgba(168,85,247,0.4); }
.severity-badge.info     { background: rgba(59,130,246,0.2); color: #60a5fa; border: 1px solid rgba(59,130,246,0.4); }

.reader-warehouse {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.reader-sku {
  font-size: 10px;
  color: #334155;
  font-family: monospace;
  background: #1e293b;
  padding: 1px 6px;
  border-radius: 4px;
}

.reader-text {
  flex: 1;
  font-size: 1.05rem;
  font-weight: 600;
  color: #cbd5e1;
  line-height: 1.6;
  overflow: hidden;
  overflow-wrap: break-word;
}

.reader-word {
  transition: color 0.05s, background 0.05s;
  border-radius: 3px;
  padding: 0 1px;
}

.reader-word.highlight {
  color: #f1f5f9;
  background: rgba(59, 130, 246, 0.35);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
}

.reader-progress {
  height: 3px;
  background: #1e293b;
  border-radius: 2px;
  overflow: hidden;
  flex-shrink: 0;
}

.reader-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 2px;
  transition: width 0.1s linear;
}

.reader-next {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #020617;
  border-radius: 6px;
  border: 1px solid #1e293b;
  flex-shrink: 0;
}

.next-label {
  font-size: 9px;
  font-weight: 800;
  color: #475569;
  letter-spacing: 0.1em;
  white-space: nowrap;
}

.next-text {
  font-size: 11px;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  font-size: 13px;
}
</style>
