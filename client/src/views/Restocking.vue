<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Card 1: Budget Control -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetControl') }}</h3>
          <span class="budget-display">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="budget-slider-container">
          <input
            type="range"
            v-model.number="budget"
            min="0"
            max="15000"
            step="100"
            class="budget-slider"
          />
          <div class="slider-labels">
            <span>$0</span>
            <span>$15,000</span>
          </div>
        </div>
        <div class="budget-summary">
          <div class="budget-stat">
            <span class="budget-stat-label">{{ t('restocking.allocated') }}</span>
            <span class="budget-stat-value allocated">{{ formatCurrency(runningTotal) }}</span>
          </div>
          <div class="budget-stat">
            <span class="budget-stat-label">{{ t('restocking.remaining') }}</span>
            <span class="budget-stat-value remaining">{{ formatCurrency(budgetRemaining) }}</span>
          </div>
          <div class="budget-stat">
            <span class="budget-stat-label">{{ t('restocking.itemsSelected') }}</span>
            <span class="budget-stat-value">{{ selectedItems.length }} / {{ recommendations.length }}</span>
          </div>
        </div>
      </div>

      <!-- Card 2: Recommendations Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.status') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-if="recommendations.length === 0"
              >
                <td colspan="7" style="text-align: center; color: #64748b; padding: 2rem;">
                  {{ t('restocking.noRecommendations') }}
                </td>
              </tr>
              <tr
                v-for="item in recommendations"
                :key="item.id"
                :class="{ 'row-excluded': !isSelected(item) }"
              >
                <td>
                  <span
                    class="badge"
                    :class="isSelected(item) ? 'success' : 'excluded'"
                  >
                    {{ isSelected(item) ? t('restocking.included') : t('restocking.excluded') }}
                  </span>
                </td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span class="badge" :class="item.trend">{{ item.trend }}</span>
                </td>
                <td>{{ item.demand_gap.toLocaleString() }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td>{{ formatCurrency(item.line_total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Card 3: Order Summary -->
      <div class="card order-summary-card">
        <!-- Success state -->
        <div v-if="submitSuccess" class="success-message">
          <div class="success-icon">&#10003;</div>
          <h3>{{ t('restocking.orderPlaced') }}</h3>
          <p>{{ t('restocking.orderPlacedDescription') }}</p>
          <button @click="resetForm" class="btn-secondary">{{ t('restocking.placeAnother') }}</button>
        </div>

        <!-- Normal state -->
        <div v-else>
          <div class="card-header">
            <h3 class="card-title">{{ t('restocking.orderSummary') }}</h3>
          </div>
          <div class="summary-content">
            <div class="total-value">{{ formatCurrency(runningTotal) }}</div>
            <div class="item-count">{{ selectedItems.length }} items</div>
            <p class="delivery-note">{{ t('restocking.deliveryNote') }}</p>
            <p v-if="submitError" class="submit-error">{{ submitError }}</p>
            <button
              @click="placeOrder"
              :disabled="!canSubmit"
              class="btn-primary"
            >
              {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
            </button>
          </div>
        </div>
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

    const loading = ref(true)
    const error = ref(null)
    const recommendations = ref([])
    const budget = ref(5000)
    const submitting = ref(false)
    const submitSuccess = ref(false)
    const submitError = ref(null)

    // Greedy knapsack: iterate priority-sorted recommendations and include
    // each item if its line_total fits within the remaining budget
    const selectedItems = computed(() => {
      let remaining = budget.value
      const selected = []
      for (const item of recommendations.value) {
        if (item.line_total <= remaining) {
          selected.push(item)
          remaining -= item.line_total
        }
      }
      return selected
    })

    const runningTotal = computed(() =>
      selectedItems.value.reduce((sum, item) => sum + item.line_total, 0)
    )

    const budgetRemaining = computed(() => budget.value - runningTotal.value)

    const canSubmit = computed(
      () => selectedItems.value.length > 0 && !submitting.value && !submitSuccess.value
    )

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockingRecommendations()
        recommendations.value = data
      } catch (err) {
        error.value = 'Failed to load restocking recommendations'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    // Returns true when item.id is present in the selectedItems set
    const isSelected = (item) => {
      return selectedItems.value.some(s => s.id === item.id)
    }

    const formatCurrency = (value) =>
      value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const payload = {
          items: selectedItems.value.map(item => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            quantity: item.demand_gap,
            unit_cost: item.unit_cost
          })),
          total_value: runningTotal.value
        }
        await api.createRestockingOrder(payload)
        submitSuccess.value = true
      } catch (err) {
        submitError.value = 'Failed to submit order. Please try again.'
      } finally {
        submitting.value = false
      }
    }

    const resetForm = () => {
      submitSuccess.value = false
      submitError.value = null
      loadRecommendations()
    }

    onMounted(() => loadRecommendations())

    return {
      t,
      loading,
      error,
      recommendations,
      budget,
      submitting,
      submitSuccess,
      submitError,
      selectedItems,
      runningTotal,
      budgetRemaining,
      canSubmit,
      isSelected,
      formatCurrency,
      placeOrder,
      resetForm
    }
  }
}
</script>

<style scoped>
.restocking {
  /* view wrapper — padding supplied by .main-content in App.vue */
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider-container {
  padding: 1rem 0;
}

.budget-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid white;
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.budget-summary {
  display: flex;
  gap: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 1rem;
}

.budget-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.budget-stat-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-stat-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-stat-value.allocated {
  color: #2563eb;
}

.budget-stat-value.remaining {
  color: #16a34a;
}

.row-excluded {
  opacity: 0.45;
}

.badge.excluded {
  background: #f1f5f9;
  color: #64748b;
}

.order-summary-card .summary-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  text-align: center;
  gap: 0.75rem;
}

.total-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
}

.item-count {
  font-size: 0.875rem;
  color: #64748b;
}

.delivery-note {
  font-size: 0.813rem;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0.5rem 1rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 2.5rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #334155;
  border: 1px solid #e2e8f0;
  padding: 0.625rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

.submit-error {
  color: #dc2626;
  font-size: 0.813rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 0.5rem 1rem;
}

.success-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2.5rem;
  text-align: center;
  gap: 0.75rem;
}

.success-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #d1fae5;
  color: #059669;
  font-size: 1.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-message h3 {
  font-size: 1.25rem;
  color: #0f172a;
}

.success-message p {
  color: #64748b;
  max-width: 28rem;
}
</style>
