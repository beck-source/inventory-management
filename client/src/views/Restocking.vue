<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="successMessage" class="success-banner">
        <span>{{ successMessage }}</span>
        <button class="success-dismiss" @click="successMessage = ''" :title="t('common.dismiss')">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.stats.recommendedSpend') }}</div>
          <div class="stat-value">{{ formatCurrency(totalSpend) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.stats.remainingBudget') }}</div>
          <div class="stat-value">{{ formatCurrency(remainingBudget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetPlanner') }}</h3>
          <span class="budget-display">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="slider-row">
          <input
            v-model.number="budget"
            type="range"
            class="budget-slider"
            min="0"
            max="200000"
            step="1000"
          />
          <div class="slider-scale">
            <span>{{ formatCurrency(0) }}</span>
            <span>{{ formatCurrency(200000) }}</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.empty') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.roi') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.name }}</strong></td>
                <td>{{ item.category }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.roi.toFixed(2) }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td><strong>{{ item.quantity }}</strong></td>
                <td><strong>{{ formatCurrency(item.lineTotal) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t } = useI18n()

    // Shared location filter (used when placing the order)
    const { selectedLocation } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref('')

    // Raw demand forecast data
    const forecasts = ref([])

    // Budget bound to the range slider (USD). Default 50k, range 0-200k.
    const budget = ref(50000)

    // Format any numeric value as USD currency.
    const formatCurrency = (value) => {
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    // Recommendation engine: ROI-first greedy fill.
    //
    // We want to spend the available budget on the items that deliver the most
    // forecasted demand per dollar. To do this:
    //   1. Compute an ROI for each forecast item = forecasted_demand / unit_cost.
    //      Higher ROI means more units of expected demand covered per dollar spent.
    //   2. Sort the items by ROI descending so the most cost-effective items are
    //      considered first.
    //   3. Greedily walk the sorted list, buying as many units of each item as the
    //      remaining budget allows (capped at that item's forecasted demand, since
    //      buying beyond forecasted demand would be wasteful). Once an item can no
    //      longer be afforded at all (qty === 0) we stop, because every subsequent
    //      item has an equal-or-lower ROI and the budget is already nearly exhausted.
    // This recomputes reactively whenever the budget slider (or forecast data) changes.
    const recommendations = computed(() => {
      // 1. Map to a working shape with ROI. Guard against a zero/undefined unit_cost.
      const ranked = forecasts.value
        .filter(f => f.unit_cost > 0)
        .map(f => ({
          sku: f.item_sku,
          name: f.item_name,
          category: f.category,
          trend: f.trend,
          unit_cost: f.unit_cost,
          forecasted_demand: f.forecasted_demand,
          roi: f.forecasted_demand / f.unit_cost
        }))
        // 2. Sort by ROI descending.
        .sort((a, b) => b.roi - a.roi)

      // 3. Greedy fill within budget.
      const result = []
      let remaining = budget.value

      for (const item of ranked) {
        const qty = Math.min(item.forecasted_demand, Math.floor(remaining / item.unit_cost))
        if (qty === 0) break
        const lineTotal = qty * item.unit_cost
        remaining -= lineTotal
        result.push({
          sku: item.sku,
          name: item.name,
          category: item.category,
          trend: item.trend,
          unit_cost: item.unit_cost,
          forecasted_demand: item.forecasted_demand,
          roi: item.roi,
          quantity: qty,
          lineTotal
        })
      }

      return result
    })

    // Total recommended spend = sum of all line totals.
    const totalSpend = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.lineTotal, 0)
    })

    // Remaining budget after the recommended spend.
    const remainingBudget = computed(() => {
      return budget.value - totalSpend.value
    })

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || submitting.value) return

      try {
        submitting.value = true
        error.value = null
        successMessage.value = ''

        const response = await api.postRestockingOrder({
          budget: budget.value,
          warehouse: selectedLocation.value,
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            category: r.category,
            quantity: r.quantity,
            unit_cost: r.unit_cost
          }))
        })

        successMessage.value = t('restocking.orderPlaced', { id: response.id })
      } catch (err) {
        error.value = 'Failed to place restocking order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => loadData())

    return {
      t,
      loading,
      error,
      submitting,
      successMessage,
      budget,
      recommendations,
      totalSpend,
      remainingBudget,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.slider-row {
  padding: 0.5rem 0.25rem 0;
}

.budget-slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
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
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #64748b;
}

.budget-display {
  font-size: 1.125rem;
  font-weight: 700;
  color: #2563eb;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
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

.success-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 0.875rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.success-dismiss {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #16a34a;
  cursor: pointer;
  transition: all 0.2s;
}

.success-dismiss:hover {
  background: #dcfce7;
}

.success-dismiss svg {
  width: 18px;
  height: 18px;
}
</style>
