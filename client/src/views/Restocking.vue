<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p class="page-description">{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="joinedRows.length === 0" class="no-forecasts-notice">
      {{ t('restocking.noForecasts') }}
    </div>
    <div v-else>
      <!-- KPI tiles -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budgetUsed') }}</div>
          <div class="stat-value stat-value--sm">
            {{ formatCurrency(totalSelectedValue, currentCurrency) }}
            <span class="stat-of">/ {{ formatCurrency(budget, currentCurrency) }}</span>
          </div>
          <!-- Thin progress bar shows how much of the budget is consumed -->
          <div class="kpi-progress-bar">
            <div
              class="kpi-progress"
              :style="{ width: Math.min(100, budget > 0 ? (totalSelectedValue / budget) * 100 : 0) + '%' }"
            ></div>
          </div>
        </div>

        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsSelected') }}</div>
          <div class="stat-value">
            {{ recommendedItems.length }}
            <span class="stat-of">/ {{ joinedRows.length }}</span>
          </div>
        </div>

        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.unitsCovered') }}</div>
          <div class="stat-value">{{ totalUnitsCovered }}</div>
        </div>

        <div class="stat-card" :class="unmetCount > 0 ? 'warning' : 'success'">
          <div class="stat-label">{{ t('restocking.unmetItems') }}</div>
          <div class="stat-value">{{ unmetCount }}</div>
        </div>
      </div>

      <!-- Budget slider card -->
      <div class="card budget-card">
        <div class="budget-row">
          <label class="budget-label" for="budget-slider">{{ t('restocking.budget') }}</label>
          <span class="budget-display">{{ formatCurrency(budget, currentCurrency) }}</span>
        </div>
        <div class="slider-wrapper">
          <span class="slider-bound">{{ formatCurrency(sliderMin, currentCurrency) }}</span>
          <input
            id="budget-slider"
            type="range"
            class="budget-slider"
            :min="sliderMin"
            :max="sliderMax"
            :step="sliderStep"
            v-model.number="budget"
          />
          <span class="slider-bound">{{ formatCurrency(sliderMax, currentCurrency) }}</span>
        </div>
      </div>

      <!-- Recommendations table card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
        </div>

        <div v-if="recommendedItems.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="col-num">{{ t('restocking.table.quantity') }}</th>
                <th class="col-num">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="col-num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendedItems" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ translateProductName(rec.name) }}</td>
                <td>
                  <span :class="['badge', rec.trend]">
                    {{ t(`trends.${rec.trend}`) }}
                  </span>
                </td>
                <td class="col-num">{{ rec.quantity }}</td>
                <td class="col-num">{{ formatCurrency(rec.unit_cost, currentCurrency) }}</td>
                <td class="col-num"><strong>{{ formatCurrency(rec.line_total, currentCurrency) }}</strong></td>
                <td class="col-num">
                  <span class="lead-time-chip">
                    {{ t('orders.leadTimeDays', { days: rec.lead_time_days }) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card-footer">
          <button
            class="btn-place-order"
            :disabled="recommendedItems.length === 0 || placing"
            @click="confirmOpen = true"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Success / error toast -->
    <Transition name="toast">
      <div
        v-if="toast.visible"
        :class="['toast', toast.type === 'error' ? 'toast--error' : 'toast--success']"
      >
        {{ toast.message }}
      </div>
    </Transition>

    <!-- Confirmation modal -->
    <RestockOrderConfirmModal
      :is-open="confirmOpen"
      :items="recommendedItems"
      :total="totalSelectedValue"
      :budget="budget"
      :max-lead-time-days="maxLeadTimeDays"
      :placing="placing"
      @close="confirmOpen = false"
      @confirm="submitOrder"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'
import RestockOrderConfirmModal from '../components/RestockOrderConfirmModal.vue'

export default {
  name: 'Restocking',
  components: { RestockOrderConfirmModal },
  setup() {
    const router = useRouter()
    const { t, currentCurrency, translateProductName } = useI18n()

    // ─── raw data ────────────────────────────────────────────────────────────
    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const inventoryMap = ref(new Map()) // sku → inventory item (O(1) lookup)

    // ─── UI state ────────────────────────────────────────────────────────────
    const budget = ref(0)
    const confirmOpen = ref(false)
    const placing = ref(false)
    const toast = ref({ visible: false, message: '', type: 'success' })

    // ─── data loading ─────────────────────────────────────────────────────────
    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        forecasts.value = forecastsData

        // Build a Map keyed by SKU for O(1) joins in computed properties
        const map = new Map()
        for (const item of inventoryData) {
          map.set(item.sku, item)
        }
        inventoryMap.value = map

        // Initialize budget after data is available so sliderMax is known
        budget.value = initialBudget()
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    // ─── joined rows (demand forecast ∩ inventory) ────────────────────────────
    const joinedRows = computed(() => {
      return forecasts.value
        .filter(f => inventoryMap.value.has(f.item_sku))
        .map(f => {
          const inv = inventoryMap.value.get(f.item_sku)
          const gap = Math.max(0, f.forecasted_demand - inv.quantity_on_hand)
          return {
            sku: f.item_sku,
            name: f.item_name,
            category: inv.category,
            trend: f.trend,
            gap,
            unit_cost: inv.unit_cost,
            lead_time_days: inv.lead_time_days ?? 0,
            reorder_point: inv.reorder_point ?? 0,
            quantity_on_hand: inv.quantity_on_hand,
            // score drives greedy sort: highest demand-cost impact first
            score: gap * inv.unit_cost,
            max_qty: gap
          }
        })
        .filter(r => r.gap > 0)
    })

    // ─── slider parameters ────────────────────────────────────────────────────
    const sliderMin = 0

    const sliderMax = computed(() => {
      // Total cost to fully replenish all forecasted gaps — rounded up to nearest 1000
      // for a friendlier slider end value
      const raw = joinedRows.value.reduce(
        (sum, r) => sum + r.gap * r.unit_cost,
        0
      )
      return Math.ceil(raw / 1000) * 1000 || 1000
    })

    const sliderStep = computed(() => {
      // Step is 1 % of max, but at least $100 so small budgets don't feel sluggish
      return Math.max(100, sliderMax.value / 100)
    })

    // We need initialBudget as a function (called after data load when sliderMax is ready)
    const initialBudget = () => {
      // Start at a quarter of max: meaningful enough to show some picks
      // but leaves room to explore both directions on the slider.
      // Zero would show an empty table (unhelpful); half feels generous.
      return Math.round(sliderMax.value / 4)
    }

    // ─── recommendation algorithm ─────────────────────────────────────────────
    const recommendedItems = computed(() => {
      if (joinedRows.value.length === 0) return []

      // Step 1: sort by score desc, unit_cost asc (tiebreaker lets cheaper items in)
      const sorted = [...joinedRows.value].sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score
        return a.unit_cost - b.unit_cost
      })

      let remaining = budget.value
      const picked = []
      const skipped = []

      // Step 2: greedy full-fill pass
      for (const row of sorted) {
        const lineCost = row.max_qty * row.unit_cost
        if (lineCost <= remaining) {
          picked.push({
            sku: row.sku,
            name: row.name,
            quantity: row.max_qty,
            unit_cost: row.unit_cost,
            line_total: lineCost,
            lead_time_days: row.lead_time_days,
            trend: row.trend,
            gap: row.gap
          })
          remaining -= lineCost
        } else {
          skipped.push(row)
        }
      }

      // Step 3: tail-fit branch
      // After the greedy loop some budget may remain but no item's full quantity
      // fits within it. Rather than waste that remainder, we look for an item that
      // (a) is currently below its reorder_point (most urgent), (b) has the
      // lowest unit_cost among skipped items, and (c) can accept at least 1 unit.
      // A partial fill is acceptable here because keeping even a small quantity
      // of an understocked item beats leaving money on the table entirely.
      if (skipped.length > 0 && remaining > 0) {
        // Candidate: below reorder_point with lowest unit_cost that still fits at qty >= 1
        const candidate = skipped
          .filter(r => r.quantity_on_hand < r.reorder_point && r.unit_cost <= remaining)
          .sort((a, b) => a.unit_cost - b.unit_cost)[0]

        if (candidate) {
          const qty = Math.min(Math.floor(remaining / candidate.unit_cost), candidate.gap)
          if (qty > 0) {
            picked.push({
              sku: candidate.sku,
              name: candidate.name,
              quantity: qty,
              unit_cost: candidate.unit_cost,
              line_total: qty * candidate.unit_cost,
              lead_time_days: candidate.lead_time_days,
              trend: candidate.trend,
              gap: candidate.gap
            })
          }
        }
      }

      return picked
    })

    // ─── KPI derived values ───────────────────────────────────────────────────
    const totalSelectedValue = computed(() =>
      recommendedItems.value.reduce((sum, r) => sum + r.line_total, 0)
    )

    const totalUnitsCovered = computed(() =>
      recommendedItems.value.reduce((sum, r) => sum + r.quantity, 0)
    )

    const unmetCount = computed(() => {
      const pickedSkus = new Set(recommendedItems.value.map(r => r.sku))
      return joinedRows.value.filter(r => !pickedSkus.has(r.sku)).length
    })

    const maxLeadTimeDays = computed(() => {
      if (recommendedItems.value.length === 0) return 0
      return Math.max(...recommendedItems.value.map(r => r.lead_time_days))
    })

    // ─── submit flow ──────────────────────────────────────────────────────────
    const showToast = (message, type = 'success', durationMs = 3500) => {
      toast.value = { visible: true, message, type }
      setTimeout(() => { toast.value.visible = false }, durationMs)
    }

    const submitOrder = async () => {
      placing.value = true
      try {
        // Strip display-only fields (line_total, trend, gap) from the payload.
        // The backend Pydantic model SubmittedOrderItem only accepts
        // {sku, name, quantity, unit_cost, lead_time_days} — extra keys cause 422.
        const items = recommendedItems.value.map(({ sku, name, quantity, unit_cost, lead_time_days }) => ({
          sku, name, quantity, unit_cost, lead_time_days
        }))

        await api.createSubmittedOrder({ items, budget: budget.value })

        confirmOpen.value = false
        showToast(t('restocking.successToast'))

        // Reset budget to initial value — the empty recommendations table
        // acts as a visual "cart cleared" signal after a successful submit.
        budget.value = initialBudget()

        // Brief pause so user can read the toast, then navigate to orders
        setTimeout(() => { router.push('/orders') }, 800)
      } catch (err) {
        console.error('Failed to submit restock order:', err)
        showToast(t('restocking.submitFailed'), 'error')
        // Leave modal open so the user can retry without losing their selection
      } finally {
        placing.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      loading,
      error,
      budget,
      sliderMin,
      sliderMax,
      sliderStep,
      joinedRows,
      recommendedItems,
      totalSelectedValue,
      totalUnitsCovered,
      unmetCount,
      maxLeadTimeDays,
      confirmOpen,
      placing,
      toast,
      submitOrder
    }
  }
}
</script>

<style scoped>
.page-description {
  color: #64748b;
  font-size: 0.938rem;
}

/* "No forecasts" notice — muted card, not an error */
.no-forecasts-notice {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
  text-align: center;
}

/* KPI stat card tweaks */
.stat-value--sm {
  font-size: 1.5rem;
}

.stat-of {
  font-size: 0.875rem;
  font-weight: 400;
  color: #94a3b8;
  margin-left: 0.25rem;
}

/* Progress bar inside budget KPI tile */
.kpi-progress-bar {
  margin-top: 0.75rem;
  height: 4px;
  background: #e2e8f0;
  border-radius: 99px;
  overflow: hidden;
}

.kpi-progress {
  height: 100%;
  background: #1e40af;
  border-radius: 99px;
  transition: width 0.3s ease;
}

/* Budget card */
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-row {
  display: flex;
  align-items: baseline;
  gap: 1rem;
  margin-bottom: 0.875rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-display {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 99px;
  cursor: pointer;
  accent-color: #1e40af; /* modern browsers: styles both thumb and track fill */
  outline: none;
}

.slider-bound {
  font-size: 0.813rem;
  color: #94a3b8;
  white-space: nowrap;
  min-width: 3.5rem;
  text-align: center;
}

/* Recommendations table */
.col-num {
  text-align: right;
}

.lead-time-chip {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  font-family: 'Monaco', 'Courier New', monospace;
}

.empty-state {
  padding: 2.5rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 1rem;
  margin-top: 0.5rem;
  border-top: 1px solid #e2e8f0;
}

.btn-place-order {
  padding: 0.625rem 1.5rem;
  background: #1e40af;
  border: 1px solid #1e3a8a;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-place-order:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-place-order:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Toast notification — anchored to top-right of main content area */
.toast {
  position: fixed;
  top: 1.5rem;
  right: 2rem;
  z-index: 3000;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  max-width: 360px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast--success {
  background: #0f172a;
  color: #f8fafc;
  border: 1px solid #1e293b;
}

.toast--error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

/* Toast enter/leave transitions */
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-0.5rem);
}
</style>
