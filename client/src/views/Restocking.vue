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
        <div class="budget-slider-section">
          <div class="budget-value">{{ currencySymbol }}{{ Math.round(budget).toLocaleString() }}</div>
          <input
            type="range"
            min="0"
            :max="sliderMax"
            step="1"
            v-model.number="budget"
            @input="onBudgetInput"
            class="budget-slider"
          />
          <div class="budget-range-labels">
            <span>{{ currencySymbol }}0</span>
            <span>{{ currencySymbol }}{{ Math.round(budgetMax).toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }}</h3>
        </div>

        <div v-if="recommendedItems.length === 0" class="no-items">
          {{ t('restocking.noItems') }}
        </div>
        <div v-else>
          <p class="select-hint">{{ t('restocking.selectItems') }}</p>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th class="col-check"></th>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.quantity') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.lineTotal') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendedItems" :key="item.sku">
                  <td class="col-check">
                    <input
                      type="checkbox"
                      :checked="checkedSkus.has(item.sku)"
                      @change="toggleChecked(item.sku)"
                    />
                  </td>
                  <td><strong>{{ item.sku }}</strong></td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.quantity }}</td>
                  <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                  <td>{{ currencySymbol }}{{ item.line_total.toLocaleString() }}</td>
                  <td>
                    <span :class="['badge', getTrendClass(item.trend)]">
                      {{ t(`trends.${item.trend}`) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="order-summary">
            <div class="summary-row">
              <span class="summary-label">{{ t('restocking.totalCost') }}</span>
              <span class="summary-value">{{ currencySymbol }}{{ checkedTotal.toLocaleString() }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">{{ t('restocking.remaining') }}</span>
              <span class="summary-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</span>
            </div>
          </div>

          <div v-if="submitSuccess" class="success-message">{{ submitSuccess }}</div>
          <div v-if="submitError" class="error">{{ submitError }}</div>

          <button
            class="place-order-btn"
            :disabled="checkedSkus.size === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
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
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitSuccess = ref(null)
    const submitError = ref(null)

    const budget = ref(0)
    const budgetMax = ref(0)
    // Ceil so the slider's max is always reachable — budgetMax itself may be
    // fractional (e.g. 5316.48), but the slider moves in whole-dollar steps.
    const sliderMax = computed(() => Math.ceil(budgetMax.value))
    const recommendedItems = ref([])
    const totalCost = ref(0)
    const checkedSkus = ref(new Set())
    // Tracks whether applyRecommendations has ever run. Only the very first
    // call should default every recommended item to checked; subsequent
    // calls (from budget changes / post-order refresh) must preserve the
    // user's existing unchecked selections instead of clobbering them.
    let hasLoadedOnce = false

    let debounceTimer = null

    const checkedTotal = computed(() => {
      return recommendedItems.value
        .filter(item => checkedSkus.value.has(item.sku))
        .reduce((sum, item) => sum + item.line_total, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - checkedTotal.value
    })

    const getTrendClass = (trend) => {
      const map = {
        increasing: 'increasing',
        stable: 'stable',
        decreasing: 'decreasing'
      }
      return map[trend] || 'stable'
    }

    const applyRecommendations = (data) => {
      const newSkus = data.recommended_items.map(item => item.sku)

      if (!hasLoadedOnce) {
        // First load ever: check everything by default.
        checkedSkus.value = new Set(newSkus)
        hasLoadedOnce = true
      } else {
        // Subsequent recompute: keep the user's exclusions for SKUs that
        // were already visible and unchecked. Brand-new SKUs (the user
        // hasn't had a chance to react to them) default to checked.
        const previousSkus = new Set(recommendedItems.value.map(item => item.sku))
        const nextChecked = new Set(
          newSkus.filter(sku => !previousSkus.has(sku) || checkedSkus.value.has(sku))
        )
        checkedSkus.value = nextChecked
      }

      recommendedItems.value = data.recommended_items
      totalCost.value = data.total_cost
    }

    const fetchRecommendations = async (budgetValue) => {
      const data = await api.getRestockingRecommendations(budgetValue)
      applyRecommendations(data)
      return data
    }

    const loadInitial = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await fetchRecommendations(0)
        budgetMax.value = data.budget_max
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const onBudgetInput = () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(async () => {
        try {
          await fetchRecommendations(budget.value)
        } catch (err) {
          error.value = 'Failed to load restocking recommendations: ' + err.message
        }
      }, 300)
    }

    const toggleChecked = (sku) => {
      const newSet = new Set(checkedSkus.value)
      if (newSet.has(sku)) {
        newSet.delete(sku)
      } else {
        newSet.add(sku)
      }
      checkedSkus.value = newSet
    }

    const placeOrder = async () => {
      submitSuccess.value = null
      submitError.value = null
      submitting.value = true
      try {
        const items = recommendedItems.value
          .filter(item => checkedSkus.value.has(item.sku))
          .map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: item.quantity,
            unit_price: item.unit_cost
          }))

        await api.submitRestockingOrder(items)
        submitSuccess.value = t('restocking.orderSuccess')
        await fetchRecommendations(budget.value)
      } catch (err) {
        submitError.value = t('restocking.orderError')
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadInitial)

    return {
      t,
      loading,
      error,
      submitting,
      submitSuccess,
      submitError,
      budget,
      budgetMax,
      sliderMax,
      recommendedItems,
      checkedSkus,
      checkedTotal,
      remainingBudget,
      currencySymbol,
      getTrendClass,
      onBudgetInput,
      toggleChecked,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-slider-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.select-hint {
  color: #64748b;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}

.no-items {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.col-check {
  width: 40px;
}

.order-summary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-label {
  color: #64748b;
  font-size: 0.938rem;
  font-weight: 600;
}

.summary-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.success-message {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.938rem;
}

.place-order-btn {
  margin-top: 1.25rem;
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
