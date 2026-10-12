<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.recommendedTotal') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ selectedTotal.toLocaleString() }}</div>
        </div>
        <div :class="['stat-card', remaining < 0 ? 'danger' : '']">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ remaining.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsSelected') }}</div>
          <div class="stat-value">{{ selectedCount }}</div>
        </div>
      </div>

      <!-- Budget slider card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.setBudget') }}</h3>
        </div>
        <div class="budget-slider-section">
          <!--
            @change fires on slider release (mouseup/touchend), not on every tick.
            This preserves manual quantity edits the user has made while dragging.
            The live budget readout still updates every tick via v-model.
          -->
          <input
            type="range"
            min="0"
            :max="budgetMax"
            step="500"
            v-model.number="budget"
            @change="seedRecommendation"
            class="budget-range"
          />
          <p class="budget-readout">
            {{ t('restocking.availableBudget') }}:
            <strong>{{ currencySymbol }}{{ budget.toLocaleString() }}</strong>
          </p>
        </div>
      </div>

      <!-- Recommended restock table card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedRestock') }}</h3>
        </div>
        <div class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.projectedGap') }}</th>
                <th>{{ t('restocking.table.include') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <!-- Empty state: no items with positive forecasted gap -->
              <tr v-if="lineItems.length === 0">
                <td colspan="9" class="empty-state">{{ t('restocking.empty') }}</td>
              </tr>
              <tr v-for="li in lineItems" :key="li.sku">
                <td><strong>{{ li.sku }}</strong></td>
                <td>{{ li.name }}</td>
                <td>
                  <span :class="['badge', li.trend]">{{ t('trends.' + li.trend) }}</span>
                </td>
                <td>{{ currencySymbol }}{{ li.unit_cost.toLocaleString() }}</td>
                <td>+{{ li.gap }}</td>
                <td>
                  <input type="checkbox" v-model="li.selected" />
                </td>
                <td>
                  <!--
                    @change sanitizes NaN/negative to 0 and auto-unchecks when qty
                    drops to 0. v-model.number handles the numeric binding.
                  -->
                  <input
                    type="number"
                    min="0"
                    v-model.number="li.quantity"
                    @change="sanitizeQty(li)"
                    class="qty-input"
                  />
                </td>
                <td>{{ currencySymbol }}{{ (li.quantity * li.unit_cost).toLocaleString() }}</td>
                <td>{{ t('restocking.leadTimeDays', { days: li.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Order footer: budget summary + place order button -->
        <div class="order-footer">
          <div :class="['budget-summary', overBudget ? 'over-budget' : 'within-budget']">
            <span>
              {{ currencySymbol }}{{ selectedTotal.toLocaleString() }}
              / {{ currencySymbol }}{{ budget.toLocaleString() }}
            </span>
            <span v-if="overBudget" class="budget-status-label">{{ t('restocking.overBudget') }}</span>
            <span v-else class="budget-status-label">{{ t('restocking.withinBudget') }}</span>
          </div>
          <button
            :class="['po-button', 'create']"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>

      <!-- Success banner shown after a successful order placement -->
      <div v-if="successMessage" class="success-banner">
        {{ successMessage }}
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

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    // Raw state refs
    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(0)
    const lineItems = ref([])
    const submitting = ref(false)
    const successMessage = ref(null)

    // --- Computed ---

    /**
     * Maximum budget based on total cost of all items with a positive demand gap.
     * Falls back to 50000 if no forecastable items are present (e.g. backend not
     * yet updated with unit_cost field).
     */
    const budgetMax = computed(() => {
      const total = forecasts.value.reduce((sum, f) => {
        const gap = f.forecasted_demand - f.current_demand
        if (gap > 0 && f.unit_cost) {
          return sum + gap * f.unit_cost
        }
        return sum
      }, 0)
      const result = Math.ceil(total)
      return result > 0 && Number.isFinite(result) ? result : 50000
    })

    // Sum of (quantity * unit_cost) for all selected rows with qty > 0
    const selectedTotal = computed(() =>
      lineItems.value.reduce((sum, li) => {
        return li.selected && li.quantity > 0 ? sum + li.quantity * li.unit_cost : sum
      }, 0)
    )

    const overBudget = computed(() => selectedTotal.value > budget.value)

    // Worst-case lead time across all selected lines with qty > 0
    const orderLeadTimeDays = computed(() => {
      const selected = lineItems.value.filter(li => li.selected && li.quantity > 0)
      if (selected.length === 0) return 0
      return Math.max(...selected.map(li => li.lead_time_days))
    })

    const canPlaceOrder = computed(() =>
      lineItems.value.some(li => li.selected && li.quantity > 0) &&
      !overBudget.value &&
      !submitting.value
    )

    const selectedCount = computed(() =>
      lineItems.value.filter(li => li.selected && li.quantity > 0).length
    )

    const remaining = computed(() => budget.value - selectedTotal.value)

    // --- Methods ---

    /**
     * Rebuilds lineItems from forecasts using the current budget.
     * Prioritises items by trend (increasing first), then largest gap, then
     * lowest cost. Allocates budget greedily until exhausted.
     * Called once after data loads and again on slider release (@change).
     */
    const seedRecommendation = () => {
      const candidates = forecasts.value
        .map(f => ({ ...f, gap: f.forecasted_demand - f.current_demand }))
        .filter(c => c.gap > 0)

      const trendRank = { increasing: 0, stable: 1, decreasing: 2 }
      candidates.sort((a, b) =>
        (trendRank[a.trend] - trendRank[b.trend]) || (b.gap - a.gap) || (a.unit_cost - b.unit_cost)
      )

      let remaining = budget.value
      lineItems.value = candidates.map(c => {
        const qty = remaining < c.unit_cost
          ? 0
          : Math.min(c.gap, Math.floor(remaining / c.unit_cost))
        remaining -= qty * c.unit_cost
        return {
          sku: c.item_sku,
          name: c.item_name,
          unit_cost: c.unit_cost,
          lead_time_days: c.lead_time_days,
          trend: c.trend,
          gap: c.gap,
          selected: qty > 0,
          quantity: qty
        }
      })
    }

    /**
     * Clamps a line item's quantity to a non-negative integer.
     * Auto-unchecks the row if quantity drops to 0 so the budget summary
     * stays accurate without requiring an extra checkbox click.
     */
    const sanitizeQty = (li) => {
      li.quantity = Number.isFinite(li.quantity) && li.quantity > 0
        ? Math.floor(li.quantity)
        : 0
      if (li.quantity === 0) li.selected = false
    }

    const load = async () => {
      loading.value = true
      error.value = null
      try {
        forecasts.value = await api.getDemandForecasts()
        // budgetMax depends on forecasts, so compute initial budget after data arrives.
        // Use a mid-range value (up to $20k) so the initial recommendation is non-trivial.
        budget.value = Math.min(budgetMax.value, 20000)
        seedRecommendation()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    /**
     * Guards against double-submit via the submitting flag.
     * Maps selected lineItems to the order item shape expected by POST /api/orders.
     */
    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      submitting.value = true
      error.value = null
      successMessage.value = null
      try {
        const items = lineItems.value
          .filter(li => li.selected && li.quantity > 0)
          .map(li => ({
            sku: li.sku,
            name: li.name,
            quantity: li.quantity,
            unit_price: li.unit_cost
          }))
        const created = await api.createOrder({
          customer: 'Internal Restock',
          items,
          lead_time_days: orderLeadTimeDays.value
        })
        successMessage.value = t('restocking.success', { orderNumber: created.order_number })
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(load)

    return {
      t,
      currencySymbol,
      loading,
      error,
      budget,
      budgetMax,
      lineItems,
      submitting,
      successMessage,
      selectedTotal,
      overBudget,
      orderLeadTimeDays,
      canPlaceOrder,
      selectedCount,
      remaining,
      seedRecommendation,
      sanitizeQty,
      placeOrder
    }
  }
}
</script>

<style scoped>
/* Budget slider section */
.budget-slider-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.5rem 0;
}

.budget-range {
  width: 100%;
  accent-color: #3b82f6;
  height: 6px;
  cursor: pointer;
}

.budget-readout {
  font-size: 0.938rem;
  color: #475569;
}

.budget-readout strong {
  color: #0f172a;
}

/* Restock table: fixed layout to prevent column shifting */
.restock-table {
  table-layout: fixed;
  width: 100%;
}

.restock-table th:nth-child(1) { width: 110px; }  /* SKU */
.restock-table th:nth-child(2) { width: 180px; }  /* Item */
.restock-table th:nth-child(3) { width: 110px; }  /* Trend */
.restock-table th:nth-child(4) { width: 100px; }  /* Unit Cost */
.restock-table th:nth-child(5) { width: 110px; }  /* Projected Gap */
.restock-table th:nth-child(6) { width: 70px;  }  /* Include */
.restock-table th:nth-child(7) { width: 100px; }  /* Quantity */
.restock-table th:nth-child(8) { width: 110px; }  /* Line Total */
.restock-table th:nth-child(9) { width: 110px; }  /* Lead Time */

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-style: italic;
}

/* Inline quantity number input */
.qty-input {
  width: 70px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #0f172a;
}

.qty-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

/* Order footer row */
.order-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0 0.25rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 1rem;
  gap: 1rem;
}

.budget-summary {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.938rem;
  font-weight: 600;
}

.budget-summary.over-budget {
  color: #dc2626;
}

.budget-summary.within-budget {
  color: #059669;
}

.budget-status-label {
  font-weight: 400;
  font-size: 0.875rem;
}

/* Place Order button — mirrors Dashboard.vue .po-button.create */
.po-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.po-button.create {
  background: #3b82f6;
  color: white;
}

.po-button.create:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.po-button.create:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* Success banner */
.success-banner {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  font-size: 0.938rem;
  font-weight: 600;
  margin-top: 0.5rem;
}
</style>
