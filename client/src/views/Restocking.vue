<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t("restocking.title") }}</h2>
      <p>{{ t("restocking.description") }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t("common.loading") }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="submittedOrder" class="success-banner">
        <div class="success-content">
          <p>{{ successMessage }}</p>
          <router-link to="/orders" class="view-orders-link">
            {{ t("restocking.viewInOrders") }}
          </router-link>
        </div>
        <button
          type="button"
          class="dismiss-btn"
          @click="submittedOrder = null"
        >
          &times;
        </button>
      </div>

      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t("restocking.budgetLabel") }}</h3>
        </div>
        <p class="budget-hint">{{ t("restocking.budgetHint") }}</p>
        <div class="budget-slider-row">
          <input
            type="range"
            min="0"
            :max="maxBudget"
            step="50"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-value">{{ formatCurrency(budget) }}</div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">
            {{ t("restocking.stats.recommendedItems") }}
          </div>
          <div class="stat-value">{{ selectedItems.length }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t("restocking.stats.totalCost") }}</div>
          <div class="stat-value">
            {{ formatCurrencyWithDecimals(totalSelectedCost) }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            {{ t("restocking.stats.remainingBudget") }}
          </div>
          <div class="stat-value">
            {{ formatCurrencyWithDecimals(remainingBudget) }}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t("restocking.recommendationsTitle") }} ({{
              recommendations.length
            }})
          </h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t("restocking.noRecommendations") }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-checkbox"></th>
                <th>{{ t("restocking.table.sku") }}</th>
                <th>{{ t("restocking.table.itemName") }}</th>
                <th>{{ t("restocking.table.trend") }}</th>
                <th>{{ t("restocking.table.currentDemand") }}</th>
                <th>{{ t("restocking.table.forecastedDemand") }}</th>
                <th>{{ t("restocking.table.suggestedQuantity") }}</th>
                <th>{{ t("restocking.table.unitCost") }}</th>
                <th>{{ t("restocking.table.subtotal") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.id">
                <td class="col-checkbox">
                  <input type="checkbox" v-model="included[item.item_sku]" />
                </td>
                <td>
                  <strong>{{ item.item_sku }}</strong>
                </td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.current_demand }}</td>
                <td>{{ item.forecasted_demand }}</td>
                <td>
                  <strong>{{ item.quantity }}</strong>
                </td>
                <td>{{ formatCurrencyWithDecimals(item.unit_cost) }}</td>
                <td>{{ formatCurrencyWithDecimals(item.subtotal) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="validationMessage" class="error">{{ validationMessage }}</div>

      <button
        type="button"
        class="place-order-btn"
        :disabled="selectedItems.length === 0 || submitting"
        @click="handlePlaceOrder"
      >
        {{
          submitting ? t("restocking.placingOrder") : t("restocking.placeOrder")
        }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { api } from "../api";
import { useI18n } from "../composables/useI18n";
import {
  formatCurrency as formatCurrencyUtil,
  formatCurrencyWithDecimals as formatCurrencyWithDecimalsUtil,
} from "../utils/currency";

const TREND_PRIORITY = {
  increasing: 3,
  stable: 2,
  decreasing: 1,
};

export default {
  name: "Restocking",
  setup() {
    const { t, currentCurrency } = useI18n();

    const loading = ref(true);
    const error = ref(null);
    const allForecasts = ref([]);

    const budget = ref(0);
    const included = reactive({});

    const submitting = ref(false);
    const submitError = ref(null);
    const submittedOrder = ref(null);
    const validationMessage = ref(null);

    const formatCurrency = (amount) =>
      formatCurrencyUtil(amount, currentCurrency.value);
    const formatCurrencyWithDecimals = (amount) =>
      formatCurrencyWithDecimalsUtil(amount, currentCurrency.value, 2);

    // Maximum cost to fully satisfy every actionable recommendation
    const maxBudget = computed(() => {
      const raw = allForecasts.value.reduce((sum, f) => {
        const gap = f.forecasted_demand - f.current_demand;
        return gap > 0 ? sum + gap * f.unit_cost : sum;
      }, 0);
      return Math.ceil(raw / 100) * 100;
    });

    const recommendations = computed(() => {
      const candidates = allForecasts.value
        .map((f) => ({
          ...f,
          gap: Math.max(f.forecasted_demand - f.current_demand, 0),
        }))
        .filter((f) => f.gap > 0)
        .sort((a, b) => {
          const priorityDiff =
            (TREND_PRIORITY[b.trend] || 0) - (TREND_PRIORITY[a.trend] || 0);
          if (priorityDiff !== 0) return priorityDiff;
          return b.gap - a.gap;
        });

      const result = [];
      let remaining = budget.value;

      for (const candidate of candidates) {
        const cost = candidate.gap * candidate.unit_cost;
        if (cost <= remaining) {
          result.push({
            ...candidate,
            quantity: candidate.gap,
            subtotal: cost,
          });
          remaining -= cost;
        }
      }

      return result;
    });

    // Backfill inclusion state for newly seen SKUs without resetting user choices
    watch(
      recommendations,
      (newRecs) => {
        newRecs.forEach((item) => {
          if (!(item.item_sku in included)) {
            included[item.item_sku] = true;
          }
        });
      },
      { immediate: true },
    );

    const selectedItems = computed(() => {
      return recommendations.value.filter(
        (item) => included[item.item_sku] !== false,
      );
    });

    const totalSelectedCost = computed(() => {
      return selectedItems.value.reduce((sum, item) => sum + item.subtotal, 0);
    });

    const remainingBudget = computed(
      () => budget.value - totalSelectedCost.value,
    );

    const successMessage = computed(() => {
      if (!submittedOrder.value) return "";
      return t("restocking.successMessage", {
        orderNumber: submittedOrder.value.order_number,
        total: formatCurrency(submittedOrder.value.total_cost),
        days: submittedOrder.value.lead_time_days,
      });
    });

    const loadForecasts = async () => {
      try {
        loading.value = true;
        error.value = null;
        allForecasts.value = await api.getDemandForecasts();
        // Initialize budget to roughly half of the max once data is loaded
        budget.value = Math.round(maxBudget.value / 2 / 50) * 50;
      } catch (err) {
        error.value = "Failed to load demand forecasts: " + err.message;
      } finally {
        loading.value = false;
      }
    };

    const handlePlaceOrder = async () => {
      if (selectedItems.value.length === 0) {
        validationMessage.value = t("restocking.validationNoItems");
        return;
      }

      validationMessage.value = null;
      submitError.value = null;
      submitting.value = true;

      try {
        const payload = {
          budget: budget.value,
          items: selectedItems.value.map((item) => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            quantity: item.quantity,
            unit_cost: item.unit_cost,
          })),
        };
        submittedOrder.value = await api.createRestockOrder(payload);
      } catch (err) {
        submitError.value = "Failed to place restock order: " + err.message;
      } finally {
        submitting.value = false;
      }
    };

    onMounted(loadForecasts);

    return {
      t,
      loading,
      error,
      budget,
      maxBudget,
      included,
      recommendations,
      selectedItems,
      totalSelectedCost,
      remainingBudget,
      submitting,
      submitError,
      submittedOrder,
      successMessage,
      validationMessage,
      handlePlaceOrder,
      formatCurrency,
      formatCurrencyWithDecimals,
    };
  },
};
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-hint {
  color: #64748b;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.budget-slider {
  flex: 1;
  accent-color: #3b82f6;
  height: 6px;
  cursor: pointer;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 110px;
  text-align: right;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.col-checkbox {
  width: 40px;
  text-align: center;
}

.col-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.place-order-btn {
  display: inline-block;
  padding: 0.75rem 1.75rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
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

.success-banner {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
}

.success-content p {
  margin-bottom: 0.375rem;
  font-size: 0.938rem;
}

.view-orders-link {
  color: #047857;
  font-weight: 600;
  text-decoration: underline;
}

.dismiss-btn {
  background: transparent;
  border: none;
  color: #065f46;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}
</style>
