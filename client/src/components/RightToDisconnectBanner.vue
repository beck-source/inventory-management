<template>
  <Teleport to="body">
    <div v-if="showBanner" class="rtd-banner" role="banner">
      <div class="rtd-inner">
        <div class="rtd-left">
          <div class="rtd-time-block">
            <span class="rtd-time">{{ currentTimeStr }}</span>
            <span class="rtd-label">Outside Business Hours</span>
          </div>
          <div class="rtd-separator"></div>
          <div class="rtd-message">
            Under the EU Right to Disconnect framework, you are not obligated to work at this time.
          </div>
        </div>

        <div class="rtd-center">
          <div class="rtd-working-time">
            <div class="wt-header">
              <span class="wt-label">Working Time Directive</span>
              <span class="wt-value">38 / 48h</span>
            </div>
            <div class="wt-track">
              <div class="wt-fill" style="width: 79.2%"></div>
            </div>
          </div>
        </div>

        <div class="rtd-right">
          <button class="btn-acknowledge" @click="dismiss">I acknowledge my rights</button>
          <button class="btn-overtime" @click="logOvertime">Log Overtime</button>
        </div>
      </div>

      <Transition name="toast">
        <div v-if="showOvertimeToast" class="overtime-toast">
          Overtime logged. Your employer has been notified.
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const DISMISS_KEY = 'right_to_disconnect_dismissed'

function isOutsideHours(date) {
  const h = date.getHours()
  return h < 8 || h >= 18
}

function isDismissed() {
  const raw = sessionStorage.getItem(DISMISS_KEY)
  if (!raw) return false
  try {
    const ts = parseInt(raw, 10)
    const elapsed = Date.now() - ts
    return elapsed < 60 * 60 * 1000 // 1 hour
  } catch {
    return false
  }
}

export default {
  name: 'RightToDisconnectBanner',
  setup() {
    const now = ref(new Date())
    const showBanner = ref(false)
    const showOvertimeToast = ref(false)
    let interval = null

    const currentTimeStr = computed(() => {
      return now.value.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    })

    const checkAndUpdate = () => {
      now.value = new Date()
      showBanner.value = isOutsideHours(now.value) && !isDismissed()
    }

    const dismiss = () => {
      sessionStorage.setItem(DISMISS_KEY, String(Date.now()))
      showBanner.value = false
    }

    const logOvertime = () => {
      showOvertimeToast.value = true
      setTimeout(() => {
        showOvertimeToast.value = false
      }, 3500)
    }

    onMounted(() => {
      checkAndUpdate()
      interval = setInterval(checkAndUpdate, 60 * 1000)
    })

    onUnmounted(() => {
      if (interval) clearInterval(interval)
    })

    return { showBanner, currentTimeStr, showOvertimeToast, dismiss, logOvertime }
  }
}
</script>

<style scoped>
.rtd-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 8000;
  background: #78350f;
  border-bottom: 2px solid #d97706;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

.rtd-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.625rem 1.5rem;
  flex-wrap: wrap;
}

.rtd-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
  min-width: 280px;
}

.rtd-time-block {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.rtd-time {
  font-size: 1.125rem;
  font-weight: 800;
  color: #fef3c7;
  letter-spacing: 0.05em;
  line-height: 1.2;
}

.rtd-label {
  font-size: 0.625rem;
  font-weight: 700;
  color: #fcd34d;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.rtd-separator {
  width: 1px;
  height: 32px;
  background: rgba(253, 230, 138, 0.3);
  flex-shrink: 0;
}

.rtd-message {
  font-size: 0.8rem;
  color: #fef3c7;
  line-height: 1.4;
  flex: 1;
}

.rtd-center {
  flex-shrink: 0;
  min-width: 160px;
}

.rtd-working-time {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.wt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.wt-label {
  font-size: 0.688rem;
  font-weight: 600;
  color: #fcd34d;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.wt-value {
  font-size: 0.75rem;
  font-weight: 700;
  color: #fef3c7;
}

.wt-track {
  height: 6px;
  background: rgba(253, 230, 138, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.wt-fill {
  height: 100%;
  background: #fcd34d;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.rtd-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.btn-acknowledge {
  background: #d97706;
  color: white;
  border: none;
  padding: 0.375rem 0.875rem;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
  white-space: nowrap;
}

.btn-acknowledge:hover {
  background: #b45309;
}

.btn-overtime {
  background: transparent;
  color: #fcd34d;
  border: 1px solid rgba(253, 211, 77, 0.4);
  padding: 0.375rem 0.75rem;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  font-family: inherit;
  white-space: nowrap;
}

.btn-overtime:hover {
  background: rgba(253, 211, 77, 0.1);
  border-color: #fcd34d;
}

.overtime-toast {
  background: #065f46;
  color: #d1fae5;
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
  padding: 0.5rem 1rem;
  border-top: 1px solid #10b981;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s ease, max-height 0.3s ease;
  max-height: 48px;
  overflow: hidden;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
