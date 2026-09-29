<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Control -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetControl') }}</h3>
        </div>
        <div class="budget-slider-wrap">
          <label class="budget-label" for="budget-slider">
            {{ t('restocking.budgetAvailable', { amount: formatCurrency(budget) }) }}
          </label>
          <input
            id="budget-slider"
            v-model.number="budget"
            type="range"
            min="0"
            max="500000"
            step="1000"
            class="budget-slider"
            :style="{ '--fill': budgetFillPercent + '%' }"
          />
          <div class="budget-range-labels">
            <span>{{ formatCurrency(0) }}</span>
            <span>{{ formatCurrency(500000) }}</span>
          </div>
        </div>

        <div class="stats-grid budget-stats">
          <div class="stat-card info">
            <div class="stat-label">{{ t('restocking.totalBudget') }}</div>
            <div class="stat-value">{{ formatCurrency(budget) }}</div>
          </div>
          <div class="stat-card warning">
            <div class="stat-label">{{ t('restocking.allocated') }}</div>
            <div class="stat-value">{{ formatCurrency(allocatedCost) }}</div>
          </div>
          <div class="stat-card success">
            <div class="stat-label">{{ t('restocking.remaining') }}</div>
            <div class="stat-value">{{ formatCurrency(remainingBudget) }}</div>
          </div>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
        </div>

        <div v-if="!hasInventory || !hasForecasts" class="empty-state">
          {{ t('restocking.noDataAvailable') }}
        </div>
        <div v-else-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.budgetTooSmall') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.totalCost') }}</th>
                <th>{{ t('restocking.table.cumulativeCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ rec.name }}</td>
                <td>{{ rec.currentDemand }}</td>
                <td><strong>{{ rec.forecastedDemand }}</strong></td>
                <td>{{ formatCurrency(rec.unitCost) }}</td>
                <td>{{ rec.quantity }}</td>
                <td>{{ formatCurrency(rec.totalCost) }}</td>
                <td>{{ formatCurrency(rec.cumulativeCost) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Submission Form -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.placeOrderTitle') }}</h3>
        </div>

        <div class="submission-form">
          <label class="notes-label" for="restock-notes">{{ t('restocking.notesLabel') }}</label>
          <textarea
            id="restock-notes"
            v-model="notes"
            class="notes-input"
            rows="3"
            :placeholder="t('restocking.notesPlaceholder')"
          ></textarea>

          <div class="submission-actions">
            <button
              class="place-order-btn"
              :disabled="submitting || recommendations.length === 0"
              @click="placeOrder"
            >
              {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
            </button>
          </div>

          <div v-if="submitError" class="error">{{ submitError }}</div>
          <div v-if="submitSuccess" class="success-message">{{ t('restocking.orderPlacedSuccess') }}</div>
        </div>
      </div>

      <!-- Submitted Order -->
      <div v-if="submittedOrder" class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.submittedOrder') }}</h3>
        </div>
        <div class="submitted-order-details">
          <div class="detail-row">
            <span class="detail-label">{{ t('restocking.orderNumber') }}</span>
            <span class="detail-value"><strong>{{ submittedOrder.order_number }}</strong></span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('restocking.status') }}</span>
            <span class="badge warning">{{ t('restocking.processing') }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('restocking.expectedDelivery') }}</span>
            <span class="detail-value">{{ formatDate(submittedOrder.expected_delivery) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('restocking.totalValue') }}</span>
            <span class="detail-value"><strong>{{ formatCurrency(submittedOrder.total_value) }}</strong></span>
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
    const { t, currentCurrency, currentLocale } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)

    const inventoryItems = ref([])
    const demandForecasts = ref([])

    const budget = ref(250000)
    const notes = ref('')

    const submitting = ref(false)
    const submitError = ref(null)
    const submitSuccess = ref(false)
    const submittedOrder = ref(null)

    const hasInventory = computed(() => inventoryItems.value.length > 0)
    const hasForecasts = computed(() => demandForecasts.value.length > 0)

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        demandForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Recommendations: sorted by forecasted demand desc, greedily allocated against budget
    const recommendations = computed(() => {
      if (!hasInventory.value || !hasForecasts.value) return []

      const inventoryBySku = new Map(inventoryItems.value.map(item => [item.sku, item]))

      const sortedForecasts = [...demandForecasts.value].sort(
        (a, b) => b.forecasted_demand - a.forecasted_demand
      )

      const results = []
      let remaining = budget.value
      let cumulative = 0

      for (const forecast of sortedForecasts) {
        const invItem = inventoryBySku.get(forecast.item_sku)
        if (!invItem || !invItem.unit_cost || invItem.unit_cost <= 0) continue

        const unitCost = invItem.unit_cost
        const quantity = Math.floor(remaining / unitCost)

        if (quantity <= 0) continue

        const totalCost = quantity * unitCost
        cumulative += totalCost
        remaining -= totalCost

        results.push({
          sku: forecast.item_sku,
          name: forecast.item_name,
          currentDemand: forecast.current_demand,
          forecastedDemand: forecast.forecasted_demand,
          unitCost,
          quantity,
          totalCost,
          cumulativeCost: cumulative
        })
      }

      return results
    })

    const allocatedCost = computed(() => {
      return recommendations.value.reduce((sum, rec) => sum + rec.totalCost, 0)
    })

    const remainingBudget = computed(() => {
      return Math.max(budget.value - allocatedCost.value, 0)
    })

    const budgetFillPercent = computed(() => {
      return (budget.value / 500000) * 100
    })

    // Reset submission feedback when budget changes since recommendations shift
    watch(budget, () => {
      submitError.value = null
      submitSuccess.value = false
    })

    const formatCurrency = (value) => {
      const numeric = Number(value) || 0
      return `${currencySymbol.value}${Math.round(numeric).toLocaleString()}`
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return

      submitting.value = true
      submitError.value = null
      submitSuccess.value = false

      try {
        const selectedItems = recommendations.value.map(rec => ({
          sku: rec.sku,
          name: rec.name,
          quantity: rec.quantity,
          unit_cost: rec.unitCost,
          total_cost: rec.totalCost
        }))

        const order = await api.submitRestockingOrder({
          selected_items: selectedItems,
          total_budget: budget.value,
          notes: notes.value
        })

        submittedOrder.value = order
        submitSuccess.value = true
      } catch (err) {
        submitError.value = 'Failed to submit restocking order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      budget,
      notes,
      hasInventory,
      hasForecasts,
      recommendations,
      allocatedCost,
      remainingBudget,
      budgetFillPercent,
      submitting,
      submitError,
      submitSuccess,
      submittedOrder,
      formatCurrency,
      formatDate,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-slider-wrap {
  margin-bottom: 1.25rem;
}

.budget-label {
  display: block;
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.75rem;
}

.budget-slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  appearance: none;
  background: linear-gradient(to right, #2563eb 0%, #2563eb var(--fill, 50%), #e2e8f0 var(--fill, 50%), #e2e8f0 100%);
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  cursor: pointer;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.budget-stats {
  margin-bottom: 0;
}

.empty-state {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #64748b;
  font-size: 0.938rem;
}

.submission-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.notes-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
}

.notes-input {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.875rem;
  color: #334155;
  resize: vertical;
}

.notes-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.submission-actions {
  display: flex;
  justify-content: flex-end;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-message {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 0.5rem 0;
  font-size: 0.938rem;
}

.submitted-order-details {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.625rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
}

.detail-value {
  color: #0f172a;
  font-size: 0.938rem;
}
</style>
