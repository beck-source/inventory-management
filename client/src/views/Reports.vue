<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t("reports.title") }}</h2>
      <p>{{ t("reports.description") }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t("common.loading") }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="isEmpty" class="empty-state">{{ t("reports.noData") }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.quarterly.title") }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t("reports.quarterly.quarter") }}</th>
                <th>{{ t("reports.quarterly.totalOrders") }}</th>
                <th>{{ t("reports.quarterly.totalRevenue") }}</th>
                <th>{{ t("reports.quarterly.avgOrderValue") }}</th>
                <th>{{ t("reports.quarterly.fulfillmentRate") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td>
                  <strong>{{ q.quarter }}</strong>
                </td>
                <td>{{ formatCount(q.total_orders) }}</td>
                <td>{{ formatMoney(q.total_revenue) }}</td>
                <td>{{ formatMoney(q.avg_order_value) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.monthlyTrend.title") }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="m in monthlyData" :key="m.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(m.revenue) + 'px' }"
                  :title="formatMoney(m.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(m.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.monthOverMonth.title") }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t("reports.monthOverMonth.month") }}</th>
                <th>{{ t("reports.monthOverMonth.orders") }}</th>
                <th>{{ t("reports.monthOverMonth.revenue") }}</th>
                <th>{{ t("reports.monthOverMonth.change") }}</th>
                <th>{{ t("reports.monthOverMonth.growthRate") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(m, index) in monthlyData" :key="m.month">
                <td>
                  <strong>{{ formatMonth(m.month) }}</strong>
                </td>
                <td>{{ formatCount(m.order_count) }}</td>
                <td>{{ formatMoney(m.revenue) }}</td>
                <td>
                  <span
                    v-if="index > 0"
                    :class="
                      getChangeClass(m.revenue, monthlyData[index - 1].revenue)
                    "
                  >
                    {{
                      getChangeValue(m.revenue, monthlyData[index - 1].revenue)
                    }}
                  </span>
                  <span v-else>—</span>
                </td>
                <td>
                  <span
                    v-if="index > 0"
                    :class="
                      getChangeClass(m.revenue, monthlyData[index - 1].revenue)
                    "
                  >
                    {{
                      getGrowthRate(m.revenue, monthlyData[index - 1].revenue)
                    }}
                  </span>
                  <span v-else>—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t("reports.stats.totalRevenueYTD") }}</div>
          <div class="stat-value">{{ formatMoney(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            {{ t("reports.stats.avgMonthlyRevenue") }}
          </div>
          <div class="stat-value">{{ formatMoney(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t("reports.stats.totalOrdersYTD") }}</div>
          <div class="stat-value">{{ formatCount(totalOrders) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t("reports.stats.bestQuarter") }}</div>
          <div class="stat-value">{{ bestQuarter || "—" }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { api } from "../api";
import { useI18n } from "../composables/useI18n";
import { useFilters } from "../composables/useFilters";
import { formatCurrency } from "../utils/currency";

const { t, currentCurrency } = useI18n();
const {
  selectedPeriod,
  selectedLocation,
  selectedCategory,
  selectedStatus,
  getCurrentFilters,
} = useFilters();

const loading = ref(true);
const error = ref(null);
const quarterlyData = ref([]);
const monthlyData = ref([]);

// Abbreviated month keys, indexed by (month number - 1), for localized labels.
const MONTH_KEYS = [
  "jan",
  "feb",
  "mar",
  "apr",
  "may",
  "jun",
  "jul",
  "aug",
  "sep",
  "oct",
  "nov",
  "dec",
];

const totalRevenue = computed(() =>
  monthlyData.value.reduce((sum, m) => sum + (m.revenue || 0), 0),
);

const avgMonthlyRevenue = computed(() =>
  monthlyData.value.length ? totalRevenue.value / monthlyData.value.length : 0,
);

const totalOrders = computed(() =>
  monthlyData.value.reduce((sum, m) => sum + (m.order_count || 0), 0),
);

const bestQuarter = computed(() => {
  let best = null;
  for (const q of quarterlyData.value) {
    if (!best || (q.total_revenue || 0) > (best.total_revenue || 0)) best = q;
  }
  return best ? best.quarter : "";
});

// Cached once per data change instead of recomputed per bar (was O(n^2)).
const maxRevenue = computed(() =>
  monthlyData.value.reduce((max, m) => Math.max(max, m.revenue || 0), 0),
);

const isEmpty = computed(
  () => quarterlyData.value.length === 0 && monthlyData.value.length === 0,
);

const loadData = async () => {
  try {
    loading.value = true;
    error.value = null;
    const filters = getCurrentFilters();
    quarterlyData.value = await api.getQuarterlyReports(filters);
    monthlyData.value = await api.getMonthlyTrends(filters);
  } catch (err) {
    error.value = t("common.error");
    console.error("Failed to load reports:", err);
  } finally {
    loading.value = false;
  }
};

// Money values come from the backend in USD; formatCurrency converts to the
// locale currency (¥ for JA) so Reports matches every other page.
const formatMoney = (value) =>
  formatCurrency(value || 0, currentCurrency.value);

const formatCount = (value) => (Number(value) || 0).toLocaleString();

const formatMonth = (monthStr) => {
  if (!monthStr) return "—";
  const [year, month] = monthStr.split("-");
  const idx = parseInt(month, 10) - 1;
  if (idx < 0 || idx > 11) return monthStr;
  return `${t("months." + MONTH_KEYS[idx])} ${year}`;
};

const getBarHeight = (revenue) => {
  if (!maxRevenue.value) return 0;
  return ((revenue || 0) / maxRevenue.value) * 200;
};

const getFulfillmentClass = (rate) => {
  if (rate >= 90) return "badge success";
  if (rate >= 75) return "badge warning";
  return "badge danger";
};

const getChangeValue = (current, previous) => {
  const change = (current || 0) - (previous || 0);
  const sign = change > 0 ? "+" : change < 0 ? "-" : "";
  return sign + formatMoney(Math.abs(change));
};

const getChangeClass = (current, previous) => {
  const change = (current || 0) - (previous || 0);
  if (change > 0) return "positive-change";
  if (change < 0) return "negative-change";
  return "";
};

const getGrowthRate = (current, previous) => {
  if (!previous) return "—";
  const rate = ((current - previous) / previous) * 100;
  const sign = rate > 0 ? "+" : "";
  return sign + rate.toFixed(1) + "%";
};

// Reload whenever any global filter changes, mirroring Dashboard/Orders.
watch(
  [selectedPeriod, selectedLocation, selectedCategory, selectedStatus],
  () => loadData(),
);

onMounted(loadData);
</script>

<style scoped>
.reports {
  padding: 0;
}

/* Bar chart — component-specific; everything else (cards, tables, badges,
   stat cards, loading/error) inherits the global system in App.vue. */
.chart-container {
  padding: 2rem 1rem 0;
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: 0.5rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: #2563eb;
  border-radius: 4px 4px 0 0;
  transition:
    height 0.3s ease,
    background 0.15s ease;
  cursor: pointer;
}

.bar:hover {
  background: #1d4ed8;
}

.bar-label {
  margin-top: 1.5rem;
  font-size: 0.75rem;
  color: #64748b;
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.positive-change {
  color: #059669;
  font-weight: 600;
}

.negative-change {
  color: #dc2626;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

@media (prefers-reduced-motion: reduce) {
  .bar {
    transition: none;
  }
}
</style>
