<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget Slider -->
    <div class="card budget-card">
      <div class="budget-header">
        <div>
          <h3 class="card-title">{{ t('restocking.budget.title') }}</h3>
          <p class="budget-subtitle">{{ t('restocking.budget.subtitle') }}</p>
        </div>
        <div class="budget-display">
          <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          <span class="budget-label">{{ t('restocking.budget.available') }}</span>
        </div>
      </div>
      <div class="slider-container">
        <span class="slider-min">{{ currencySymbol }}0</span>
        <input
          type="range"
          class="budget-slider"
          :min="0"
          :max="sliderMax"
          :step="500"
          v-model.number="budget"
        />
        <span class="slider-max">{{ currencySymbol }}{{ sliderMax.toLocaleString() }}</span>
      </div>
      <div class="budget-usage-bar">
        <div
          class="budget-used"
          :class="{ 'over-budget': selectedTotal > budget }"
          :style="{ width: Math.min((selectedTotal / budget) * 100, 100) + '%' }"
        ></div>
      </div>
      <div class="budget-meta">
        <span class="budget-used-label">
          {{ t('restocking.budget.used') }}:
          <strong :class="{ 'text-danger': selectedTotal > budget }">
            {{ currencySymbol }}{{ selectedTotal.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) }}
          </strong>
        </span>
        <span class="budget-remaining-label">
          {{ t('restocking.budget.remaining') }}:
          <strong :class="{ 'text-danger': remaining < 0 }">
            {{ currencySymbol }}{{ Math.abs(remaining).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) }}
            {{ remaining < 0 ? t('restocking.budget.over') : '' }}
          </strong>
        </span>
        <span class="budget-items-label">
          {{ selectedItems.length }} {{ t('restocking.budget.itemsSelected') }}
        </span>
      </div>
    </div>

    <!-- Success Banner -->
    <transition name="fade">
      <div v-if="orderSuccess" class="success-banner">
        <span class="success-icon">✓</span>
        <div>
          <strong>{{ t('restocking.order.successTitle') }}</strong>
          <span>{{ t('restocking.order.successMessage', { number: lastOrderNumber }) }}</span>
        </div>
        <button class="dismiss-btn" @click="orderSuccess = false">×</button>
      </div>
    </transition>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Summary KPI Strip -->
      <div class="kpi-strip">
        <div class="kpi-card kpi-critical">
          <div class="kpi-num">{{ criticalCount }}</div>
          <div class="kpi-lbl">{{ t('restocking.kpi.critical') }}</div>
        </div>
        <div class="kpi-card kpi-high">
          <div class="kpi-num">{{ highCount }}</div>
          <div class="kpi-lbl">{{ t('restocking.kpi.high') }}</div>
        </div>
        <div class="kpi-card kpi-medium">
          <div class="kpi-num">{{ mediumCount }}</div>
          <div class="kpi-lbl">{{ t('restocking.kpi.medium') }}</div>
        </div>
        <div class="kpi-card kpi-budget">
          <div class="kpi-num">{{ withinBudgetCount }}</div>
          <div class="kpi-lbl">{{ t('restocking.kpi.withinBudget') }}</div>
        </div>
      </div>

      <!-- Recommendations Table -->
      <div class="card table-card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.recommendations.title') }}
            <span class="count-badge">{{ recommendations.length }}</span>
          </h3>
          <div class="table-actions">
            <button class="btn-secondary" @click="autoSelectByBudget">
              {{ t('restocking.recommendations.autoSelect') }}
            </button>
            <button class="btn-secondary" @click="clearAll">
              {{ t('restocking.recommendations.clearAll') }}
            </button>
          </div>
        </div>

        <div class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="col-check">
                  <input type="checkbox" :checked="allSelected" @change="toggleAll" />
                </th>
                <th class="col-priority">{{ t('restocking.table.priority') }}</th>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-warehouse">{{ t('restocking.table.warehouse') }}</th>
                <th class="col-stock">{{ t('restocking.table.onHand') }}</th>
                <th class="col-stock">{{ t('restocking.table.reorderPoint') }}</th>
                <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                <th class="col-qty">{{ t('restocking.table.recommendedQty') }}</th>
                <th class="col-cost">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-total">{{ t('restocking.table.totalCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations"
                :key="item.sku"
                :class="['restock-row', { selected: isSelected(item.sku), 'over-budget-row': wouldExceedBudget(item) }]"
                @click="toggleItem(item)"
              >
                <td class="col-check" @click.stop>
                  <input
                    type="checkbox"
                    :checked="isSelected(item.sku)"
                    @change="toggleItem(item)"
                  />
                </td>
                <td class="col-priority">
                  <span :class="['priority-badge', 'priority-' + item.priority]">
                    {{ t('restocking.priority.' + item.priority) }}
                  </span>
                </td>
                <td class="col-sku"><strong>{{ item.sku }}</strong></td>
                <td class="col-name">{{ item.item_name }}</td>
                <td class="col-warehouse">{{ item.warehouse }}</td>
                <td class="col-stock">
                  <span :class="{ 'text-danger': item.quantity_on_hand <= item.reorder_point }">
                    {{ item.quantity_on_hand }}
                  </span>
                </td>
                <td class="col-stock text-muted">{{ item.reorder_point }}</td>
                <td class="col-trend">
                  <span :class="['trend-badge', 'trend-' + item.trend]">
                    {{ t('trends.' + item.trend) }}
                  </span>
                </td>
                <td class="col-qty">{{ item.recommended_quantity }}</td>
                <td class="col-cost">{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td class="col-total">
                  <strong>{{ currencySymbol }}{{ item.total_cost.toLocaleString() }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Place Order Button -->
      <div class="order-footer">
        <div class="order-summary-text">
          <template v-if="selectedItems.length > 0">
            {{ t('restocking.order.summaryText', {
              count: selectedItems.length,
              total: currencySymbol + selectedTotal.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })
            }) }}
          </template>
          <template v-else>
            {{ t('restocking.order.noItems') }}
          </template>
        </div>
        <button
          class="btn-place-order"
          :disabled="selectedItems.length === 0 || placing"
          @click="placeOrder"
        >
          <span v-if="placing" class="spinner"></span>
          {{ placing ? t('restocking.order.placing') : t('restocking.order.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const recommendations = ref([])
    const selectedSkus = ref(new Set())
    const budget = ref(10000)
    const sliderMax = ref(50000)
    const placing = ref(false)
    const orderSuccess = ref(false)
    const lastOrderNumber = ref('')

    // ── Counts ──────────────────────────────────────────────────────────────
    const criticalCount = computed(() => recommendations.value.filter(r => r.priority === 'critical').length)
    const highCount = computed(() => recommendations.value.filter(r => r.priority === 'high').length)
    const mediumCount = computed(() => recommendations.value.filter(r => r.priority === 'medium').length)
    const withinBudgetCount = computed(() => {
      let running = 0
      let count = 0
      for (const item of recommendations.value) {
        if (running + item.total_cost <= budget.value) {
          running += item.total_cost
          count++
        } else {
          break
        }
      }
      return count
    })

    // ── Selection helpers ────────────────────────────────────────────────────
    const isSelected = (sku) => selectedSkus.value.has(sku)

    const selectedItems = computed(() =>
      recommendations.value.filter(r => selectedSkus.value.has(r.sku))
    )

    const selectedTotal = computed(() =>
      selectedItems.value.reduce((sum, r) => sum + r.total_cost, 0)
    )

    const remaining = computed(() => budget.value - selectedTotal.value)

    const allSelected = computed(() =>
      recommendations.value.length > 0 &&
      recommendations.value.every(r => selectedSkus.value.has(r.sku))
    )

    const wouldExceedBudget = (item) => {
      if (isSelected(item.sku)) return false
      return selectedTotal.value + item.total_cost > budget.value
    }

    const toggleItem = (item) => {
      const updated = new Set(selectedSkus.value)
      if (updated.has(item.sku)) {
        updated.delete(item.sku)
      } else {
        updated.add(item.sku)
      }
      selectedSkus.value = updated
    }

    const toggleAll = () => {
      if (allSelected.value) {
        selectedSkus.value = new Set()
      } else {
        selectedSkus.value = new Set(recommendations.value.map(r => r.sku))
      }
    }

    // Auto-select highest-priority items that fit within budget (greedy)
    const autoSelectByBudget = () => {
      const selected = new Set()
      let running = 0
      for (const item of recommendations.value) {
        if (running + item.total_cost <= budget.value) {
          selected.add(item.sku)
          running += item.total_cost
        }
      }
      selectedSkus.value = selected
    }

    const clearAll = () => {
      selectedSkus.value = new Set()
    }

    // Re-run auto-select whenever budget changes (only if user hasn't manually tweaked)
    let userManuallyChanged = false
    watch(budget, () => {
      if (!userManuallyChanged) autoSelectByBudget()
    })
    watch(selectedSkus, () => {
      userManuallyChanged = true
    }, { deep: true })

    // ── Data loading ─────────────────────────────────────────────────────────
    const loadRecommendations = async () => {
      try {
        loading.value = true
        recommendations.value = await api.getRestockingRecommendations()
        // Determine a sensible slider max
        const totalCost = recommendations.value.reduce((s, r) => s + r.total_cost, 0)
        sliderMax.value = Math.max(50000, Math.ceil(totalCost / 10000) * 10000)
        // Initial auto-select
        userManuallyChanged = false
        autoSelectByBudget()
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // ── Place order ───────────────────────────────────────────────────────────
    const placeOrder = async () => {
      if (selectedItems.value.length === 0) return
      placing.value = true
      try {
        const items = selectedItems.value.map(r => ({
          sku: r.sku,
          item_name: r.item_name,
          quantity: r.recommended_quantity,
          unit_cost: r.unit_cost
        }))
        const result = await api.submitRestockingOrder(items)
        lastOrderNumber.value = result.order_number
        orderSuccess.value = true
        // Reset selection after placing
        clearAll()
        userManuallyChanged = false
        setTimeout(() => { orderSuccess.value = false }, 6000)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      currencySymbol,
      loading,
      error,
      recommendations,
      budget,
      sliderMax,
      placing,
      orderSuccess,
      lastOrderNumber,
      criticalCount,
      highCount,
      mediumCount,
      withinBudgetCount,
      isSelected,
      selectedItems,
      selectedTotal,
      remaining,
      allSelected,
      wouldExceedBudget,
      toggleItem,
      toggleAll,
      autoSelectByBudget,
      clearAll,
      placeOrder
    }
  }
}
</script>

<style scoped>
/* ── Budget card ─────────────────────────────────────────────────────────── */
.budget-card {
  margin-bottom: 1.5rem;
}
.budget-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.budget-subtitle {
  font-size: 0.82rem;
  color: #64748b;
  margin-top: 0.2rem;
}
.budget-display {
  text-align: right;
}
.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  display: block;
}
.budget-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* slider */
.slider-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.slider-min, .slider-max {
  font-size: 0.78rem;
  color: #64748b;
  white-space: nowrap;
  min-width: 60px;
}
.slider-max { text-align: right; }
.budget-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}
.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}
.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #fff;
}

/* usage bar */
.budget-usage-bar {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.65rem;
}
.budget-used {
  height: 100%;
  background: #22c55e;
  border-radius: 4px;
  transition: width 0.3s ease, background 0.3s ease;
}
.budget-used.over-budget { background: #ef4444; }

/* meta row */
.budget-meta {
  display: flex;
  gap: 1.5rem;
  font-size: 0.82rem;
  color: #64748b;
  flex-wrap: wrap;
}
.budget-meta strong { font-weight: 600; color: #0f172a; }
.text-danger { color: #ef4444 !important; }
.text-muted { color: #94a3b8; }

/* ── Success banner ─────────────────────────────────────────────────────── */
.success-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
  margin-bottom: 1.25rem;
}
.success-icon {
  font-size: 1.2rem;
  color: #22c55e;
  flex-shrink: 0;
}
.success-banner strong {
  display: block;
  font-weight: 600;
  color: #15803d;
  margin-bottom: 0.1rem;
}
.success-banner span { font-size: 0.83rem; color: #166534; }
.dismiss-btn {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.3rem;
  color: #166534;
  cursor: pointer;
  line-height: 1;
  padding: 0 0.2rem;
}

/* ── KPI strip ──────────────────────────────────────────────────────────── */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.kpi-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.2rem;
  text-align: center;
}
.kpi-num {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.2rem;
}
.kpi-lbl {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.kpi-critical .kpi-num { color: #dc2626; }
.kpi-high .kpi-num    { color: #f97316; }
.kpi-medium .kpi-num  { color: #eab308; }
.kpi-budget .kpi-num  { color: #3b82f6; }

/* ── Table card ─────────────────────────────────────────────────────────── */
.table-card .card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.count-badge {
  display: inline-block;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  padding: 0.05rem 0.5rem;
  margin-left: 0.4rem;
  vertical-align: middle;
}
.table-actions {
  display: flex;
  gap: 0.5rem;
}
.btn-secondary {
  font-size: 0.8rem;
  padding: 0.35rem 0.8rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fafc;
  color: #475569;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.15s;
}
.btn-secondary:hover { background: #e2e8f0; }

.restock-table {
  table-layout: fixed;
  width: 100%;
  font-size: 0.83rem;
  border-collapse: collapse;
}
.restock-table th, .restock-table td {
  padding: 0.55rem 0.7rem;
  text-align: left;
  vertical-align: middle;
}
.restock-table thead th {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}
.restock-table tbody tr {
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: background 0.1s;
}
.restock-table tbody tr:hover { background: #f8fafc; }
.restock-table tbody tr:last-child { border-bottom: none; }
.restock-table tbody tr.selected { background: #eff6ff; }
.restock-table tbody tr.over-budget-row { opacity: 0.5; }

.col-check    { width: 40px; }
.col-priority { width: 90px; }
.col-sku      { width: 110px; }
.col-name     { /* flex */ }
.col-warehouse{ width: 130px; }
.col-stock    { width: 80px; text-align: right; }
.col-trend    { width: 90px; }
.col-qty      { width: 80px; text-align: right; }
.col-cost     { width: 90px; text-align: right; }
.col-total    { width: 100px; text-align: right; }

/* Priority badges */
.priority-badge {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 700;
  border-radius: 4px;
  padding: 0.15rem 0.45rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.priority-critical { background: #fee2e2; color: #dc2626; }
.priority-high     { background: #ffedd5; color: #c2410c; }
.priority-medium   { background: #fef9c3; color: #854d0e; }

/* Trend badges */
.trend-badge {
  display: inline-block;
  font-size: 0.72rem;
  border-radius: 4px;
  padding: 0.12rem 0.4rem;
}
.trend-increasing { background: #dcfce7; color: #15803d; }
.trend-stable     { background: #f1f5f9; color: #475569; }
.trend-decreasing { background: #fee2e2; color: #b91c1c; }

/* ── Order footer ───────────────────────────────────────────────────────── */
.order-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1.5rem;
  padding: 1.1rem 1.4rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}
.order-summary-text {
  font-size: 0.9rem;
  color: #475569;
}
.btn-place-order {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}
.btn-place-order:hover:not(:disabled) { background: #2563eb; }
.btn-place-order:disabled { opacity: 0.5; cursor: not-allowed; }

/* spinner */
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* fade transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.35s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Responsive */
@media (max-width: 900px) {
  .kpi-strip { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .kpi-strip { grid-template-columns: repeat(2, 1fr); }
  .col-warehouse, .col-cost { display: none; }
}
</style>
