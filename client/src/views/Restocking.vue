<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Slider -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
          <span class="budget-display">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
        <div class="slider-container">
          <span class="slider-label">{{ currencySymbol }}0</span>
          <input
            type="range"
            class="budget-slider"
            v-model.number="budget"
            min="0"
            max="100000"
            step="500"
          />
          <span class="slider-label">{{ currencySymbol }}100,000</span>
        </div>
        <div class="budget-summary">
          <div class="budget-stat">
            <span class="budget-stat-label">{{ t('restocking.totalSelected') }}</span>
            <span class="budget-stat-value spend">{{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</span>
          </div>
          <div class="budget-stat">
            <span class="budget-stat-label">{{ t('restocking.budgetRemaining') }}</span>
            <span class="budget-stat-value" :class="remaining < 0 ? 'over' : 'remain'">
              {{ currencySymbol }}{{ remaining.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Success Banner -->
      <div v-if="lastOrder" class="success-banner">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="10" fill="#059669"/>
          <path d="M6 10l3 3 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div>
          <strong>{{ t('restocking.orderPlaced') }}</strong> —
          {{ lastOrder.order_number }} &middot; {{ t('orders.table.expectedDelivery') }}: {{ formatDate(lastOrder.expected_delivery) }}
        </div>
        <button class="dismiss-btn" @click="lastOrder = null">✕</button>
      </div>

      <!-- Recommended Items -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendedItems.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="recommendedItems.length === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? t('common.loading') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="recommendedItems.length === 0" class="no-items">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('inventory.table.sku') }}</th>
                <th>{{ t('inventory.table.itemName') }}</th>
                <th>{{ t('restocking.demandGrowth') }}</th>
                <th>{{ t('restocking.qtyToRestock') }}</th>
                <th>{{ t('restocking.unitCost') }}</th>
                <th>{{ t('restocking.totalCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendedItems" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>
                  <span class="badge increasing">+{{ item.demandGrowthPct.toFixed(1) }}%</span>
                </td>
                <td>{{ item.qtyToRestock.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ item.unitCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
                <td><strong>{{ currencySymbol }}{{ item.itemCost.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const lastOrder = ref(null)
    const budget = ref(10000)

    const allForecasts = ref([])
    const inventoryMap = ref({})  // keyed by sku

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const [forecasts, inventoryItems] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({ warehouse: filters.warehouse, category: filters.category })
        ])
        allForecasts.value = forecasts
        inventoryMap.value = Object.fromEntries(inventoryItems.map(i => [i.sku, i]))
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch([selectedLocation, selectedCategory], loadData)
    onMounted(loadData)

    // Items eligible for restocking: have inventory data, and need restocking
    const eligibleItems = computed(() => {
      return allForecasts.value
        .filter(f => {
          const inv = inventoryMap.value[f.item_sku]
          if (!inv) return false
          const qty = Math.max(0, inv.reorder_point - inv.quantity_on_hand)
          return qty > 0 && f.current_demand > 0
        })
        .map(f => {
          const inv = inventoryMap.value[f.item_sku]
          const qtyToRestock = Math.max(0, inv.reorder_point - inv.quantity_on_hand)
          const demandGrowthPct = ((f.forecasted_demand - f.current_demand) / f.current_demand) * 100
          return {
            sku: f.item_sku,
            name: f.item_name,
            demandGrowthPct,
            qtyToRestock,
            unitCost: inv.unit_cost,
            itemCost: qtyToRestock * inv.unit_cost,
            warehouse: inv.warehouse,
            category: inv.category
          }
        })
        .sort((a, b) => b.demandGrowthPct - a.demandGrowthPct)
    })

    // Greedy selection within budget
    const recommendedItems = computed(() => {
      let remaining = budget.value
      const selected = []
      for (const item of eligibleItems.value) {
        if (item.itemCost <= remaining) {
          selected.push(item)
          remaining -= item.itemCost
        }
      }
      return selected
    })

    const totalCost = computed(() =>
      recommendedItems.value.reduce((sum, i) => sum + i.itemCost, 0)
    )

    const remaining = computed(() => budget.value - totalCost.value)

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      })
    }

    const placeOrder = async () => {
      if (recommendedItems.value.length === 0) return
      placing.value = true
      try {
        const filters = getCurrentFilters()
        const items = recommendedItems.value.map(i => ({
          sku: i.sku,
          name: i.name,
          quantity: i.qtyToRestock,
          unit_price: i.unitCost
        }))
        const order = await api.createOrder({
          customer: 'Restocking System',
          items,
          warehouse: filters.warehouse !== 'all' ? filters.warehouse : null,
          category: filters.category !== 'all' ? filters.category : null
        })
        lastOrder.value = order
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    return {
      t,
      loading,
      error,
      placing,
      lastOrder,
      budget,
      currencySymbol,
      recommendedItems,
      totalCost,
      remaining,
      formatDate,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card .card-header {
  align-items: center;
}

.budget-display {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.025em;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0 1rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.slider-label {
  font-size: 0.813rem;
  color: #64748b;
  white-space: nowrap;
}

.budget-summary {
  display: flex;
  gap: 2rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f1f5f9;
}

.budget-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.budget-stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.budget-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.budget-stat-value.spend { color: #0f172a; }
.budget-stat-value.remain { color: #059669; }
.budget-stat-value.over { color: #dc2626; }

.success-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  color: #065f46;
  font-size: 0.938rem;
}

.dismiss-btn {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
  font-size: 1rem;
  padding: 0.25rem;
}

.dismiss-btn:hover { color: #0f172a; }

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) { background: #1d4ed8; }

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.no-items {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
