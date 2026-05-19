<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>

      <!-- Toast notifications -->
      <div v-if="successMessage" class="toast toast-success">
        <span>{{ successMessage }}</span>
        <button @click="goToOrders" class="toast-link">{{ t('restocking.viewInOrders') }} &rarr;</button>
      </div>
      <div v-if="errorMessage" class="toast toast-error">{{ errorMessage }}</div>

      <!-- Budget card -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetCard.title') }}</h3>
        </div>

        <p class="budget-help">{{ t('restocking.budgetCard.help') }}</p>

        <div class="budget-row">
          <div class="budget-figure">
            <span class="budget-amount">{{ formattedBudget }}</span>
            <span class="budget-ceiling">/ {{ formattedCeiling }}</span>
          </div>
          <input
            type="range"
            class="budget-slider"
            :min="0"
            :max="budgetCeiling"
            :step="50"
            v-model.number="budget"
            :disabled="!candidates.length"
            :style="{ '--pct': sliderPct }"
          />
        </div>

        <div class="budget-stats">
          <div class="budget-stat">
            <div class="stat-label">{{ t('restocking.budgetCard.selected') }}</div>
            <div class="stat-value">{{ formattedSelected }}</div>
          </div>
          <div class="budget-stat">
            <div class="stat-label">{{ t('restocking.budgetCard.itemsSelected', { count: selectedCount }) }}</div>
            <div class="stat-progress">
              <div class="stat-progress-bar" :style="{ width: utilizationPct + '%' }"></div>
            </div>
            <div class="stat-meta">{{ utilizationPct }}% {{ t('restocking.budgetCard.utilization') }}</div>
          </div>
        </div>
      </div>

      <!-- Recommendations table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.table.title') }}</h3>
          <button
            class="place-order-btn"
            :disabled="!selectedCount || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="!candidates.length" class="empty-state">
          {{ t('restocking.budgetCard.noCandidates') }}
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.currentStock') }}</th>
                <th>{{ t('restocking.table.reorderPoint') }}</th>
                <th>{{ t('restocking.table.trending') }}</th>
                <th>{{ t('restocking.table.qty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.subtotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in candidates"
                :key="row.sku"
                :class="{ 'row-skipped': !row.included }"
              >
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ translateProductName(row.name) }}</td>
                <td>{{ row.warehouse }}</td>
                <td>{{ row.quantity_on_hand }}</td>
                <td>{{ row.reorder_point }}</td>
                <td>
                  <span v-if="row.is_trending" class="badge increasing">
                    {{ t('restocking.trendingBadge') }}
                  </span>
                  <span v-else class="muted">&mdash;</span>
                </td>
                <td><strong>{{ row.restock_qty }}</strong></td>
                <td>{{ formatCurrency(row.unit_cost, currentCurrency) }}</td>
                <td>
                  <strong v-if="row.included">{{ formatCurrency(row.subtotal, currentCurrency) }}</strong>
                  <span v-else class="muted">
                    {{ formatCurrency(row.subtotal, currentCurrency) }}
                    <span class="skipped-label">({{ t('restocking.skippedLabel') }})</span>
                  </span>
                </td>
                <td>{{ t('orders.leadTimeDays', { days: row.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const router = useRouter()
    const { t, currentCurrency, translateProductName } = useI18n()
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref(null)
    const errorMessage = ref(null)

    const inventoryItems = ref([])
    const demandForecasts = ref([])
    const budget = ref(0)

    // ── helpers ──────────────────────────────────────────────────────────────

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      const d = new Date(dateString)
      if (isNaN(d.getTime())) return dateString
      return d.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    // ── data loading ─────────────────────────────────────────────────────────

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()

        const [invData, demandData] = await Promise.all([
          api.getInventory({ warehouse: filters.warehouse, category: filters.category }),
          api.getDemandForecasts()
        ])

        inventoryItems.value = invData
        demandForecasts.value = demandData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch([selectedLocation, selectedCategory], () => {
      loadData()
    })

    // ── computed: demand trend map ────────────────────────────────────────────

    const demandTrendBySku = computed(() => {
      const map = new Map()
      for (const forecast of demandForecasts.value) {
        map.set(forecast.item_sku, forecast.trend)
      }
      return map
    })

    // ── computed: candidates (items below reorder point) ─────────────────────

    const sortedCandidates = computed(() => {
      const raw = inventoryItems.value
        .filter(item => item.quantity_on_hand < item.reorder_point)
        .map(item => {
          const restock_qty = item.reorder_point - item.quantity_on_hand
          const subtotal = restock_qty * item.unit_cost
          const is_trending = demandTrendBySku.value.get(item.sku) === 'increasing'
          const shortfall_pct = (item.reorder_point - item.quantity_on_hand) / item.reorder_point
          return {
            ...item,
            restock_qty,
            subtotal,
            is_trending,
            shortfall_pct
          }
        })

      // Stable sort: trending desc, shortfall_pct desc, sku asc
      return raw.sort((a, b) => {
        if (b.is_trending !== a.is_trending) return b.is_trending ? 1 : -1
        if (b.shortfall_pct !== a.shortfall_pct) return b.shortfall_pct - a.shortfall_pct
        return a.sku.localeCompare(b.sku)
      })
    })

    // ── computed: budget ceiling ──────────────────────────────────────────────

    const budgetCeiling = computed(() => {
      const total = sortedCandidates.value.reduce((sum, item) => sum + item.subtotal, 0)
      if (total === 0) return 1000
      return Math.ceil(total / 100) * 100
    })

    // ── computed: selected items (greedy fit within budget) ───────────────────

    const candidates = computed(() => {
      let remaining = budget.value
      const result = []
      for (const item of sortedCandidates.value) {
        const fits = item.subtotal <= remaining
        result.push({ ...item, included: fits })
        if (fits) remaining -= item.subtotal
      }
      return result
    })

    const selectedItems = computed(() => candidates.value.filter(r => r.included))
    const selectedTotal = computed(() => selectedItems.value.reduce((sum, r) => sum + r.subtotal, 0))
    const selectedCount = computed(() => selectedItems.value.length)

    // ── computed: slider & display ────────────────────────────────────────────

    const sliderPct = computed(() => {
      if (!budgetCeiling.value) return 0
      return Math.round((budget.value / budgetCeiling.value) * 100)
    })

    const formattedBudget = computed(() => formatCurrency(budget.value, currentCurrency.value))
    const formattedCeiling = computed(() => formatCurrency(budgetCeiling.value, currentCurrency.value))
    const formattedSelected = computed(() => formatCurrency(selectedTotal.value, currentCurrency.value))

    const utilizationPct = computed(() => {
      if (!budget.value) return 0
      return Math.round((selectedTotal.value / budget.value) * 100)
    })

    // When candidates list changes (filter update), reset budget to ceiling
    watch(
      () => sortedCandidates.value.length,
      () => {
        budget.value = budgetCeiling.value
      }
    )

    // ── place order ───────────────────────────────────────────────────────────

    const placeOrder = async () => {
      if (!selectedItems.value.length) return
      submitting.value = true
      errorMessage.value = null
      try {
        const payload = {
          budget: budget.value,
          items: selectedItems.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.restock_qty,
            unit_cost: r.unit_cost,
            lead_time_days: r.lead_time_days
          }))
        }
        const created = await api.createSubmittedOrder(payload)
        successMessage.value = t('restocking.successToast', {
          orderNumber: created.order_number,
          expected: formatDate(created.expected_delivery)
        })
      } catch (err) {
        errorMessage.value = t('restocking.errorToast')
      } finally {
        submitting.value = false
      }
    }

    const goToOrders = () => router.push('/orders')

    onMounted(async () => {
      await loadData()
      // Set initial budget to ceiling after data loads
      budget.value = budgetCeiling.value
    })

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      loading,
      error,
      submitting,
      successMessage,
      errorMessage,
      budget,
      budgetCeiling,
      candidates,
      selectedItems,
      selectedTotal,
      selectedCount,
      sliderPct,
      formattedBudget,
      formattedCeiling,
      formattedSelected,
      utilizationPct,
      placeOrder,
      goToOrders
    }
  }
}
</script>

<style scoped>
.budget-help {
  color: #64748b;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.budget-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.budget-figure {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  min-width: 200px;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-ceiling {
  font-size: 1rem;
  color: #64748b;
  font-weight: 500;
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(
    to right,
    #2563eb 0%,
    #2563eb calc(var(--pct, 0) * 1%),
    #e2e8f0 calc(var(--pct, 0) * 1%),
    #e2e8f0 100%
  );
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #2563eb;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25);
}

.budget-slider::-moz-range-thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #2563eb;
  cursor: pointer;
}

.budget-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.budget-stats {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
}

.budget-stat .stat-label {
  color: #64748b;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.budget-stat .stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.stat-progress {
  height: 8px;
  background: #f1f5f9;
  border-radius: 999px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.stat-progress-bar {
  height: 100%;
  background: linear-gradient(to right, #2563eb, #3b82f6);
  transition: width 0.2s ease;
}

.stat-meta {
  color: #64748b;
  font-size: 0.813rem;
  margin-top: 0.375rem;
}

.place-order-btn {
  background: #0f172a;
  color: #fff;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.row-skipped td {
  opacity: 0.45;
}

.muted {
  color: #94a3b8;
}

.skipped-label {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-left: 0.25rem;
}

.toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.toast-success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
}

.toast-error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.toast-link {
  background: transparent;
  border: none;
  color: inherit;
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
}
</style>
