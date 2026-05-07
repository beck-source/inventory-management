<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t("restocking.title") }}</h2>
      <p>{{ t("restocking.description") }}</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t("restocking.budgetLabel") }}</h3>
      </div>
      <div class="budget-controls">
        <div class="slider-row">
          <label class="slider-label">{{ t("restocking.budget") }}</label>
          <input
            type="range"
            min="0"
            max="500000"
            step="5000"
            v-model.number="budget"
            class="budget-slider"
          />
          <span class="budget-display">{{ formattedBudget }}</span>
        </div>
        <div class="budget-stats">
          <div class="budget-stat">
            <span class="budget-stat-label">{{
              t("restocking.cartTotal")
            }}</span>
            <span class="budget-stat-value"
              >{{ currencySymbol }}{{ cartTotal.toLocaleString() }}</span
            >
          </div>
          <div
            class="budget-stat"
            :class="{ 'over-budget': cartTotal > budget }"
          >
            <span class="budget-stat-label">{{
              t("restocking.remaining")
            }}</span>
            <span class="budget-stat-value"
              >{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</span
            >
          </div>
          <div class="budget-stat">
            <span class="budget-stat-label">{{
              t("restocking.itemsSelected")
            }}</span>
            <span class="budget-stat-value">{{ cart.length }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          {{ t("restocking.recommendations") }}
          <span class="badge info count-badge">{{
            recommendations.length
          }}</span>
        </h3>
      </div>

      <div v-if="loading" class="loading">{{ t("common.loading") }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="recommendations.length === 0" class="empty-state">
        {{ t("restocking.noRecommendations") }}
      </div>
      <div v-else>
        <div
          v-for="group in groupedRecommendations"
          :key="group.warehouse"
          class="warehouse-group"
        >
          <div class="warehouse-header">
            <span class="warehouse-name">{{ group.warehouse }}</span>
            <span v-if="group.leadTimeDays" class="badge info">
              {{ t("restocking.warehouseEta", { days: group.leadTimeDays }) }}
            </span>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t("restocking.table.include") }}</th>
                  <th>{{ t("restocking.table.sku") }}</th>
                  <th>{{ t("restocking.table.item") }}</th>
                  <th>{{ t("restocking.table.urgency") }}</th>
                  <th>{{ t("restocking.table.onHand") }}</th>
                  <th>{{ t("restocking.table.reorderPoint") }}</th>
                  <th>{{ t("restocking.table.forecast") }}</th>
                  <th>{{ t("restocking.table.qty") }}</th>
                  <th>{{ t("restocking.table.unitCost") }}</th>
                  <th>{{ t("restocking.table.lineTotal") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="rec in group.items"
                  :key="rec.sku"
                  :class="{ 'row-excluded': !includedSkus.has(rec.sku) }"
                >
                  <td>
                    <input
                      type="checkbox"
                      :checked="includedSkus.has(rec.sku)"
                      @change="toggleInclude(rec.sku)"
                    />
                  </td>
                  <td>
                    <code>{{ rec.sku }}</code>
                  </td>
                  <td>{{ rec.name }}</td>
                  <td>
                    <span :class="['badge', urgencyClass(rec.urgency)]">
                      {{ t(`restocking.urgency.${rec.urgency}`) }}
                    </span>
                  </td>
                  <td>{{ rec.quantity_on_hand }}</td>
                  <td>{{ rec.reorder_point }}</td>
                  <td>{{ rec.forecasted_demand }}</td>
                  <td>
                    <input
                      type="number"
                      min="1"
                      :value="effectiveQty(rec)"
                      @input="updateQty(rec.sku, $event.target.value)"
                      class="qty-input"
                    />
                  </td>
                  <td>
                    {{ currencySymbol }}{{ rec.unit_cost.toLocaleString() }}
                  </td>
                  <td>
                    <strong>
                      {{ currencySymbol
                      }}{{
                        (effectiveQty(rec) * rec.unit_cost).toLocaleString()
                      }}
                    </strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card-footer">
          <div v-if="submitError" class="error">{{ submitError }}</div>
          <div v-if="cartTotal > budget" class="error">
            {{ t("restocking.cartTooLarge") }}
          </div>
          <div class="footer-actions">
            <button
              class="btn-primary"
              :disabled="!canPlaceOrder || submitting"
              @click="placeOrder"
            >
              {{
                submitting
                  ? t("restocking.placing")
                  : t("restocking.placeOrder")
              }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { useI18n } from "../composables/useI18n";

// Per-warehouse lead times in days — each warehouse gets its own ETA badge
const LEAD_TIMES = {
  "San Francisco": 7,
  London: 14,
  Tokyo: 21,
};

export default {
  name: "Restocking",
  setup() {
    const { t, currentCurrency } = useI18n();
    const router = useRouter();
    const budget = ref(100000);
    const recommendations = ref([]);
    const includedSkus = ref(new Set());
    const overrideQty = ref({});
    const loading = ref(false);
    const error = ref(null);
    const submitting = ref(false);
    const submitError = ref(null);

    const currencySymbol = computed(() => {
      return currentCurrency.value === "JPY" ? "¥" : "$";
    });

    const formattedBudget = computed(() => {
      return `${currencySymbol.value}${budget.value.toLocaleString()}`;
    });

    const effectiveQty = (rec) => {
      return overrideQty.value[rec.sku] !== undefined
        ? overrideQty.value[rec.sku]
        : rec.recommended_quantity;
    };

    const updateQty = (sku, value) => {
      const parsed = parseInt(value, 10);
      if (!isNaN(parsed) && parsed >= 1) {
        overrideQty.value = { ...overrideQty.value, [sku]: parsed };
      }
    };

    const toggleInclude = (sku) => {
      const next = new Set(includedSkus.value);
      if (next.has(sku)) {
        next.delete(sku);
      } else {
        next.add(sku);
      }
      includedSkus.value = next;
    };

    // Group recommendations by warehouse so each warehouse can show its own ETA
    const groupedRecommendations = computed(() => {
      const map = {};
      for (const rec of recommendations.value) {
        if (!map[rec.warehouse]) {
          map[rec.warehouse] = {
            warehouse: rec.warehouse,
            leadTimeDays: LEAD_TIMES[rec.warehouse] ?? null,
            items: [],
          };
        }
        map[rec.warehouse].items.push(rec);
      }
      return Object.values(map);
    });

    const cart = computed(() => {
      return recommendations.value.filter((rec) =>
        includedSkus.value.has(rec.sku),
      );
    });

    const cartTotal = computed(() => {
      return cart.value.reduce(
        (sum, rec) => sum + effectiveQty(rec) * rec.unit_cost,
        0,
      );
    });

    const remainingBudget = computed(() => budget.value - cartTotal.value);

    const canPlaceOrder = computed(
      () => cart.value.length > 0 && cartTotal.value <= budget.value,
    );

    const urgencyClass = (urgency) => {
      const map = { urgent: "danger", rising: "warning", stable: "info" };
      return map[urgency] || "info";
    };

    const loadRecommendations = async () => {
      loading.value = true;
      error.value = null;
      try {
        const data = await api.getRestockingRecommendations(budget.value);
        recommendations.value = data;
        // Default-check every returned SKU; also clear stale user overrides
        includedSkus.value = new Set(data.map((r) => r.sku));
        overrideQty.value = {};
      } catch (err) {
        error.value = "Failed to load recommendations";
        console.error(err);
      } finally {
        loading.value = false;
      }
    };

    // Debounce budget-driven refetches so the slider doesn't hammer the API on every tick
    let debounceTimer = null;
    watch(budget, () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadRecommendations();
      }, 150);
    });

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return;
      submitting.value = true;
      submitError.value = null;
      try {
        const items = cart.value.map((rec) => ({
          sku: rec.sku,
          quantity: effectiveQty(rec),
        }));
        await api.submitRestockingOrder(items, budget.value);
        router.push("/orders");
      } catch (err) {
        submitError.value =
          err?.response?.data?.detail || "Failed to submit order";
        console.error(err);
      } finally {
        submitting.value = false;
      }
    };

    onMounted(() => loadRecommendations());

    return {
      t,
      budget,
      recommendations,
      includedSkus,
      loading,
      error,
      submitting,
      submitError,
      currencySymbol,
      formattedBudget,
      groupedRecommendations,
      cart,
      cartTotal,
      remainingBudget,
      canPlaceOrder,
      effectiveQty,
      updateQty,
      toggleInclude,
      urgencyClass,
      placeOrder,
    };
  },
};
</script>

<style scoped>
.budget-controls {
  padding: 0.5rem 0;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.slider-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  white-space: nowrap;
  min-width: 80px;
}

.budget-slider {
  flex: 1;
  accent-color: #2563eb;
  height: 6px;
  cursor: pointer;
}

.budget-display {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 120px;
  text-align: right;
}

.budget-stats {
  display: flex;
  gap: 2rem;
}

.budget-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.budget-stat.over-budget .budget-stat-value {
  color: #dc2626;
}

.budget-stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.count-badge {
  margin-left: 0.5rem;
  vertical-align: middle;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.warehouse-group {
  margin-bottom: 1.5rem;
}

.warehouse-group:last-of-type {
  margin-bottom: 0;
}

.warehouse-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.warehouse-name {
  font-size: 0.938rem;
  font-weight: 700;
  color: #0f172a;
}

.qty-input {
  width: 72px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #0f172a;
  text-align: right;
}

.qty-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}

.row-excluded td {
  opacity: 0.45;
}

.row-excluded td:first-child {
  opacity: 1;
}

.card-footer {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

.btn-primary {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
</style>
