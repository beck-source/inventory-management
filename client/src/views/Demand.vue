<template>
  <div class="demand">
    <div class="page-header">
      <h2>{{ t("demand.title") }}</h2>
      <p>{{ t("demand.description") }}</p>
    </div>

    <ErrorState
      v-if="loading || error"
      :loading="loading"
      :message="error || ''"
      @retry="reload"
    />
    <div v-else>
      <div class="demand-trend-cards">
        <div class="trend-card increasing-card">
          <div class="trend-header">
            <div class="trend-icon">↑</div>
            <div>
              <div class="trend-label">{{ t("demand.increasingDemand") }}</div>
              <div class="trend-count">
                {{
                  t("demand.itemsCount", {
                    count: getForecastsByTrend("increasing").length,
                  })
                }}
              </div>
            </div>
          </div>
          <div class="trend-items">
            <div
              v-for="item in getForecastsByTrend('increasing').slice(0, 5)"
              :key="item.id"
              class="trend-item"
            >
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">+{{ getChangePercent(item) }}%</span>
            </div>
            <div
              v-if="getForecastsByTrend('increasing').length > 5"
              class="more-items"
            >
              +{{ getForecastsByTrend("increasing").length - 5 }}
              {{ t("demand.more") }}
            </div>
          </div>
        </div>

        <div class="trend-card stable-card">
          <div class="trend-header">
            <div class="trend-icon">→</div>
            <div>
              <div class="trend-label">{{ t("demand.stableDemand") }}</div>
              <div class="trend-count">
                {{
                  t("demand.itemsCount", {
                    count: getForecastsByTrend("stable").length,
                  })
                }}
              </div>
            </div>
          </div>
          <div class="trend-items">
            <div
              v-for="item in getForecastsByTrend('stable').slice(0, 5)"
              :key="item.id"
              class="trend-item"
            >
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change neutral"
                >{{ getChangePercent(item) }}%</span
              >
            </div>
            <div
              v-if="getForecastsByTrend('stable').length > 5"
              class="more-items"
            >
              +{{ getForecastsByTrend("stable").length - 5 }}
              {{ t("demand.more") }}
            </div>
          </div>
        </div>

        <div class="trend-card decreasing-card">
          <div class="trend-header">
            <div class="trend-icon">↓</div>
            <div>
              <div class="trend-label">{{ t("demand.decreasingDemand") }}</div>
              <div class="trend-count">
                {{
                  t("demand.itemsCount", {
                    count: getForecastsByTrend("decreasing").length,
                  })
                }}
              </div>
            </div>
          </div>
          <div class="trend-items">
            <div
              v-for="item in getForecastsByTrend('decreasing').slice(0, 5)"
              :key="item.id"
              class="trend-item"
            >
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">{{ getChangePercent(item) }}%</span>
            </div>
            <div
              v-if="getForecastsByTrend('decreasing').length > 5"
              class="more-items"
            >
              +{{ getForecastsByTrend("decreasing").length - 5 }}
              {{ t("demand.more") }}
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("demand.demandForecasts") }}</h3>
        </div>
        <div class="table-container">
          <table>
            <caption class="sr-only">
              {{
                t("demand.demandForecasts")
              }}
            </caption>
            <thead>
              <tr>
                <th scope="col">{{ t("demand.table.sku") }}</th>
                <th scope="col">{{ t("demand.table.itemName") }}</th>
                <th scope="col">{{ t("demand.table.currentDemand") }}</th>
                <th scope="col">{{ t("demand.table.forecastedDemand") }}</th>
                <th scope="col">{{ t("demand.table.change") }}</th>
                <th scope="col">{{ t("demand.table.trend") }}</th>
                <th scope="col">{{ t("demand.table.period") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="forecast in forecasts" :key="forecast.id">
                <td>
                  <strong>{{ forecast.item_sku }}</strong>
                </td>
                <td>{{ forecast.item_name }}</td>
                <td>{{ forecast.current_demand }}</td>
                <td>
                  <strong>{{ forecast.forecasted_demand }}</strong>
                </td>
                <td>
                  <span :style="{ color: getChangeColor(forecast) }">
                    {{ getChangePercent(forecast) }}%
                  </span>
                </td>
                <td>
                  <span :class="['badge', forecast.trend]">
                    {{ t(`trends.${forecast.trend}`) }}
                  </span>
                </td>
                <td>{{ translatePeriod(forecast.period) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed } from "vue";
import { api } from "../api";
import { useFilters } from "../composables/useFilters";
import { useI18n } from "../composables/useI18n";
import { useFilteredLoad } from "../composables/useFilteredLoad";
import ErrorState from "../components/ErrorState.vue";

export default {
  name: "Demand",
  components: { ErrorState },
  setup() {
    const { t } = useI18n();
    const allForecasts = ref([]);
    const inventoryItems = ref([]);

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } =
      useFilters();

    // Filter forecasts based on inventory filters
    const forecasts = computed(() => {
      if (
        selectedLocation.value === "all" &&
        selectedCategory.value === "all"
      ) {
        return allForecasts.value;
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map((item) => item.sku));
      return allForecasts.value.filter((f) => validSkus.has(f.item_sku));
    });

    const { loading, error, reload } = useFilteredLoad(async () => {
      const filters = getCurrentFilters();

      const [forecastsData, inventoryData] = await Promise.all([
        api.getDemandForecasts(),
        api.getInventory({
          warehouse: filters.warehouse,
          category: filters.category,
        }),
      ]);

      allForecasts.value = forecastsData;
      inventoryItems.value = inventoryData;
    });

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], reload);

    const getForecastsByTrend = (trend) => {
      return forecasts.value.filter((f) => f.trend === trend);
    };

    const getChangePercent = (forecast) => {
      const change = (
        ((forecast.forecasted_demand - forecast.current_demand) /
          forecast.current_demand) *
        100
      ).toFixed(1);
      return change > 0 ? `+${change}` : change;
    };

    const getChangeColor = (forecast) => {
      const change = forecast.forecasted_demand - forecast.current_demand;
      const changePercent = Math.abs((change / forecast.current_demand) * 100);

      // If change is within ±2%, consider it stable and show blue
      if (changePercent <= 2) {
        return "var(--blue)"; // Blue for stable
      }

      if (change > 0) return "var(--green)"; // Green for increasing
      if (change < 0) return "var(--red)"; // Red for decreasing
      return "var(--blue)"; // Blue for no change
    };

    const translatePeriod = (period) => {
      // Period values like "Next 3 months", "Q1 2025", "30 days", etc.
      const { currentLocale } = useI18n();
      if (currentLocale.value === "ja") {
        return period
          .replace(/Next\s+/i, "次の")
          .replace(/\s+months/i, "か月")
          .replace(/\s+month/i, "か月")
          .replace(/\s+days/i, "日間")
          .replace(/\s+day/i, "日")
          .replace("Q1", "第1四半期")
          .replace("Q2", "第2四半期")
          .replace("Q3", "第3四半期")
          .replace("Q4", "第4四半期");
      }
      return period;
    };

    return {
      t,
      loading,
      error,
      reload,
      forecasts,
      getForecastsByTrend,
      getChangePercent,
      getChangeColor,
      translatePeriod,
    };
  },
};
</script>

<style scoped>
.demand-trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.trend-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
  transition: all 0.2s ease;
}

.trend-card:hover {
  box-shadow: 0 4px 12px var(--shadow-a);
}

.increasing-card {
  border-left: 4px solid var(--green);
}

.stable-card {
  border-left: 4px solid var(--blue);
}

.decreasing-card {
  border-left: 4px solid var(--red);
}

.trend-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.trend-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 1.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .trend-icon {
  background: var(--green-soft);
  color: var(--success-fg);
}

.stable-card .trend-icon {
  background: var(--blue-soft);
  color: var(--accent);
}

.decreasing-card .trend-icon {
  background: var(--red-soft);
  color: var(--danger-fg);
}

.trend-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trend-count {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-strong);
  margin-top: 0.25rem;
}

.trend-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--surface-muted);
  border-radius: 6px;
  transition: background 0.2s;
}

.trend-item:hover {
  background: var(--surface-sunken);
}

.item-name {
  font-size: 0.875rem;
  color: var(--text-strong);
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 1rem;
}

.item-change {
  font-size: 0.813rem;
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .item-change {
  color: var(--success-fg);
}

.stable-card .item-change {
  color: var(--blue);
}

.decreasing-card .item-change {
  color: var(--danger-fg);
}

.item-change.neutral {
  color: var(--text-muted);
}

.more-items {
  font-size: 0.813rem;
  color: var(--text-muted);
  font-style: italic;
  text-align: center;
  padding: 0.5rem;
}
</style>
