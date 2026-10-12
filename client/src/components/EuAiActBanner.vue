<template>
  <div v-if="!dismissed" class="ai-act-banner">
    <div class="banner-main">
      <div class="banner-left">
        <span class="high-risk-badge">HIGH RISK</span>
        <span class="banner-text">
          AI-assisted {{ pageLabel }}.
          EU AI Act Art. 13 — Transparency &amp; Human Oversight required.
          All recommendations must be reviewed by a qualified human before action.
        </span>
      </div>
      <div class="banner-right">
        <button class="btn-view-log" @click="showLog = !showLog">
          {{ showLog ? 'Hide AI Log' : 'View AI Log' }}
        </button>
        <button class="btn-dismiss" @click="dismiss">Dismiss</button>
      </div>
    </div>

    <Transition name="expand">
      <div v-if="showLog" class="ai-log">
        <div class="table-container">
          <table class="log-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Decision</th>
                <th>Confidence</th>
                <th>Human Review</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in logEntries" :key="entry.id">
                <td class="log-timestamp">{{ entry.timestamp }}</td>
                <td>{{ entry.decision }}</td>
                <td>
                  <span class="confidence-badge" :class="entry.confidenceClass">{{ entry.confidence }}</span>
                </td>
                <td>
                  <span class="review-badge" :class="entry.reviewClass">{{ entry.review }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="log-note">
          Log retained for 10 years per EU AI Act Art. 12.
          System registration: EU-AI-{{ registrationId }}.
        </p>
      </div>
    </Transition>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'EuAiActBanner',
  props: {
    page: {
      type: String,
      default: 'demand-forecast'
    }
  },
  setup(props) {
    const dismissed = ref(false)
    const showLog = ref(false)
    const registrationId = ref('')

    const pageLabel = computed(() => {
      const labels = {
        'demand-forecast': 'Demand Forecast',
        'restocking': 'Restocking Planner'
      }
      return labels[props.page] || props.page
    })

    const logEntries = computed(() => {
      if (props.page === 'restocking') {
        return [
          { id: 1, timestamp: '2026-07-22 09:14', decision: 'Recommend restock SRV-301 (45 units)', confidence: '94%', confidenceClass: 'high', review: 'Pending', reviewClass: 'pending' },
          { id: 2, timestamp: '2026-07-22 08:55', decision: 'Flag PRN-102 as critical shortage', confidence: '88%', confidenceClass: 'high', review: 'Approved', reviewClass: 'approved' },
          { id: 3, timestamp: '2026-07-21 16:42', decision: 'Reduce order qty MOT-220 by 30%', confidence: '71%', confidenceClass: 'medium', review: 'Overridden', reviewClass: 'overridden' },
          { id: 4, timestamp: '2026-07-21 14:18', decision: 'Recommend supplier switch CBL-045', confidence: '63%', confidenceClass: 'medium', review: 'Pending', reviewClass: 'pending' }
        ]
      }
      return [
        { id: 1, timestamp: '2026-07-22 09:14', decision: 'Forecast +18% demand SRV-301 Q3', confidence: '94%', confidenceClass: 'high', review: 'Pending', reviewClass: 'pending' },
        { id: 2, timestamp: '2026-07-22 08:55', decision: 'Predict declining trend PRN-102', confidence: '82%', confidenceClass: 'high', review: 'Approved', reviewClass: 'approved' },
        { id: 3, timestamp: '2026-07-21 17:30', decision: 'Seasonal spike alert MOT-220', confidence: '75%', confidenceClass: 'medium', review: 'Approved', reviewClass: 'approved' },
        { id: 4, timestamp: '2026-07-21 11:05', decision: 'Anomaly detected CBL-045 orders', confidence: '61%', confidenceClass: 'medium', review: 'Overridden', reviewClass: 'overridden' }
      ]
    })

    const dismiss = () => {
      sessionStorage.setItem(`ai_act_dismissed_${props.page}`, '1')
      dismissed.value = true
    }

    onMounted(() => {
      dismissed.value = !!sessionStorage.getItem(`ai_act_dismissed_${props.page}`)
      registrationId.value = String(100000 + Math.floor(Math.random() * 900000))
    })

    return { dismissed, showLog, pageLabel, logEntries, registrationId, dismiss }
  }
}
</script>

<style scoped>
.ai-act-banner {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-left: 4px solid #dc2626;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  overflow: hidden;
}

.banner-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  flex-wrap: wrap;
}

.high-risk-badge {
  background: #dc2626;
  color: white;
  font-size: 0.688rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.banner-text {
  font-size: 0.813rem;
  color: #7c2d12;
  line-height: 1.5;
}

.banner-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.btn-view-log {
  background: white;
  color: #7c2d12;
  border: 1px solid #fed7aa;
  padding: 0.375rem 0.75rem;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
}

.btn-view-log:hover {
  background: #fff7ed;
}

.btn-dismiss {
  background: transparent;
  color: #9a3412;
  border: none;
  padding: 0.375rem 0.625rem;
  font-size: 0.75rem;
  cursor: pointer;
  font-family: inherit;
  transition: color 0.15s;
}

.btn-dismiss:hover {
  color: #7c2d12;
}

/* Log section */
.ai-log {
  border-top: 1px solid #fed7aa;
  padding: 1rem;
  background: #fffbf7;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.813rem;
}

.log-table thead {
  background: #fef3c7;
}

.log-table th {
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #92400e;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border: none;
}

.log-table td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid #fde68a;
  color: #1e293b;
}

.log-table tbody tr:hover {
  background: #fef9f0;
}

.log-timestamp {
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  color: #64748b;
  white-space: nowrap;
}

.confidence-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.confidence-badge.high {
  background: #d1fae5;
  color: #065f46;
}

.confidence-badge.medium {
  background: #fef3c7;
  color: #92400e;
}

.review-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.review-badge.pending {
  background: #dbeafe;
  color: #1e40af;
}

.review-badge.approved {
  background: #d1fae5;
  color: #065f46;
}

.review-badge.overridden {
  background: #fecaca;
  color: #991b1b;
}

.log-note {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #fde68a;
  font-style: italic;
}

/* Expand animation */
.expand-enter-active,
.expand-leave-active {
  transition: opacity 0.2s ease;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
}
</style>
