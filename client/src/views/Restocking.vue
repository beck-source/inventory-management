<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <!-- Success state -->
    <div v-else-if="orderSuccess" class="card success-card">
      <div class="success-icon">✓</div>
      <h3>{{ t('restocking.orderPlaced') }}</h3>
      <p>{{ t('restocking.orderSuccess').replace('{orderNumber}', submittedOrder.order_number) }}</p>
      <p>{{ t('restocking.expectedDelivery').replace('{date}', formatDate(submittedOrder.expected_delivery)) }}</p>
      <button @click="resetForm" class="btn-primary">{{ t('restocking.placeAnother') }}</button>
    </div>

    <!-- Main form -->
    <div v-else>
      <!-- Budget card -->
      <div class="card budget-card">
        <div class="budget-header">
          <span class="budget-label">{{ t('restocking.budgetLabel') }}</span>
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
        <input type="range" v-model.number="budget" min="0" max="500000" step="1000" class="budget-slider" />
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: budgetUsedPercent + '%', background: progressColor }"></div>
        </div>
        <div class="budget-meta">
          <span>{{ t('restocking.budgetUsed') }}: {{ formatCurrency(totalCost) }}</span>
          <span>{{ t('restocking.remaining') }}: {{ formatCurrency(remainingBudget) }}</span>
        </div>
      </div>

      <!-- Selected items card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.selectedItems') }} ({{ selectedItems.length }})</h3>
          <span class="total-cost">{{ formatCurrency(totalCost) }}</span>
        </div>

        <div v-if="selectedItems.length === 0" class="no-items">{{ t('restocking.noItems') }}</div>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>{{ t('restocking.sku') }}</th>
                <th>{{ t('restocking.itemName') }}</th>
                <th>{{ t('restocking.trend') }}</th>
                <th>{{ t('restocking.restockQty') }}</th>
                <th>{{ t('restocking.unitCost') }}</th>
                <th>{{ t('restocking.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedItems" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td><span :class="['badge', item.trend]">{{ item.trend }}</span></td>
                <td>{{ item.quantity.toLocaleString() }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td><strong>{{ formatCurrency(item.line_total) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="order-actions">
        <button
          @click="placeOrder"
          :disabled="selectedItems.length === 0 || submitting"
          class="btn-primary btn-place-order"
        >
          {{ submitting ? t('common.loading') : t('restocking.placeOrder') }}
        </button>
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
    const budget = ref(100000)
    const submitting = ref(false)
    const orderSuccess = ref(false)
    const submittedOrder = ref(null)
    const allForecasts = ref([])
    const inventoryMap = ref({})

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        allForecasts.value = forecasts
        const map = {}
        inventory.forEach(item => {
          map[item.sku] = item
        })
        inventoryMap.value = map
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const selectedItems = computed(() => {
      // Filter out decreasing trend
      const candidates = allForecasts.value
        .filter(f => f.trend !== 'decreasing')
        .reduce((acc, f) => {
          const inv = inventoryMap.value[f.item_sku]
          if (!inv) return acc
          const gap = f.forecasted_demand - inv.quantity_on_hand
          if (gap <= 0) return acc
          acc.push({
            sku: f.item_sku,
            name: f.item_name,
            trend: f.trend,
            quantity: gap,
            unit_cost: inv.unit_cost,
            line_total: gap * inv.unit_cost
          })
          return acc
        }, [])

      // Sort: increasing first, then stable; within each tier by line_total descending
      candidates.sort((a, b) => {
        const tierOrder = { increasing: 0, stable: 1 }
        const tierA = tierOrder[a.trend] ?? 2
        const tierB = tierOrder[b.trend] ?? 2
        if (tierA !== tierB) return tierA - tierB
        return b.line_total - a.line_total
      })

      // Greedy fill
      let remaining = budget.value
      const result = []
      for (const item of candidates) {
        if (item.line_total <= remaining) {
          result.push(item)
          remaining -= item.line_total
        }
        // Don't break — a cheaper item later may still fit
      }
      return result
    })

    const totalCost = computed(() => selectedItems.value.reduce((sum, i) => sum + i.line_total, 0))

    const budgetUsedPercent = computed(() => {
      return budget.value > 0 ? Math.min((totalCost.value / budget.value) * 100, 100) : 0
    })

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const progressColor = computed(() => {
      const pct = budgetUsedPercent.value
      if (pct > 95) return '#ef4444'
      if (pct > 80) return '#f59e0b'
      return '#10b981'
    })

    const placeOrder = async () => {
      if (selectedItems.value.length === 0) return
      try {
        submitting.value = true
        const result = await api.createRestockingOrder({
          budget: budget.value,
          items: selectedItems.value.map(item => ({
            sku: item.sku,
            name: item.name,
            quantity: item.quantity,
            unit_cost: item.unit_cost,
            line_total: item.line_total
          }))
        })
        submittedOrder.value = result
        orderSuccess.value = true
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    const resetForm = () => {
      orderSuccess.value = false
      submittedOrder.value = null
      budget.value = 100000
    }

    const formatCurrency = (v) => v.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    onMounted(() => loadData())

    return {
      t,
      loading,
      error,
      budget,
      submitting,
      orderSuccess,
      submittedOrder,
      selectedItems,
      totalCost,
      budgetUsedPercent,
      remainingBudget,
      progressColor,
      placeOrder,
      resetForm,
      formatCurrency,
      formatDate
    }
  }
}
</script>

<style scoped>
.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  height: 6px;
  margin: 0.75rem 0;
  cursor: pointer;
  accent-color: #3b82f6;
}

.progress-track {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.budget-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  margin-top: 0.5rem;
}

.no-items {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.total-cost {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.btn-place-order {
  min-width: 160px;
}

.success-card {
  text-align: center;
  padding: 3rem;
  border-left: 4px solid #10b981;
}

.success-icon {
  font-size: 3rem;
  color: #10b981;
  margin-bottom: 1rem;
}

.success-card h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.5rem;
}

.success-card p {
  color: #64748b;
  margin-bottom: 0.5rem;
}

.success-card button {
  margin-top: 1.5rem;
}

.restock-table {
  table-layout: fixed;
  width: 100%;
}
</style>
