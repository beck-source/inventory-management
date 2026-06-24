<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error && !allRecommendations.length" class="error">{{ error }}</div>
    <div v-else>

      <!-- Budget Card -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-body">
          <div class="budget-display">{{ formatCurrency(budget) }}</div>
          <input
            type="range"
            class="budget-slider"
            v-model.number="budget"
            :min="0"
            :max="budgetMax"
            :step="500"
          />
          <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
          <div class="stat-chips">
            <div class="stat-chip chip-blue">
              <span class="chip-label">{{ t('restocking.budgetLabel') }}</span>
              <span class="chip-value">{{ formatCurrency(budget) }}</span>
            </div>
            <div class="stat-chip" :class="totalCost > budget ? 'chip-red' : 'chip-green'">
              <span class="chip-label">{{ t('restocking.totalCost') }}</span>
              <span class="chip-value">{{ formatCurrency(totalCost) }}</span>
            </div>
            <div class="stat-chip" :class="remainingBudget <= 0 ? 'chip-red' : 'chip-green'">
              <span class="chip-label">{{ t('restocking.remainingBudget') }}</span>
              <span class="chip-value">{{ formatCurrency(remainingBudget) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Lead Time Strip -->
      <div class="lead-time-strip">
        {{ t('restocking.leadTimeNote') }}
      </div>

      <!-- Recommendations Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.selectedCount', { count: selectedItems.length }) }}
          </h3>
        </div>

        <div v-if="allRecommendations.length === 0" class="no-data">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table class="recommendations-table">
            <thead>
              <tr>
                <th class="col-check"></th>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-num">{{ t('restocking.table.onHand') }}</th>
                <th class="col-num">{{ t('restocking.table.forecasted') }}</th>
                <th class="col-num">{{ t('restocking.table.toRestock') }}</th>
                <th class="col-num">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-num">{{ t('restocking.table.estimatedCost') }}</th>
                <th class="col-trend">{{ t('restocking.table.trend') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in allRecommendations"
                :key="item.sku"
                :class="isSelected(item) ? 'selected-row' : 'unselected-row'"
              >
                <td class="col-check">
                  <span v-if="isSelected(item)" class="checkmark">&#10003;</span>
                </td>
                <td class="col-sku"><code>{{ item.sku }}</code></td>
                <td class="col-name">{{ item.item_name }}</td>
                <td class="col-num">{{ item.quantity_on_hand.toLocaleString() }}</td>
                <td class="col-num">{{ item.forecasted_demand.toLocaleString() }}</td>
                <td class="col-num"><strong>{{ item.quantity_to_restock.toLocaleString() }}</strong></td>
                <td class="col-num">{{ formatCurrency(item.unit_cost) }}</td>
                <td class="col-num"><strong>{{ formatCurrency(item.estimated_cost) }}</strong></td>
                <td class="col-trend">
                  <span :class="['trend-badge', `trend-${item.trend}`]">{{ item.trend }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Place Order -->
      <div class="place-order-section">
        <button
          class="place-order-btn"
          :disabled="selectedItems.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
        <p v-if="successMessage" class="success-msg">{{ successMessage }}</p>
        <p v-if="error" class="error-msg">{{ error }}</p>
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
    const { t } = useI18n()

    const allRecommendations = ref([])
    const budget = ref(10000)
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref(null)

    const budgetMax = computed(() =>
      Math.max(50000, Math.ceil(
        allRecommendations.value.reduce((s, i) => s + i.estimated_cost, 0) / 1000
      ) * 1000)
    )

    const selectedItems = computed(() => {
      let remaining = budget.value
      return allRecommendations.value.filter(item => {
        if (item.estimated_cost <= remaining) {
          remaining -= item.estimated_cost
          return true
        }
        return false
      })
    })

    const totalCost = computed(() =>
      selectedItems.value.reduce((s, i) => s + i.estimated_cost, 0)
    )

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const isSelected = (item) =>
      selectedItems.value.some(s => s.sku === item.sku)

    const formatCurrency = (value) =>
      value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        allRecommendations.value = await api.getRestockingRecommendations()
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      successMessage.value = null
      error.value = null
      try {
        await api.createOrder({
          items: selectedItems.value.map(i => ({
            sku: i.sku,
            name: i.item_name,
            quantity: i.quantity_to_restock,
            unit_price: i.unit_cost
          })),
          total_value: totalCost.value
        })
        successMessage.value = t('restocking.orderSuccess')
        budget.value = 10000
        await loadRecommendations()
      } catch (err) {
        error.value = t('restocking.orderError')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      allRecommendations,
      budget,
      budgetMax,
      loading,
      error,
      submitting,
      successMessage,
      selectedItems,
      totalCost,
      remainingBudget,
      isSelected,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 0;
}

.budget-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.budget-display {
  font-size: 2.5rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: -1px;
}

.budget-slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #334155;
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
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #1d4ed8;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #1d4ed8;
}

.budget-hint {
  font-size: 0.8rem;
  color: #64748b;
  margin: 0;
}

.stat-chips {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.stat-chip {
  flex: 1;
  min-width: 140px;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.chip-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.7;
}

.chip-value {
  font-size: 1.1rem;
  font-weight: 700;
}

.chip-blue  { background: #1e3a5f; color: #93c5fd; }
.chip-green { background: #14532d; color: #86efac; }
.chip-red   { background: #450a0a; color: #fca5a5; }

.lead-time-strip {
  background: #1e3a5f;
  color: #93c5fd;
  border: 1px solid #2563eb44;
  border-radius: 8px;
  padding: 0.65rem 1.25rem;
  font-size: 0.82rem;
  font-weight: 500;
  margin: 1rem 0;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.9rem;
}

.recommendations-table {
  width: 100%;
  table-layout: auto;
}

.col-check  { width: 36px; text-align: center; }
.col-sku    { width: 90px; }
.col-name   { min-width: 180px; }
.col-num    { width: 110px; text-align: right; }
.col-trend  { width: 110px; text-align: center; }

.checkmark {
  color: #10b981;
  font-size: 1rem;
  font-weight: 700;
}

.selected-row {
  background: rgba(16, 185, 129, 0.07);
  border-left: 3px solid #10b981;
}

.unselected-row {
  opacity: 0.55;
}

.trend-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  text-transform: capitalize;
}

.trend-increasing { background: #14532d; color: #86efac; }
.trend-stable     { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
.trend-decreasing { background: #450a0a; color: #fca5a5; }

.place-order-section {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.place-order-btn {
  width: 100%;
  padding: 0.875rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.success-msg {
  color: #22c55e;
  font-size: 0.88rem;
  font-weight: 500;
  text-align: center;
}

.error-msg {
  color: #ef4444;
  font-size: 0.88rem;
  text-align: center;
}

code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  color: #22d3ee;
}
</style>
