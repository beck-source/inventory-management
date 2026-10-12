<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!recommendations.length" class="empty-state">
      {{ t('restocking.noRecommendations') }}
    </div>

    <div v-else>
      <!-- Submission confirmation -->
      <div v-if="placedOrder" class="success-banner" role="status">
        <div class="success-mark" aria-hidden="true">
          <svg viewBox="0 0 20 20" width="20" height="20">
            <path d="M5 10.5l3.2 3.2L15 7" fill="none" stroke="currentColor"
              stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <div class="success-text">
          <div class="success-title">
            {{ t('restocking.successTitle', { orderNumber: placedOrder.order_number }) }}
          </div>
          <div class="success-body">
            {{ t('restocking.successBody', {
              count: placedOrder.item_count,
              total: currencySymbol + money0(placedOrder.total_value),
              lead: placedOrder.lead_time_days
            }) }}
          </div>
        </div>
        <div class="success-actions">
          <router-link to="/orders" class="btn btn-ghost">{{ t('restocking.viewInOrders') }}</router-link>
          <button class="btn btn-secondary" @click="placedOrder = null">
            {{ t('restocking.placeAnother') }}
          </button>
        </div>
      </div>

      <template v-if="!placedOrder">
      <!-- Budget control + capacity waterline (the hero) -->
      <div class="card budget-card">
        <div class="budget-head">
          <div class="budget-block">
            <div class="budget-label">{{ t('restocking.budgetLabel') }}</div>
            <div class="budget-value">{{ currencySymbol }}{{ money0(budget) }}</div>
            <div class="budget-hint">{{ t('restocking.budgetHint') }}</div>
          </div>
          <div class="full-order">
            <div class="full-order-label">{{ t('restocking.fullOrderCost') }}</div>
            <div class="full-order-value">{{ currencySymbol }}{{ money0(totalCost) }}</div>
            <div class="full-order-sub">{{ recommendations.length }} {{ t('common.items') }}</div>
          </div>
        </div>

        <input
          class="budget-slider"
          type="range"
          min="0"
          :max="maxBudget"
          step="1000"
          v-model.number="budget"
          :aria-label="t('restocking.budgetLabel')"
          :aria-valuetext="currencySymbol + money0(budget) + ' — ' + t('restocking.capacitySpent') + ' ' + currencySymbol + money0(spent)"
        />
        <div class="slider-scale">
          <span>{{ currencySymbol }}0</span>
          <span>{{ currencySymbol }}{{ money0(maxBudget) }}</span>
        </div>

        <!-- Segmented capacity bar: each included item is a tonal segment of the spend -->
        <div class="capacity">
          <div
            class="capacity-bar"
            role="img"
            :aria-label="t('restocking.capacitySpent') + ' ' + currencySymbol + money0(spent) + ', ' + t('restocking.capacityRemaining') + ' ' + currencySymbol + money0(remaining)"
          >
            <div
              v-for="(seg, i) in included"
              :key="seg.item_sku"
              class="capacity-seg"
              :class="{ alt: i % 2 === 1 }"
              :style="{ width: pct(seg.line_total, budget) + '%' }"
              :title="seg.item_name + ' · ' + currencySymbol + money0(seg.line_total)"
            ></div>
          </div>
          <div class="capacity-legend">
            <span class="cap-spent">
              <span class="dot" aria-hidden="true"></span>
              {{ t('restocking.capacitySpent') }} <strong>{{ currencySymbol }}{{ money0(spent) }}</strong>
            </span>
            <span class="cap-remaining">
              {{ t('restocking.capacityRemaining') }} <strong>{{ currencySymbol }}{{ money0(remaining) }}</strong>
            </span>
          </div>
        </div>
      </div>

      <!-- Summary metrics -->
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.stats.inOrder') }}</div>
          <div class="stat-value">{{ included.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.orderTotal') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ money0(spent) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.stats.budgetRemaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ money0(remaining) }}</div>
        </div>
        <div class="stat-card" :class="excluded.length ? 'warning' : ''">
          <div class="stat-label">{{ t('restocking.stats.excluded') }}</div>
          <div class="stat-value">{{ excluded.length }}</div>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.inOrder') }} ({{ included.length }})</h3>
        </div>

        <div v-if="!included.length" class="empty-selection">
          {{ t('restocking.emptySelection') }}
        </div>

        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="c-item">{{ t('restocking.table.item') }}</th>
                <th class="c-trend">{{ t('restocking.table.trend') }}</th>
                <th class="c-num">{{ t('restocking.table.gap') }}</th>
                <th class="c-num">{{ t('restocking.table.quantity') }}</th>
                <th class="c-num">{{ t('restocking.table.unitCost') }}</th>
                <th class="c-num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="c-lead">{{ t('restocking.table.leadTime') }}</th>
                <th class="c-share">{{ t('restocking.table.share') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in included" :key="item.item_sku">
                <td class="c-item">
                  <div class="item-name">{{ translateProductName(item.item_name) }}</div>
                  <div class="item-sku">{{ item.item_sku }}</div>
                </td>
                <td class="c-trend">
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="c-num gap-pos">+{{ item.demand_gap }}</td>
                <td class="c-num">{{ item.recommended_quantity.toLocaleString(localeTag) }}</td>
                <td class="c-num">{{ currencySymbol }}{{ money2(item.unit_cost) }}</td>
                <td class="c-num"><strong>{{ currencySymbol }}{{ money0(item.line_total) }}</strong></td>
                <td class="c-lead">{{ t('restocking.leadDays', { count: item.lead_time_days }) }}</td>
                <td class="c-share">
                  <div class="share-track">
                    <div class="share-fill" :style="{ width: pct(item.line_total, budget) + '%' }"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Waterline divider -->
        <div v-if="excluded.length" class="waterline">
          <span class="waterline-label">{{ t('restocking.waterline') }}</span>
        </div>

        <!-- Won't fit -->
        <div v-if="excluded.length" class="table-container excluded-zone">
          <table class="restock-table">
            <tbody>
              <tr v-for="item in excluded" :key="item.item_sku" class="excluded-row">
                <td class="c-item">
                  <div class="item-name">{{ translateProductName(item.item_name) }}</div>
                  <div class="item-sku">{{ item.item_sku }}</div>
                </td>
                <td class="c-trend">
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="c-num gap-pos">+{{ item.demand_gap }}</td>
                <td class="c-num">{{ item.recommended_quantity.toLocaleString(localeTag) }}</td>
                <td class="c-num">{{ currencySymbol }}{{ money2(item.unit_cost) }}</td>
                <td class="c-num"><strong>{{ currencySymbol }}{{ money0(item.line_total) }}</strong></td>
                <td class="c-lead">{{ t('restocking.leadDays', { count: item.lead_time_days }) }}</td>
                <td class="c-share over-tag">{{ t('restocking.overBudget') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Action bar -->
      <div class="action-bar">
        <div class="action-summary">
          <span class="as-count">{{ included.length }} {{ t('common.items') }}</span>
          <span class="as-sep">·</span>
          <span class="as-total">{{ currencySymbol }}{{ money0(spent) }}</span>
        </div>
        <div class="action-right">
          <span v-if="placeError" class="action-error">{{ placeError }}</span>
          <button
            class="btn btn-primary place-btn"
            :disabled="!included.length || placing"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
      </template>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const recommendations = ref([])
    const budget = ref(0)

    const placing = ref(false)
    const placeError = ref(null)
    const placedOrder = ref(null)

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))
    const localeTag = computed(() => (currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'))

    const money0 = (n) =>
      Number(n || 0).toLocaleString(localeTag.value, { maximumFractionDigits: 0 })
    const money2 = (n) =>
      Number(n || 0).toLocaleString(localeTag.value, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    const pct = (part, whole) => (whole > 0 ? Math.min(100, (part / whole) * 100) : 0)
    const round2 = (n) => Math.round(n * 100) / 100

    const totalCost = computed(() =>
      round2(recommendations.value.reduce((sum, r) => sum + r.line_total, 0))
    )

    const maxBudget = computed(() => {
      const t = totalCost.value
      return Math.max(1000, Math.ceil(t / 1000) * 1000)
    })

    // Greedy budget allocation by demand urgency. Recommendations arrive already
    // ranked by the server; we walk them in order and include each item that
    // still fits the remaining budget, leaving the rest below the waterline.
    const selection = computed(() => {
      let spent = 0
      const included = []
      const excluded = []
      for (const r of recommendations.value) {
        if (spent + r.line_total <= budget.value + 0.001) {
          spent = round2(spent + r.line_total)
          included.push(r)
        } else {
          excluded.push(r)
        }
      }
      return { included, excluded, spent, remaining: round2(budget.value - spent) }
    })

    const included = computed(() => selection.value.included)
    const excluded = computed(() => selection.value.excluded)
    const spent = computed(() => selection.value.spent)
    const remaining = computed(() => selection.value.remaining)

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendations.value = await api.getRestockRecommendations()
        // Default budget: a clean figure that funds most of the order but leaves
        // a clearly-too-expensive item below the waterline. Clamped to the max.
        budget.value = Math.min(45000, maxBudget.value)
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (!included.value.length || placing.value) return
      try {
        placing.value = true
        placeError.value = null
        const payload = {
          budget: budget.value,
          items: included.value.map((i) => ({
            item_sku: i.item_sku,
            item_name: i.item_name,
            quantity: i.recommended_quantity,
            unit_cost: i.unit_cost
          }))
        }
        placedOrder.value = await api.createRestockOrder(payload)
        if (typeof window !== 'undefined') {
          const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
          window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' })
        }
      } catch (err) {
        placeError.value = 'Failed to submit order: ' + (err.response?.data?.detail || err.message)
      } finally {
        placing.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      loading,
      error,
      recommendations,
      budget,
      placing,
      placeError,
      placedOrder,
      currencySymbol,
      localeTag,
      money0,
      money2,
      pct,
      totalCost,
      maxBudget,
      included,
      excluded,
      spent,
      remaining,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
/* ---- Budget hero ---- */
.budget-card {
  padding: 1.5rem;
}

.budget-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}

.budget-label,
.full-order-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
}

.budget-value {
  font-size: 2.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1.05;
  margin-top: 0.25rem;
  font-variant-numeric: tabular-nums;
}

.budget-hint {
  font-size: 0.813rem;
  color: #94a3b8;
  margin-top: 0.375rem;
}

.full-order {
  text-align: right;
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.full-order-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #334155;
  margin-top: 0.25rem;
  font-variant-numeric: tabular-nums;
}

.full-order-sub {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.125rem;
}

/* ---- Slider ---- */
.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
  margin: 0.5rem 0 0.25rem;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid #ffffff;
  box-shadow: 0 0 0 1px #2563eb;
  cursor: pointer;
  transition: transform 0.12s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.12);
}

.budget-slider::-moz-range-thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid #ffffff;
  box-shadow: 0 0 0 1px #2563eb;
  cursor: pointer;
}

.budget-slider:focus-visible {
  box-shadow: 0 0 0 2px #bfdbfe;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
  margin-bottom: 1.25rem;
}

/* ---- Capacity waterline bar (signature) ---- */
.capacity-bar {
  display: flex;
  width: 100%;
  height: 30px;
  border-radius: 8px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.capacity-seg {
  height: 100%;
  background: #2563eb;
  border-right: 1px solid rgba(255, 255, 255, 0.85);
  transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

.capacity-seg.alt {
  background: #3b82f6;
}

.capacity-seg:last-child {
  border-right: none;
}

.capacity-legend {
  display: flex;
  justify-content: space-between;
  margin-top: 0.625rem;
  font-size: 0.875rem;
  color: #64748b;
}

.capacity-legend strong {
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.cap-spent {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.cap-spent .dot {
  width: 9px;
  height: 9px;
  border-radius: 2px;
  background: #2563eb;
  display: inline-block;
}

/* ---- Recommendation tables ---- */
.restock-table {
  table-layout: fixed;
  width: 100%;
}

.restock-table th.c-num,
.restock-table td.c-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.c-item { width: 26%; }
.c-trend { width: 11%; }
.c-num { width: 11%; }
.c-lead { width: 9%; text-align: right; }
.c-share { width: 12%; }

.item-name {
  font-weight: 600;
  color: #0f172a;
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-sku {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.125rem;
}

.gap-pos {
  color: #059669;
  font-weight: 600;
}

.c-lead {
  color: #475569;
  font-variant-numeric: tabular-nums;
}

.share-track {
  height: 8px;
  width: 100%;
  border-radius: 999px;
  background: #f1f5f9;
  overflow: hidden;
}

.share-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 999px;
  transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ---- Waterline divider ---- */
.waterline {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 1.25rem 0 0.5rem;
}

.waterline::before,
.waterline::after {
  content: '';
  flex: 1;
  border-top: 1px dashed #cbd5e1;
}

.waterline-label {
  padding: 0 1rem;
  font-size: 0.688rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #94a3b8;
}

.excluded-zone {
  opacity: 0.6;
}

.excluded-row td {
  color: #94a3b8;
}

.excluded-row .item-name {
  color: #64748b;
  font-weight: 500;
}

.over-tag {
  text-align: right;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #b45309;
}

.empty-selection {
  padding: 2rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.938rem;
}

.empty-state {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* ---- Action bar ---- */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  position: sticky;
  bottom: 1rem;
}

.action-summary {
  font-size: 0.938rem;
  color: #64748b;
}

.action-summary .as-total {
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.action-summary .as-sep {
  margin: 0 0.5rem;
  color: #cbd5e1;
}

.action-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.action-error {
  font-size: 0.813rem;
  color: #991b1b;
}

/* ---- Buttons ---- */
.btn {
  font-family: inherit;
  font-size: 0.938rem;
  font-weight: 600;
  border-radius: 8px;
  padding: 0.625rem 1.25rem;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-primary:disabled {
  background: #cbd5e1;
  border-color: #cbd5e1;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #334155;
  border-color: #cbd5e1;
}

.btn-secondary:hover {
  border-color: #94a3b8;
  background: #f8fafc;
}

.btn-ghost {
  background: transparent;
  color: #2563eb;
  border-color: transparent;
}

.btn-ghost:hover {
  background: #eff6ff;
}

.place-btn {
  min-width: 150px;
  justify-content: center;
}

/* ---- Success banner ---- */
.success-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
}

.success-mark {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #059669;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-text {
  flex: 1;
}

.success-title {
  font-weight: 700;
  color: #065f46;
  font-size: 1rem;
}

.success-body {
  font-size: 0.875rem;
  color: #047857;
  margin-top: 0.125rem;
  font-variant-numeric: tabular-nums;
}

.success-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

@media (prefers-reduced-motion: reduce) {
  .capacity-seg,
  .share-fill,
  .budget-slider::-webkit-slider-thumb {
    transition: none;
  }
}

@media (max-width: 720px) {
  .budget-head { flex-direction: column; }
  .full-order { text-align: left; align-self: stretch; }
  .c-share, .c-lead { display: none; }
}
</style>
