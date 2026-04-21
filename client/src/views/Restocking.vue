<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('restocking.loadingCandidates') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Summary stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.candidates') }}</div>
          <div class="stat-value">{{ candidates.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.maxPossibleSpend') }}</div>
          <div class="stat-value stat-value--currency">{{ formatCurrency(sliderMax) }}</div>
        </div>
        <div class="stat-card" :class="{ danger: overBudget }">
          <div class="stat-label">{{ t('restocking.selectedTotal') }}</div>
          <div class="stat-value stat-value--currency" :class="{ 'over-budget-text': overBudget }">
            {{ formatCurrency(selectedTotal) }}
          </div>
        </div>
      </div>

      <!-- Budget card -->
      <div class="card">
        <div class="budget-header">
          <span class="budget-label">{{ t('restocking.budget') }}</span>
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="range-wrapper">
          <input
            type="range"
            :min="0"
            :max="sliderMax"
            :step="sliderStep"
            v-model.number="budget"
            class="budget-range"
          />
        </div>
        <div class="budget-bar">
          <div
            class="budget-fill"
            :class="{ 'over-budget': overBudget }"
            :style="{ width: Math.min((selectedTotal / (budget || 1)) * 100, 100) + '%' }"
          ></div>
        </div>
        <div class="budget-info">
          <span>
            {{ t('restocking.selectedOf', { selected: formatCurrency(selectedTotal), budget: formatCurrency(budget) }) }}
            &middot; {{ selectedCandidates.length }} {{ t('common.items') }}
          </span>
          <span v-if="overBudget" class="over-budget-warning">
            &#9888; {{ t('restocking.overBudget', { amount: formatCurrency(selectedTotal - budget) }) }}
          </span>
        </div>
      </div>

      <!-- Success message -->
      <div v-if="successMessage" class="inline-success">{{ successMessage }}</div>

      <!-- Candidates card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.restockingCandidates') }}</h3>
          <button class="btn-secondary btn-sm" @click="resetAutoSelect">{{ t('restocking.resetAutoSelect') }}</button>
        </div>

        <div v-if="candidates.length === 0" class="empty-state">
          {{ t('restocking.noItems') }}
        </div>
        <div v-else class="table-container">
          <table class="candidates-table">
            <thead>
              <tr>
                <th class="col-check"></th>
                <th class="col-sku">SKU</th>
                <th class="col-name">{{ t('restocking.table.item') }}</th>
                <th class="col-warehouse">{{ t('restocking.table.warehouse') }}</th>
                <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                <th class="col-num">{{ t('restocking.table.current') }}</th>
                <th class="col-num">{{ t('restocking.table.forecast') }}</th>
                <th class="col-num">{{ t('restocking.table.shortfall') }}</th>
                <th class="col-num">{{ t('restocking.table.qtyToOrder') }}</th>
                <th class="col-cost">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-cost">{{ t('restocking.table.subtotal') }}</th>
                <th class="col-lead">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in candidates"
                :key="candidateKey(c)"
                :class="['candidate-row', { selected: isSelected(c) }]"
                @click="toggle(c)"
              >
                <td class="col-check">
                  <input
                    type="checkbox"
                    :checked="isSelected(c)"
                    @click.stop="toggle(c)"
                  />
                </td>
                <td class="col-sku"><code>{{ c.sku }}</code></td>
                <td class="col-name">{{ c.name }}</td>
                <td class="col-warehouse">{{ c.warehouse }}</td>
                <td class="col-trend">
                  <span :class="['badge', c.trend]">{{ c.trend }}</span>
                </td>
                <td class="col-num">{{ c.quantity_on_hand }}</td>
                <td class="col-num">{{ c.forecasted_demand }}</td>
                <td class="col-num">{{ c.shortfall }}</td>
                <td class="col-num">{{ c.recommended_qty }}</td>
                <td class="col-cost">{{ formatCurrency(c.unit_cost) }}</td>
                <td class="col-cost">{{ formatCurrency(c.recommended_qty * c.unit_cost) }}</td>
                <td class="col-lead">{{ c.lead_time_days }} {{ t('restocking.days') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Action row -->
      <div class="action-row">
        <button class="btn-secondary" @click="router.push('/')">{{ t('restocking.cancel') }}</button>
        <button
          class="btn-primary"
          :disabled="selectedCandidates.length === 0 || overBudget || submitting"
          @click="submitOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

const router = useRouter()
const { getCurrentFilters, selectedLocation, selectedCategory } = useFilters()
const { t, currentCurrency } = useI18n()

// State
const candidates = ref([])
const selectedSkus = ref(new Set())
const budget = ref(0)
const userOverride = ref(false)
const loading = ref(false)
const error = ref(null)
const submitting = ref(false)
const successMessage = ref('')

// Helpers
const candidateKey = (c) => `${c.sku}__${c.warehouse}`

const isSelected = (c) => selectedSkus.value.has(candidateKey(c))

const toggle = (c) => {
  const key = candidateKey(c)
  const next = new Set(selectedSkus.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  selectedSkus.value = next
  userOverride.value = true
}

// Computed
const sliderMax = computed(() => {
  const total = candidates.value.reduce((sum, c) => sum + c.estimated_cost, 0)
  return Math.max(1000, Math.ceil(total / 1000) * 1000)
})

const sliderStep = computed(() => {
  return Math.max(100, Math.round(sliderMax.value / 200))
})

const selectedCandidates = computed(() => {
  return candidates.value.filter(c => isSelected(c))
})

const selectedTotal = computed(() => {
  return selectedCandidates.value.reduce((sum, c) => sum + c.recommended_qty * c.unit_cost, 0)
})

const overBudget = computed(() => selectedTotal.value > budget.value)

// Auto-select via greedy fill
const autoSelect = () => {
  let remaining = budget.value
  const next = new Set()
  for (const c of candidates.value) {
    if (remaining >= c.estimated_cost) {
      next.add(candidateKey(c))
      remaining -= c.estimated_cost
    }
  }
  selectedSkus.value = next
}

const resetAutoSelect = () => {
  userOverride.value = false
  autoSelect()
}

// Load candidates
const loadCandidates = async () => {
  loading.value = true
  error.value = null
  try {
    candidates.value = await api.getRestockingCandidates(getCurrentFilters())
    userOverride.value = false
    // Set budget to max of all candidates and then auto-select
    budget.value = sliderMax.value
    autoSelect()
  } catch (err) {
    error.value = 'Failed to load restocking candidates'
    console.error(err)
  } finally {
    loading.value = false
  }
}

// Watchers
watch(budget, () => {
  if (!userOverride.value) autoSelect()
})

watch([selectedLocation, selectedCategory], () => {
  loadCandidates()
})

// Submit order
const submitOrder = async () => {
  submitting.value = true
  error.value = null
  try {
    const items = selectedCandidates.value.map(c => ({
      sku: c.sku,
      name: c.name,
      quantity: c.recommended_qty,
      unit_cost: c.unit_cost,
      lead_time_days: c.lead_time_days,
      subtotal: Math.round(c.recommended_qty * c.unit_cost)
    }))
    const response = await api.submitRestockingOrder({ items })
    successMessage.value = `Order ${response.id} submitted. Redirecting to Orders...`
    setTimeout(() => {
      router.push('/orders')
    }, 800)
  } catch (err) {
    error.value = 'Failed to submit restocking order: ' + (err.message || 'Unknown error')
    console.error(err)
  } finally {
    submitting.value = false
  }
}

// Currency format helper
const formatCurrency = (value) => {
  return Number(value).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  })
}

onMounted(loadCandidates)
</script>

<style scoped>
.restocking {
  /* inherits main-content padding */
}

/* Stat value override for currency (smaller font so it fits) */
.stat-value--currency {
  font-size: 1.5rem;
}

.over-budget-text {
  color: var(--color-danger);
}

/* Budget card internals */
.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
}

.range-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.budget-range {
  flex: 1;
  accent-color: var(--color-accent);
  cursor: pointer;
}

/* Budget progress bar */
.budget-bar {
  height: 12px;
  background: var(--color-surface-alt);
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-bottom: var(--space-3);
}

.budget-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: var(--radius-sm);
  transition: width 200ms ease, background 200ms ease;
}

.budget-fill.over-budget {
  background: var(--color-danger);
}

.budget-info {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.over-budget-warning {
  color: var(--color-danger);
  font-weight: 600;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

/* Candidates table */
.candidates-table {
  table-layout: auto;
  width: 100%;
}

.col-check { width: 36px; }
.col-sku { width: 110px; }
.col-name { min-width: 160px; }
.col-warehouse { width: 130px; }
.col-trend { width: 100px; }
.col-num { width: 90px; text-align: right; }
.col-cost { width: 100px; text-align: right; }
.col-lead { width: 90px; text-align: right; }

.candidate-row {
  cursor: pointer;
}

.candidate-row.selected {
  background: var(--color-accent-bg);
}

.candidate-row.selected:hover {
  background: var(--color-info-bg);
}

code {
  font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
  font-size: 0.8rem;
  background: var(--color-surface-alt);
  padding: 2px 5px;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
}

/* Buttons */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease, box-shadow 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
  box-shadow: var(--shadow-md);
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  background: transparent;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--color-surface-alt);
  color: var(--color-text);
}

.btn-sm {
  padding: var(--space-1) var(--space-3);
  font-size: 0.813rem;
}

/* Action row */
.action-row {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

/* Inline success */
.inline-success {
  background: var(--color-success-bg);
  color: #065f46;
  border: 1px solid var(--color-success-bg);
  border-radius: var(--radius-sm);
  padding: var(--space-3) var(--space-4);
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: var(--space-4);
}
</style>
