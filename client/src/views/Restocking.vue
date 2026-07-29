<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-body">
        <input
          v-model.number="budget"
          type="range"
          min="0"
          max="500000"
          step="5000"
          class="budget-slider"
        />
        <div class="budget-value">{{ formatMoney(budget) }}</div>
        <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="recommendations">
      <div v-if="submitMessage" :class="['submit-message', submitStatus]">{{ submitMessage }}</div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.allocated') }}</div>
          <div class="stat-value">{{ formatMoney(recommendations.total_cost) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatMoney(recommendations.remaining_budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.items.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.totalUnits') }}</div>
          <div class="stat-value">{{ recommendations.total_units.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ t('restocking.leadTimeDays', { days: recommendations.max_lead_time_days }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }} ({{ recommendations.items.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="submitting || loading || recommendations.items.length === 0"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
        <div class="table-container">
          <table v-if="recommendations.items.length">
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.onHand') }}</th>
                <th>{{ t('restocking.table.forecast') }}</th>
                <th>{{ t('restocking.table.shortfall') }}</th>
                <th>{{ t('restocking.table.orderQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.coverage') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations.items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.category }}</td>
                <td>
                  <!-- Rising demand is the risk here: increasing trend is flagged as danger, decreasing as success -->
                  <span :class="['badge', getTrendClass(item.trend)]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>{{ item.quantity_on_hand }}</td>
                <td>{{ item.forecasted_demand }}</td>
                <td>{{ item.shortfall }}</td>
                <td><strong>{{ item.recommended_quantity }}</strong></td>
                <td>{{ formatMoney(item.unit_cost) }}</td>
                <td><strong>{{ formatMoney(item.line_total) }}</strong></td>
                <td>{{ t('restocking.leadTimeDays', { days: item.lead_time_days }) }}</td>
                <td>
                  <span :class="['badge', item.fully_funded ? 'success' : 'warning']">
                    {{ item.fully_funded ? t('restocking.full') : t('restocking.partial') }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">{{ t('restocking.recommendedEmpty') }}</div>
        </div>
      </div>

      <div class="card" v-if="recommendations.unfunded_items.length">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.unfunded') }} ({{ recommendations.unfunded_items.length }})</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.shortfall') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.shortfallCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations.unfunded_items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.shortfall }}</td>
                <td>{{ formatMoney(item.unit_cost) }}</td>
                <td><strong>{{ formatMoney(item.shortfall_cost) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    // Budget figures are money, so pad to a fixed number of decimals instead of the bare
    // toLocaleString() used elsewhere (which renders 23740.50 as "23,740.5"). JPY has no minor unit.
    const formatMoney = (value) => {
      const decimals = currentCurrency.value === 'JPY' ? 0 : 2
      return currencySymbol.value + Number(value).toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      })
    }

    const budget = ref(100000)
    const loading = ref(true)
    const error = ref(null)
    const recommendations = ref(null)

    const submitting = ref(false)
    const submitMessage = ref('')
    const submitStatus = ref('')

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendations.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce budget changes with a plain setTimeout (no @vueuse/core dependency in this project)
    watch(budget, () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 250)
    })

    const getTrendClass = (trend) => {
      const trendMap = {
        increasing: 'danger',
        decreasing: 'success',
        stable: 'info'
      }
      return trendMap[trend] || 'info'
    }

    const placeOrder = async () => {
      if (!recommendations.value || recommendations.value.items.length === 0) return

      submitting.value = true
      submitMessage.value = ''
      try {
        const result = await api.createRestockOrder({
          budget: budget.value,
          items: recommendations.value.items
        })
        submitMessage.value = t('restocking.orderPlaced', { orderNumber: result.order_number })
        submitStatus.value = 'success'
        await loadRecommendations()
      } catch (err) {
        submitMessage.value = t('restocking.orderFailed')
        submitStatus.value = 'error'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      budget,
      loading,
      error,
      recommendations,
      submitting,
      submitMessage,
      submitStatus,
      currencySymbol,
      formatMoney,
      getTrendClass,
      placeOrder
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

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  appearance: none;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  cursor: pointer;
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  cursor: pointer;
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-value {
  margin-top: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-hint {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: #64748b;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
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

.submit-message {
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.submit-message.success {
  background: #d1fae5;
  color: #059669;
}

.submit-message.error {
  background: #fee2e2;
  color: #dc2626;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}
</style>
