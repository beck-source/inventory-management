<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error && !recommendation" class="error">{{ error }}</div>
    <div v-else>
      <div class="budget-card card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
        </div>
        <div class="budget-controls">
          <div class="budget-display">
            <span class="budget-amount">{{ formatCurrency(budget, currentCurrency) }}</span>
          </div>
          <div class="slider-wrapper">
            <input
              type="range"
              :min="0"
              :max="maxBudget"
              :step="sliderStep"
              v-model.number="budget"
              class="budget-slider"
            />
            <div class="slider-labels">
              <span>{{ formatCurrency(0, currentCurrency) }}</span>
              <span>{{ formatCurrency(maxBudget, currentCurrency) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="recommendation" class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemCount', { count: recommendation.item_count }) }}</div>
          <div class="stat-value">{{ recommendation.item_count }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value stat-value--currency">{{ formatCurrency(recommendation.total_cost, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value stat-value--currency">{{ formatCurrency(Math.max(0, budget - recommendation.total_cost), currentCurrency) }}</div>
        </div>
      </div>

      <div
        v-if="recommendation && recommendation.skipped_no_inventory && recommendation.skipped_no_inventory.length > 0"
        class="skipped-notice"
      >
        {{ t('restocking.skippedNotice', { count: recommendation.skipped_no_inventory.length }) }}
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.recommendedItems') }}
            <span v-if="recommendation"> ({{ recommendation.item_count }})</span>
          </h3>
          <button
            class="btn-primary"
            :disabled="submitting || !recommendation || recommendation.items.length === 0"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="!recommendation || recommendation.items.length === 0" class="no-data">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="col-number">{{ t('restocking.table.gapQuantity') }}</th>
                <th class="col-number">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-number">{{ t('restocking.table.lineCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendation.items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td class="col-number">{{ item.quantity.toLocaleString() }}</td>
                <td class="col-number">{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
                <td class="col-number"><strong>{{ formatCurrency(item.line_cost, currentCurrency) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const router = useRouter()

    const loading = ref(true)
    const error = ref(null)
    const budget = ref(0)
    const recommendation = ref(null)
    const maxBudget = ref(0)
    const submitting = ref(false)

    // Debounce timer stored in closure
    let debounceTimer = null

    const sliderStep = computed(() => Math.max(1, Math.round(maxBudget.value / 100)))

    const loadRecommendations = async (budgetValue) => {
      error.value = null
      try {
        const resp = await api.getRestockingRecommendations(budgetValue)
        recommendation.value = resp
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
        console.error(err)
      }
    }

    watch(budget, (newBudget) => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations(newBudget)
      }, 300)
    })

    const placeOrder = async () => {
      if (!recommendation.value || recommendation.value.items.length === 0) return
      submitting.value = true
      error.value = null
      try {
        await api.createRestockingOrder({ items: recommendation.value.items })
        router.push('/orders')
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
        console.error(err)
        submitting.value = false
      }
    }

    onMounted(async () => {
      loading.value = true
      error.value = null
      try {
        const resp = await api.getRestockingRecommendations(Number.MAX_SAFE_INTEGER)
        maxBudget.value = resp.max_budget
        budget.value = resp.max_budget
        recommendation.value = resp
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    })

    return {
      t,
      currentCurrency,
      formatCurrency,
      loading,
      error,
      budget,
      recommendation,
      maxBudget,
      submitting,
      sliderStep,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.budget-display {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.slider-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
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
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: background 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #1d4ed8;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
}

.stat-value--currency {
  font-size: 1.5rem;
}

.skipped-notice {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.col-number {
  text-align: right;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.25rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
  white-space: nowrap;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
