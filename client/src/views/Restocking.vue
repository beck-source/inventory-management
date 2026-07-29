<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-slider-row">
          <input type="range" min="0" max="50000" step="500" v-model.number="budget" />
          <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
        <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ items.length }})</h3>
        </div>
        <div v-if="items.length === 0" class="loading">{{ t('restocking.noRecommendations') }}</div>
        <div v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th></th>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.category') }}</th>
                  <th>{{ t('restocking.table.demandGap') }}</th>
                  <th>{{ t('restocking.table.quantity') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.subtotal') }}</th>
                  <th>{{ t('restocking.table.leadTime') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="line in items" :key="line.sku">
                  <td><input type="checkbox" v-model="line.included" /></td>
                  <td><strong>{{ line.sku }}</strong></td>
                  <td>{{ line.item_name }}</td>
                  <td>{{ line.category }}</td>
                  <td>+{{ line.demand_gap }}</td>
                  <td>
                    <input
                      type="number"
                      min="1"
                      class="qty-input"
                      v-model.number="line.quantity"
                      :disabled="!line.included"
                    />
                  </td>
                  <td>{{ currencySymbol }}{{ line.unit_cost }}</td>
                  <td><strong>{{ currencySymbol }}{{ lineSubtotal(line).toLocaleString() }}</strong></td>
                  <td>{{ line.lead_time_days }} {{ t('restocking.table.days') }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="order-summary">
            <div class="summary-row">
              <span>{{ t('restocking.runningTotal') }}</span>
              <strong>{{ currencySymbol }}{{ runningTotal.toLocaleString() }}</strong>
            </div>
            <div class="summary-row">
              <span>{{ t('restocking.budgetRemaining') }}</span>
              <strong>{{ currencySymbol }}{{ (budget - runningTotal).toLocaleString() }}</strong>
            </div>
            <p v-if="runningTotal > budget" class="over-budget">
              {{ t('restocking.overBudgetWarning') }}
            </p>
            <p v-if="successMessage" class="success-banner">{{ successMessage }}</p>
            <p v-if="submitError" class="error">{{ submitError }}</p>
            <button
              class="btn-primary"
              :disabled="submitting || selectedCount === 0"
              @click="placeOrder"
            >
              {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const budget = ref(10000)
    const items = ref([])
    const submitting = ref(false)
    const successMessage = ref(null)
    const submitError = ref(null)
    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockingRecommendations(budget.value)
        items.value = data.recommendations.map(rec => ({
          ...rec,
          included: rec.fits_budget,
          quantity: rec.recommended_quantity
        }))
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce so dragging the slider doesn't fire a request per pixel
    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 300)
    })

    const lineSubtotal = (line) => line.quantity * line.unit_cost

    const runningTotal = computed(() =>
      items.value.filter(l => l.included).reduce((sum, l) => sum + lineSubtotal(l), 0)
    )
    const selectedCount = computed(() => items.value.filter(l => l.included).length)

    const placeOrder = async () => {
      submitting.value = true
      successMessage.value = null
      submitError.value = null
      try {
        const payload = {
          budget: budget.value,
          items: items.value.filter(l => l.included).map(l => ({ sku: l.sku, quantity: l.quantity }))
        }
        const order = await api.createRestockingOrder(payload)
        successMessage.value = t('restocking.orderSuccess', { orderNumber: order.order_number })
        await loadRecommendations()
      } catch (err) {
        submitError.value = t('restocking.orderError') + ': ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t, loading, error, budget, items, submitting, successMessage, submitError,
      currencySymbol, lineSubtotal, runningTotal, selectedCount, placeOrder
    }
  }
}
</script>

<style scoped>
.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-slider-row input[type='range'] {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
}

.budget-slider-row input[type='range']::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
}

.budget-slider-row input[type='range']::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: none;
}

.budget-value {
  font-weight: 700;
  font-size: 1.25rem;
  color: #0f172a;
}

.budget-hint {
  color: #64748b;
  font-size: 0.813rem;
  margin-top: 0.5rem;
}

.qty-input {
  width: 70px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.order-summary {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
}

.over-budget {
  color: #dc2626;
  margin-top: 0.5rem;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 0.75rem;
  border-radius: 8px;
  margin: 0.75rem 0;
}
</style>
