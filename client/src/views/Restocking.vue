<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="candidates.length === 0">
      <div class="card empty-card">
        <p class="empty-text">{{ t('restocking.noItems') }}</p>
      </div>
    </div>
    <div v-else>
      <!-- Budget card -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget.label') }}</h3>
          <span class="lead-time-badge">{{ t('restocking.leadTime') }}</span>
        </div>

        <div class="slider-row">
          <input
            v-model.number="budget"
            type="range"
            :min="0"
            :max="maxBudget"
            :step="1000"
            class="budget-slider"
            aria-label="Budget slider"
          />
        </div>

        <div class="budget-pills">
          <div class="budget-pill">
            <span class="pill-label">{{ t('restocking.budget.label') }}</span>
            <span class="pill-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          </div>
          <div class="budget-pill allocated">
            <span class="pill-label">{{ t('restocking.budget.allocated') }}</span>
            <span class="pill-value">{{ currencySymbol }}{{ allocatedCost.toLocaleString() }}</span>
          </div>
          <div class="budget-pill remaining" :class="{ 'over-budget': remainingBudget < 0 }">
            <span class="pill-label">{{ t('restocking.budget.remaining') }}</span>
            <span class="pill-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <!-- Recommended items card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.items.title') }}
            <span class="item-count">({{ t('restocking.items.summary', { count: selectedCandidates.length }) }})</span>
          </h3>
        </div>

        <div v-if="budget === 0 || selectedCandidates.length === 0" class="empty-state">
          <p>{{ t('restocking.items.empty') }}</p>
        </div>
        <div v-else class="table-container">
          <table class="restocking-table">
            <thead>
              <tr>
                <th class="col-check"></th>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.name') }}</th>
                <th class="col-category">{{ t('restocking.table.category') }}</th>
                <th class="col-warehouse">{{ t('restocking.table.warehouse') }}</th>
                <th class="col-num">{{ t('restocking.table.onHand') }}</th>
                <th class="col-num">{{ t('restocking.table.reorderPoint') }}</th>
                <th class="col-num">{{ t('restocking.table.qtyToOrder') }}</th>
                <th class="col-cost">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-cost">{{ t('restocking.table.totalCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <!--
                Render ALL candidates so deselected rows stay visible and can be re-checked.
                selectedSkus drives :checked so unaffordable rows show unchecked correctly.
                Rows outside budget that the user hasn't explicitly touched get a dimmer style.
              -->
              <tr
                v-for="candidate in candidates"
                :key="candidate.sku"
                :class="{
                  'row-deselected': deselected.has(candidate.sku),
                  'row-unaffordable': !selectedSkus.has(candidate.sku) && !deselected.has(candidate.sku)
                }"
              >
                <td class="col-check">
                  <input
                    type="checkbox"
                    :checked="selectedSkus.has(candidate.sku)"
                    @change="toggleItem(candidate.sku)"
                    class="row-checkbox"
                    :aria-label="`Select ${candidate.name}`"
                  />
                </td>
                <td class="col-sku"><code class="sku-code">{{ candidate.sku }}</code></td>
                <td class="col-name"><strong>{{ candidate.name }}</strong></td>
                <td class="col-category">
                  <span class="badge info">{{ candidate.category }}</span>
                </td>
                <td class="col-warehouse">{{ candidate.warehouse }}</td>
                <td class="col-num">{{ candidate.quantity_on_hand }}</td>
                <td class="col-num">{{ candidate.reorder_point }}</td>
                <td class="col-num"><strong>{{ candidate.restock_quantity }}</strong></td>
                <td class="col-cost">{{ currencySymbol }}{{ candidate.unit_cost.toLocaleString() }}</td>
                <td class="col-cost"><strong>{{ currencySymbol }}{{ candidate.restock_cost.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="summary-row">
                <td colspan="7" class="summary-label">Total Selected ({{ selectedCandidates.length }} items)</td>
                <td class="col-num summary-qty">{{ totalRestockQty.toLocaleString() }}</td>
                <td></td>
                <td class="col-cost summary-total">{{ currencySymbol }}{{ allocatedCost.toLocaleString() }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- Place order section -->
      <div class="place-order-section">
        <div v-if="orderPlaced" class="success-banner">
          <div class="success-icon">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <circle cx="10" cy="10" r="10" fill="#059669" />
              <path d="M6 10l3 3 5-5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </div>
          <div class="success-text">
            <strong>{{ t('restocking.orderPlaced') }}</strong>
            <p>{{ t('restocking.success', { orderNumber: placedOrderNumber, date: placedDeliveryDate }) }}</p>
          </div>
        </div>
        <button
          v-else
          @click="placeOrder"
          :disabled="selectedCandidates.length === 0 || submitting"
          class="btn-place-order"
        >
          {{ submitting ? t('common.loading') : t('restocking.placeOrder') }}
        </button>
      </div>
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
    const { t, currentCurrency, currentLocale } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const candidates = ref([])
    const budget = ref(0)
    const deselected = ref(new Set())
    const submitting = ref(false)
    const orderPlaced = ref(false)
    const placedOrderNumber = ref('')
    const placedDeliveryDate = ref('')

    // Sum of all candidate restock costs, rounded up to nearest $10K, minimum $50K
    const maxBudget = computed(() => {
      const total = candidates.value.reduce((sum, c) => sum + c.restock_cost, 0)
      return Math.max(50000, Math.ceil(total / 10000) * 10000)
    })

    // Greedy selection: iterate candidates in urgency order, include each item if its
    // restock_cost fits within the remaining budget AND the user has not deselected it.
    const selectedCandidates = computed(() => {
      let remaining = budget.value
      return candidates.value.filter(c => {
        if (deselected.value.has(c.sku)) return false
        if (c.restock_cost <= remaining) {
          remaining -= c.restock_cost
          return true
        }
        return false
      })
    })

    const allocatedCost = computed(() =>
      selectedCandidates.value.reduce((sum, c) => sum + c.restock_cost, 0)
    )

    // Set of SKUs that are currently selected (within budget and not deselected).
    // Used to drive checkbox :checked and row styling without filtering the rendered rows.
    const selectedSkus = computed(() => new Set(selectedCandidates.value.map(c => c.sku)))

    const remainingBudget = computed(() => budget.value - allocatedCost.value)

    const totalRestockQty = computed(() =>
      selectedCandidates.value.reduce((sum, c) => sum + c.restock_quantity, 0)
    )

    const toggleItem = (sku) => {
      const next = new Set(deselected.value)
      if (next.has(sku)) {
        next.delete(sku)
      } else {
        next.add(sku)
      }
      // Replace the ref value so Vue detects the Set mutation
      deselected.value = next
    }

    const formatDate = (isoString) => {
      const date = new Date(isoString)
      if (isNaN(date.getTime())) return isoString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    // Return the most frequently occurring value of a given key in an array of objects.
    // Falls back to `fallback` when the array is empty.
    const mostCommon = (items, key, fallback) => {
      if (!items.length) return fallback
      const freq = {}
      for (const item of items) {
        const val = item[key] || fallback
        freq[val] = (freq[val] || 0) + 1
      }
      return Object.entries(freq).sort((a, b) => b[1] - a[1])[0][0]
    }

    const placeOrder = async () => {
      if (selectedCandidates.value.length === 0) return
      submitting.value = true
      error.value = null
      try {
        const orderNumber = 'RESTOCK-' + Date.now()
        const orderDate = new Date().toISOString()
        const expectedDelivery = new Date(Date.now() + 7 * 86400000).toISOString()

        const items = selectedCandidates.value.map(c => ({
          sku: c.sku,
          name: c.name,
          quantity: c.restock_quantity,
          unit_price: c.unit_cost
        }))

        const payload = {
          order_number: orderNumber,
          customer: 'Internal Restocking',
          items,
          status: 'Restocking',
          order_date: orderDate,
          expected_delivery: expectedDelivery,
          total_value: allocatedCost.value,
          warehouse: mostCommon(selectedCandidates.value, 'warehouse', 'All'),
          category: mostCommon(selectedCandidates.value, 'category', 'Mixed')
        }

        await api.createOrder(payload)

        placedOrderNumber.value = orderNumber
        placedDeliveryDate.value = formatDate(expectedDelivery)
        orderPlaced.value = true
      } catch (err) {
        error.value = 'Failed to place order: ' + (err.response?.data?.detail || err.message)
        console.error('Place order error:', err)
      } finally {
        submitting.value = false
      }
    }

    const loadCandidates = async () => {
      loading.value = true
      error.value = null
      try {
        candidates.value = await api.getRestockingCandidates()
        // Set budget to max so all candidates are auto-selected on load
        budget.value = maxBudget.value
      } catch (err) {
        error.value = 'Failed to load restocking candidates: ' + err.message
        console.error('Load candidates error:', err)
      } finally {
        loading.value = false
      }
    }

    onMounted(loadCandidates)

    return {
      t,
      currencySymbol,
      loading,
      error,
      candidates,
      budget,
      maxBudget,
      deselected,
      selectedCandidates,
      selectedSkus,
      allocatedCost,
      remainingBudget,
      totalRestockQty,
      toggleItem,
      submitting,
      orderPlaced,
      placedOrderNumber,
      placedDeliveryDate,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  /* Page-level wrapper — padding provided by .main-content in App.vue */
}

/* Empty state when no low-stock items exist */
.empty-card {
  text-align: center;
  padding: 3rem;
}

.empty-text {
  color: #64748b;
  font-size: 0.938rem;
}

/* Budget card */
.budget-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.lead-time-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: #ede9fe;
  color: #5b21b6;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.slider-row {
  padding: 0.75rem 0 1.25rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #7c3aed;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(124, 58, 237, 0.4);
  transition: box-shadow 0.2s;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 1px 8px rgba(124, 58, 237, 0.6);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #7c3aed;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(124, 58, 237, 0.4);
}

/* Budget stat pills */
.budget-pills {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.budget-pill {
  display: inline-flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.875rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  min-width: 160px;
}

.budget-pill.allocated {
  border-color: #c4b5fd;
  background: #faf5ff;
}

.budget-pill.remaining {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.budget-pill.remaining.over-budget {
  border-color: #fecaca;
  background: #fef2f2;
}

.budget-pill.remaining.over-budget .pill-value {
  color: #dc2626;
}

.pill-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.pill-value {
  font-size: 1.375rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-pill.allocated .pill-value {
  color: #7c3aed;
}

.budget-pill.remaining .pill-value {
  color: #059669;
}

/* Item count in card header */
.item-count {
  font-size: 0.938rem;
  font-weight: 400;
  color: #64748b;
  margin-left: 0.375rem;
}

/* Empty state inside items card */
.empty-state {
  padding: 2.5rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Restocking table */
.restocking-table {
  table-layout: fixed;
  width: 100%;
}

.col-check {
  width: 40px;
}

.col-sku {
  width: 120px;
}

.col-name {
  width: 200px;
}

.col-category {
  width: 130px;
}

.col-warehouse {
  width: 160px;
}

.col-num {
  width: 100px;
  text-align: right;
}

.col-cost {
  width: 110px;
  text-align: right;
}

.row-checkbox {
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: #7c3aed;
}

.sku-code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.813rem;
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  color: #475569;
}

.row-deselected td {
  opacity: 0.45;
  text-decoration: line-through;
}

/* Rows that don't fit within the current budget (not explicitly deselected by user) */
.row-unaffordable td {
  opacity: 0.5;
  color: #94a3b8;
}

/* Summary footer row */
.summary-row {
  border-top: 2px solid #e2e8f0;
  background: #f8fafc;
}

.summary-row td {
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
}

.summary-label {
  font-weight: 600;
  color: #475569;
}

.summary-qty {
  font-weight: 700;
  color: #0f172a;
  text-align: right;
}

.summary-total {
  font-weight: 700;
  color: #7c3aed;
  text-align: right;
  font-size: 0.938rem;
}

/* Place order section */
.place-order-section {
  margin-bottom: 1.5rem;
}

.btn-place-order {
  display: block;
  width: 100%;
  padding: 1rem 2rem;
  background: #7c3aed;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
  letter-spacing: 0.01em;
}

.btn-place-order:hover:not(:disabled) {
  background: #6d28d9;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.35);
}

.btn-place-order:disabled {
  background: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
  box-shadow: none;
}

/* Success banner */
.success-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
  padding: 1rem 1.25rem;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  border-radius: 10px;
}

.success-icon {
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.success-text strong {
  display: block;
  font-size: 0.938rem;
  color: #065f46;
  margin-bottom: 0.25rem;
}

.success-text p {
  font-size: 0.875rem;
  color: #047857;
  margin: 0;
}
</style>
