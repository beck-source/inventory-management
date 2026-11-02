<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="successInfo" class="success-banner">
        <div class="success-title">{{ t('restocking.success.title') }}</div>
        <div class="success-message">
          {{ t('restocking.success.message', { orderNumber: successInfo.orderNumber, delivery: successInfo.delivery }) }}
        </div>
        <div class="success-hint">{{ t('restocking.success.viewInOrders') }}</div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.stats.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.recommendedItems') }}</div>
          <div class="stat-value">{{ recommendation.length }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.stats.orderTotal') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ orderTotal.toLocaleString() }}</div>
        </div>
        <div class="stat-card" :class="remaining < 0 ? 'danger' : 'info'">
          <div class="stat-label">{{ t('restocking.stats.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ remaining.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget.title') }}</h3>
        </div>
        <div class="budget-control">
          <label class="budget-label" for="budget-slider">{{ t('restocking.budget.label') }}</label>
          <div class="budget-slider-row">
            <input
              id="budget-slider"
              type="range"
              min="0"
              :max="maxBudget"
              :step="step"
              v-model.number="budget"
              class="budget-slider"
            />
            <span class="budget-amount">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          </div>
          <p class="budget-help">{{ t('restocking.budget.help') }}</p>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendation.title') }}</h3>
          <button class="reset-btn" @click="resetToRecommendation" :disabled="!edited">
            {{ t('restocking.recommendation.reset') }}
          </button>
        </div>

        <div v-if="recommendation.length === 0" class="empty-state">
          {{ t('restocking.recommendation.empty') }}
        </div>

        <template v-else>
          <div v-if="orderTotal > budget" class="over-budget-warning">
            {{ t('restocking.recommendation.overBudget') }}
          </div>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.forecastedDemand') }}</th>
                  <th>{{ t('restocking.table.quantity') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.lineTotal') }}</th>
                  <th>{{ t('restocking.table.remove') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="line in orderLines" :key="line.sku">
                  <td><strong>{{ line.sku }}</strong></td>
                  <td>{{ translateProductName(line.name) }}</td>
                  <td>{{ line.forecasted_demand }}</td>
                  <td>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      class="qty-input"
                      :value="line.quantity"
                      @change="updateQuantity(line, $event)"
                    />
                  </td>
                  <td>{{ currencySymbol }}{{ line.unit_cost.toLocaleString() }}</td>
                  <td><strong>{{ currencySymbol }}{{ (line.quantity * line.unit_cost).toLocaleString() }}</strong></td>
                  <td>
                    <button class="remove-btn" @click="removeLine(line.sku)">
                      {{ t('restocking.table.remove') }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="place-order-row">
            <button
              class="place-order-btn"
              @click="placeOrder"
              :disabled="submitting || orderLines.length === 0"
            >
              {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const forecasts = ref([])
    const budget = ref(0)
    const orderLines = ref([])
    const edited = ref(false)
    const successInfo = ref(null)

    // Candidate lines: items whose forecast exceeds current demand
    const candidates = computed(() => {
      return forecasts.value
        .map((f) => {
          const candidateQty = Math.max(f.forecasted_demand - f.current_demand, 0)
          return {
            sku: f.item_sku,
            name: f.item_name,
            forecasted_demand: f.forecasted_demand,
            unit_cost: f.unit_cost,
            quantity: candidateQty
          }
        })
        .filter((c) => c.quantity > 0)
        .sort((a, b) => b.forecasted_demand - a.forecasted_demand)
    })

    // Full-restock total, rounded up to a clean integer
    const maxBudget = computed(() => {
      const total = candidates.value.reduce((sum, c) => sum + c.quantity * c.unit_cost, 0)
      return Math.ceil(total)
    })

    const step = computed(() => Math.max(1, Math.round(maxBudget.value / 100)))

    // Greedy selection: highest forecasted demand first, within budget
    const recommendation = computed(() => {
      const selected = []
      let spent = 0
      for (const c of candidates.value) {
        const lineCost = c.quantity * c.unit_cost
        if (lineCost <= budget.value - spent) {
          selected.push({
            sku: c.sku,
            name: c.name,
            forecasted_demand: c.forecasted_demand,
            unit_cost: c.unit_cost,
            quantity: c.quantity
          })
          spent += lineCost
        }
      }
      return selected
    })

    const orderTotal = computed(() => {
      return orderLines.value.reduce((sum, line) => sum + line.quantity * line.unit_cost, 0)
    })

    const remaining = computed(() => budget.value - orderTotal.value)

    // Re-seed the working set from the recommendation only while untouched
    watch(
      recommendation,
      (newRecommendation) => {
        if (!edited.value) {
          orderLines.value = JSON.parse(JSON.stringify(newRecommendation))
        }
      },
      { immediate: true }
    )

    const updateQuantity = (line, event) => {
      const parsed = parseInt(event.target.value, 10)
      const quantity = Number.isNaN(parsed) || parsed < 1 ? 1 : parsed
      line.quantity = quantity
      event.target.value = quantity
      edited.value = true
    }

    const removeLine = (sku) => {
      edited.value = true
      orderLines.value = orderLines.value.filter((line) => line.sku !== sku)
    }

    const resetToRecommendation = () => {
      edited.value = false
      orderLines.value = JSON.parse(JSON.stringify(recommendation.value))
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) {
        return dateString
      }
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        // Initialize budget to about 50% of the full-restock total once data exists
        budget.value = Math.round(maxBudget.value / 2)
      } catch (err) {
        error.value = t('restocking.loadError')
        console.error('Failed to load demand forecasts:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      try {
        submitting.value = true
        error.value = null
        const items = orderLines.value.map((line) => ({
          sku: line.sku,
          name: line.name,
          quantity: line.quantity,
          unit_price: line.unit_cost
        }))
        const resp = await api.createOrder({ items })
        successInfo.value = {
          orderNumber: resp.order_number,
          delivery: formatDate(resp.expected_delivery)
        }
        // Re-seed a fresh recommendation after a successful submission
        edited.value = false
        orderLines.value = JSON.parse(JSON.stringify(recommendation.value))
      } catch (err) {
        error.value = t('restocking.error')
        console.error('Failed to place order:', err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      submitting,
      currencySymbol,
      translateProductName,
      budget,
      maxBudget,
      step,
      recommendation,
      orderLines,
      edited,
      orderTotal,
      remaining,
      successInfo,
      updateQuantity,
      removeLine,
      resetToRecommendation,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-control {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.budget-slider {
  flex: 1;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-amount {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 120px;
  text-align: right;
}

.budget-help {
  font-size: 0.813rem;
  color: #64748b;
}

.qty-input {
  width: 80px;
  padding: 0.4rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.813rem;
  color: #0f172a;
  background: white;
  font-weight: 500;
  transition: all 0.2s;
}

.qty-input:hover {
  border-color: #94a3b8;
}

.qty-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.reset-btn {
  padding: 0.4rem 0.875rem;
  background: white;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #94a3b8;
  color: #0f172a;
}

.reset-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.remove-btn {
  padding: 0.3rem 0.75rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #991b1b;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fee2e2;
  border-color: #fca5a5;
}

.place-order-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.25rem;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.over-budget-warning {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  color: #92400e;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-size: 0.938rem;
}

.success-banner {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.success-title {
  font-size: 1rem;
  font-weight: 700;
  color: #065f46;
  margin-bottom: 0.375rem;
}

.success-message {
  font-size: 0.875rem;
  color: #047857;
  margin-bottom: 0.25rem;
}

.success-hint {
  font-size: 0.813rem;
  color: #059669;
}
</style>
