<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-header">
        <label for="budget-range" class="budget-label">{{ t('restocking.budgetLabel') }}</label>
        <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
      <input
        id="budget-range"
        type="range"
        min="0"
        max="100000"
        step="500"
        v-model.number="budget"
        class="budget-slider"
      >
    </div>

    <div v-if="successMessage" class="success-banner">
      <span>{{ successMessage }}</span>
      <router-link to="/orders" class="success-link">{{ t('restocking.viewInOrders') }}</router-link>
      <button type="button" class="dismiss-btn" @click="successMessage = null">&times;</button>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.allocated') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ allocated.toLocaleString() }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ remaining.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendations.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting || loading || isStale"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="submitError" class="error">{{ submitError }}</div>

        <p v-if="recommendations.length === 0" class="no-recommendations">
          {{ t('restocking.noRecommendations') }}
        </p>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.reason') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.subtotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ item.category }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td>{{ reasonText(item) }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ item.subtotal.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const budget = ref(20000)
    const allocated = ref(0)
    const remaining = ref(0)
    const recommendations = ref([])

    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)

    let debounceTimer = null
    // Budget the displayed recommendations were computed for; also true while a reload is pending
    const loadedBudget = ref(null)
    // Incremented per request so a slow, older response can't overwrite a newer one
    let requestSeq = 0

    const loadRecommendations = async () => {
      const seq = ++requestSeq
      const requestedBudget = budget.value
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockRecommendations(requestedBudget)
        if (seq !== requestSeq) return
        allocated.value = data.allocated
        remaining.value = data.remaining
        recommendations.value = data.items
        loadedBudget.value = requestedBudget
      } catch (err) {
        if (seq !== requestSeq) return
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        if (seq === requestSeq) loading.value = false
      }
    }

    // Recommendations are stale until they match the slider (covers the debounce window)
    const isStale = computed(() => loadedBudget.value !== budget.value)

    // Debounce budget changes so we don't fire a request on every tick of the slider drag
    watch(budget, () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 350)
    })

    onUnmounted(() => {
      if (debounceTimer) clearTimeout(debounceTimer)
      requestSeq++
    })

    const reasonText = (item) => {
      if (item.source === 'backlog') {
        return t('restocking.reasonBacklog', {
          days: item.days_delayed,
          priority: t('priority.' + item.priority)
        })
      }
      if (item.source === 'demand') {
        return t('restocking.reasonDemand', { count: item.demand_gap })
      }
      return ''
    }

    const placeOrder = async () => {
      try {
        submitting.value = true
        submitError.value = null
        const payload = {
          budget: loadedBudget.value,
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            category: r.category,
            warehouse: r.warehouse,
            unit_cost: r.unit_cost,
            quantity: r.quantity
          }))
        }
        const order = await api.submitRestockOrder(payload)
        successMessage.value = t('restocking.orderSuccess', {
          orderNumber: order.order_number,
          days: order.lead_time_days
        })
        // Backlog/demand datasets are static mock reference data in this demo, so nothing
        // decrements them when an order is placed - the same items intentionally keep
        // reappearing until the budget itself changes.
        await loadRecommendations()
      } catch (err) {
        submitError.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      loading,
      error,
      budget,
      allocated,
      remaining,
      recommendations,
      currencySymbol,
      translateProductName,
      translateWarehouse,
      reasonText,
      submitting,
      isStale,
      submitError,
      successMessage,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.budget-label {
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2563eb;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
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

.no-recommendations {
  color: #64748b;
  padding: 1.5rem 0;
  text-align: center;
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.success-link {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
}

.dismiss-btn {
  margin-left: auto;
  background: none;
  border: none;
  color: #065f46;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  padding: 0 0.25rem;
}
</style>
