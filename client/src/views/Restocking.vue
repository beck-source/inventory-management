<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="orderPlaced" class="success-banner">
        <span class="checkmark">&#10003;</span>
        {{ t('restocking.orderPlaced') }}
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
          <span class="budget-display">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
        <input
          type="range"
          v-model.number="budget"
          :min="0"
          :max="maxBudget"
          :step="100"
          class="budget-slider"
        />
        <div class="summary-pills">
          <div class="pill">
            <span class="pill-label">{{ t('restocking.itemsRecommended') }}</span>
            <span class="pill-value">{{ recommendedItems.length }}</span>
          </div>
          <div class="pill">
            <span class="pill-label">{{ t('restocking.estimatedSpend') }}</span>
            <span class="pill-value">{{ currencySymbol }}{{ estimatedSpend.toLocaleString() }}</span>
          </div>
          <div class="pill">
            <span class="pill-label">{{ t('restocking.remainingBudget') }}</span>
            <span class="pill-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <div v-if="recommendedItems.length > 0" class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
          <button
            class="place-order-btn"
            :disabled="recommendedItems.length === 0 || orderPlaced"
            @click="placeOrder"
          >
            {{ t('restocking.placeOrder') }}
          </button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('inventory.table.sku') }}</th>
                <th>{{ t('inventory.table.name') }}</th>
                <th>{{ t('demand.table.trend') }}</th>
                <th>{{ t('demand.table.currentDemand') }}</th>
                <th>{{ t('demand.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.qtyToOrder') }}</th>
                <th>{{ t('restocking.unitCost') }}</th>
                <th>{{ t('restocking.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendedItems" :key="item.id">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td><span :class="['badge', item.trend]">{{ item.trend }}</span></td>
                <td>{{ item.current_demand.toLocaleString() }}</td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ (item.unit_cost * item.forecasted_demand).toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="card">
        <div class="empty-state">
          {{ t('restocking.noItems') }}
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

    const forecasts = ref([])
    const loading = ref(true)
    const error = ref(null)
    const budget = ref(0)
    const orderPlaced = ref(false)

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const maxBudget = computed(() => {
      return forecasts.value.reduce((sum, item) => {
        return sum + item.unit_cost * item.forecasted_demand
      }, 0)
    })

    const recommendedItems = computed(() => {
      const sorted = [...forecasts.value].sort((a, b) => {
        const trendOrder = { increasing: 0, stable: 1, decreasing: 2 }
        const trendA = trendOrder[a.trend] ?? 1
        const trendB = trendOrder[b.trend] ?? 1
        if (trendA !== trendB) return trendA - trendB
        const diffA = a.forecasted_demand - a.current_demand
        const diffB = b.forecasted_demand - b.current_demand
        return diffB - diffA
      })

      let running = 0
      const included = []
      for (const item of sorted) {
        const lineTotal = item.unit_cost * item.forecasted_demand
        if (running + lineTotal <= budget.value) {
          running += lineTotal
          included.push(item)
        }
      }
      return included
    })

    const estimatedSpend = computed(() => {
      return recommendedItems.value.reduce((sum, item) => {
        return sum + item.unit_cost * item.forecasted_demand
      }, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - estimatedSpend.value
    })

    const placeOrder = async () => {
      try {
        const mappedItems = recommendedItems.value.map(item => ({
          sku: item.item_sku,
          name: item.item_name,
          quantity: item.forecasted_demand,
          unit_cost: item.unit_cost
        }))
        await api.createRestockingOrder(mappedItems)
        orderPlaced.value = true
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
        console.error(err)
      }
    }

    watch(budget, () => {
      orderPlaced.value = false
    })

    onMounted(async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        budget.value = Math.round(maxBudget.value * 0.5 / 100) * 100
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    })

    return {
      t,
      forecasts,
      loading,
      error,
      budget,
      orderPlaced,
      currencySymbol,
      maxBudget,
      recommendedItems,
      estimatedSpend,
      remainingBudget,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.budget-slider {
  width: 100%;
  margin: 0.75rem 0 0;
  accent-color: #2563eb;
  height: 6px;
  cursor: pointer;
}

.budget-display {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-pills {
  display: flex;
  gap: 1.5rem;
  margin-top: 1rem;
}

.pill {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pill-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.pill-value {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkmark {
  font-size: 1.125rem;
  font-weight: 700;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
