<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-body">
        <div class="budget-readout">{{ formatCurrency(budget, currentCurrency) }}</div>
        <input
          type="range"
          class="budget-slider"
          min="0"
          max="10000"
          step="500"
          v-model.number="budget"
        />
        <div class="budget-summary">
          <div class="summary-chip">
            <span class="chip-label">{{ t('restocking.budget') }}</span>
            <span class="chip-value">{{ formatCurrency(recommendation.budget, currentCurrency) }}</span>
          </div>
          <div class="summary-chip">
            <span class="chip-label">{{ t('restocking.spent') }}</span>
            <span class="chip-value">{{ formatCurrency(recommendation.spent, currentCurrency) }}</span>
          </div>
          <div class="summary-chip">
            <span class="chip-label">{{ t('restocking.remaining') }}</span>
            <span class="chip-value">{{ formatCurrency(recommendation.remaining, currentCurrency) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          {{ t('restocking.recommendations') }} ({{ recommendation.items.length }})
        </h3>
      </div>
      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="recommendation.items.length === 0" class="empty-state">
        {{ t('restocking.emptyState') }}
      </div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.item') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th>{{ t('restocking.table.quantity') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.lineTotal') }}</th>
              <th>{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendation.items" :key="item.item_sku">
              <td><strong>{{ item.item_sku }}</strong></td>
              <td>{{ item.item_name }}</td>
              <td>
                <span :class="['badge', item.trend]">
                  {{ t(`trends.${item.trend}`) }}
                </span>
              </td>
              <td>{{ item.quantity }}</td>
              <td>{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
              <td><strong>{{ formatCurrency(item.line_total, currentCurrency) }}</strong></td>
              <td>{{ item.lead_time_days }} {{ t('restocking.days') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="card-footer">
        <button
          class="place-order-btn"
          :disabled="recommendation.items.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>

    <div v-if="lastOrder" class="confirmation-strip">
      <span class="confirmation-text">
        {{ t('restocking.orderPlaced', { orderNumber: lastOrder.order_number }) }}
      </span>
      <router-link to="/orders" class="confirmation-link">
        {{ t('restocking.viewInOrders') }}
      </router-link>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const budget = ref(5000)
    const recommendation = ref({ budget: 0, spent: 0, remaining: 0, items: [] })
    const loading = ref(true)
    const submitting = ref(false)
    const error = ref(null)
    const lastOrder = ref(null)

    let debounceTimer = null

    const loadRecommendation = async () => {
      try {
        loading.value = true
        error.value = null
        recommendation.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      try {
        submitting.value = true
        error.value = null
        const result = await api.createRestockingOrder({ budget: budget.value })
        lastOrder.value = result
        await loadRecommendation()
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    watch(budget, () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendation()
      }, 200)
    })

    onMounted(loadRecommendation)

    return {
      t,
      currentCurrency,
      budget,
      recommendation,
      loading,
      submitting,
      error,
      lastOrder,
      placeOrder,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-body {
  padding: 1.5rem;
}

.budget-readout {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 1rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  accent-color: #0f172a;
  cursor: pointer;
  margin-bottom: 1.5rem;
}

.budget-slider::-webkit-slider-runnable-track {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
}

.budget-slider::-moz-range-track {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
}

.budget-summary {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.summary-chip {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  flex: 1;
  min-width: 140px;
}

.chip-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chip-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.confirmation-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1.5rem;
  padding: 1rem 1.25rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-left: 4px solid #10b981;
  border-radius: 8px;
}

.confirmation-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #065f46;
}

.confirmation-link {
  font-size: 0.875rem;
  font-weight: 600;
  color: #059669;
  text-decoration: none;
}

.confirmation-link:hover {
  text-decoration: underline;
}
</style>
