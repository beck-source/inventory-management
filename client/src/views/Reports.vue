<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t("reports.title") }}</h2>
      <p>{{ t("reports.description") }}</p>
    </div>

    <ErrorState
      v-if="loading || error"
      :loading="loading"
      :message="error || ''"
      @retry="reload"
    />
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.quarterly.title") }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <caption class="sr-only">
              {{
                t("reports.quarterly.title")
              }}
            </caption>
            <thead>
              <tr>
                <th scope="col">{{ t("reports.quarterly.quarter") }}</th>
                <th scope="col">{{ t("reports.quarterly.totalOrders") }}</th>
                <th scope="col">{{ t("reports.quarterly.totalRevenue") }}</th>
                <th scope="col">{{ t("reports.quarterly.avgOrderValue") }}</th>
                <th scope="col">
                  {{ t("reports.quarterly.fulfillmentRate") }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td>
                  <strong>{{ q.quarter }}</strong>
                </td>
                <td>{{ q.total_orders }}</td>
                <td>{{ money(q.total_revenue) }}</td>
                <td>{{ money(q.avg_order_value) }}</td>
                <td>
                  <span
                    v-if="hasRate(q.fulfillment_rate)"
                    :class="getFulfillmentClass(q.fulfillment_rate)"
                  >
                    {{ q.fulfillment_rate }}%
                  </span>
                  <span v-else>{{ t("reports.notAvailable") }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.trend.title") }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div
              v-for="month in monthlyData"
              :key="month.month"
              class="bar-wrapper"
            >
              <div class="bar-container">
                <div
                  class="bar"
                  role="img"
                  :aria-label="getBarLabel(month)"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="money(month.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("reports.mom.title") }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <caption class="sr-only">
              {{
                t("reports.mom.title")
              }}
            </caption>
            <thead>
              <tr>
                <th scope="col">{{ t("reports.mom.month") }}</th>
                <th scope="col">{{ t("reports.mom.orders") }}</th>
                <th scope="col">{{ t("reports.mom.revenue") }}</th>
                <th scope="col">{{ t("reports.mom.change") }}</th>
                <th scope="col">{{ t("reports.mom.growthRate") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td>
                  <strong>{{ formatMonth(month.month) }}</strong>
                </td>
                <td>{{ month.order_count }}</td>
                <td>{{ money(month.revenue) }}</td>
                <td>
                  <span
                    v-if="index > 0"
                    :class="
                      getChangeClass(
                        month.revenue,
                        monthlyData[index - 1].revenue,
                      )
                    "
                  >
                    {{
                      getChangeValue(
                        month.revenue,
                        monthlyData[index - 1].revenue,
                      )
                    }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span
                    v-if="index > 0"
                    :class="
                      getChangeClass(
                        month.revenue,
                        monthlyData[index - 1].revenue,
                      )
                    "
                  >
                    {{
                      getGrowthRate(
                        month.revenue,
                        monthlyData[index - 1].revenue,
                      )
                    }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">
            {{ t("reports.summary.totalRevenueYtd") }}
          </div>
          <div class="stat-value">{{ moneyWhole(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            {{ t("reports.summary.avgMonthlyRevenue") }}
          </div>
          <div class="stat-value">{{ moneyWhole(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            {{ t("reports.summary.totalOrdersYtd") }}
          </div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t("reports.summary.bestQuarter") }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from "vue";
import { api } from "../api";
import { useI18n } from "../composables/useI18n";
import { useFilters } from "../composables/useFilters";
import { useFilteredLoad } from "../composables/useFilteredLoad";
import {
  formatCurrencyWithDecimals,
  formatCurrency,
} from "../utils/currency";
import ErrorState from "../components/ErrorState.vue";

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
const MAX_BAR_HEIGHT = 200;

export default {
  name: "Reports",
  components: { ErrorState },
  setup() {
    const { t, currentCurrency } = useI18n();

    const quarterlyData = ref([]);
    const monthlyData = ref([]);

    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters,
    } = useFilters();

    const { loading, error, reload } = useFilteredLoad(async () => {
      const filters = getCurrentFilters();
      const [quarterly, monthly] = await Promise.all([
        api.getQuarterlyReports(filters),
        api.getMonthlyTrends(filters),
      ]);
      quarterlyData.value = quarterly;
      monthlyData.value = monthly;
    });

    watch(
      [selectedPeriod, selectedLocation, selectedCategory, selectedStatus],
      reload,
    );

    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + (m.revenue || 0), 0),
    );

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length > 0
        ? totalRevenue.value / monthlyData.value.length
        : 0,
    );

    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + (m.order_count || 0), 0),
    );

    const bestQuarter = computed(() => {
      const best = quarterlyData.value.reduce(
        (acc, q) => (q.total_revenue > acc.revenue
          ? { revenue: q.total_revenue, quarter: q.quarter }
          : acc),
        { revenue: 0, quarter: "" },
      );
      return best.quarter;
    });

    const maxRevenue = computed(() =>
      monthlyData.value.reduce((max, m) => Math.max(max, m.revenue || 0), 0),
    );

    const money = (amount) =>
      formatCurrencyWithDecimals(amount, currentCurrency.value, 2);

    const moneyWhole = (amount) =>
      formatCurrency(amount, currentCurrency.value);

    const formatMonth = (monthStr) => {
      const parts = String(monthStr).split("-");
      const monthIndex = parseInt(parts[1], 10) - 1;
      if (!parts[1] || isNaN(monthIndex) || monthIndex < 0 || monthIndex > 11) {
        return monthStr;
      }
      return t("months." + MONTH_KEYS[monthIndex]) + " " + parts[0];
    };

    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0;
      return (revenue / maxRevenue.value) * MAX_BAR_HEIGHT;
    };

    const getBarLabel = (month) =>
      t("reports.trend.barLabel", {
        month: formatMonth(month.month),
        value: money(month.revenue),
      });

    const hasRate = (rate) => typeof rate === "number" && !isNaN(rate);

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return "badge success";
      if (rate >= 75) return "badge warning";
      return "badge danger";
    };

    const getChangeValue = (current, previous) => {
      const change = current - previous;
      if (change > 0) return "+" + money(change);
      if (change < 0) return "-" + money(Math.abs(change));
      return money(0);
    };

    const getChangeClass = (current, previous) => {
      const change = current - previous;
      if (change > 0) return "positive-change";
      if (change < 0) return "negative-change";
      return "";
    };

    const getGrowthRate = (current, previous) => {
      if (!previous) return t("reports.notAvailable");
      const rate = ((current - previous) / previous) * 100;
      return (rate > 0 ? "+" : "") + rate.toFixed(1) + "%";
    };

    return {
      t,
      loading,
      error,
      reload,
      quarterlyData,
      monthlyData,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      money,
      moneyWhole,
      formatMonth,
      getBarHeight,
      getBarLabel,
      hasRate,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate,
    };
  },
};
</script>

<style scoped>
.reports {
  padding: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: var(--surface-muted);
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 2px solid var(--border);
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.reports-table tr:hover {
  background: var(--surface-muted);
}

.chart-container {
  overflow-x: auto;
  padding: 2rem 1rem;
  min-height: 300px;
}

.bar-chart {
  min-width: 0;
  max-width: 100%;
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
  min-width: 0;
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
  background: linear-gradient(to top, var(--blue), var(--blue-light));
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, var(--accent-solid), var(--blue));
}

.bar-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: 1.5rem;
}

.positive-change {
  color: var(--success-fg);
  font-weight: 600;
}

.negative-change {
  color: var(--danger-fg);
  font-weight: 600;
}
</style>
