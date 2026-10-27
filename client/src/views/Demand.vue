<template>
  <div class="demand">
    <div class="page-header">
      <h2>{{ t('demand.title') }}</h2>
      <p>{{ t('demand.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="demand-trend-cards">
        <div class="trend-card increasing-card">
          <div class="trend-header">
            <div class="trend-icon">↑</div>
            <div>
              <div class="trend-label">{{ t('demand.increasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('increasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('increasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">+{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('increasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('increasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="trend-card stable-card">
          <div class="trend-header">
            <div class="trend-icon">→</div>
            <div>
              <div class="trend-label">{{ t('demand.stableDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('stable').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('stable').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change neutral">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('stable').length > 5" class="more-items">
              +{{ getForecastsByTrend('stable').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="trend-card decreasing-card">
          <div class="trend-header">
            <div class="trend-icon">↓</div>
            <div>
              <div class="trend-label">{{ t('demand.decreasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('decreasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('decreasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('decreasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('decreasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('demand.demandForecasts') }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('demand.table.sku') }}</th>
                <th>{{ t('demand.table.itemName') }}</th>
                <th>{{ t('demand.table.currentDemand') }}</th>
                <th>{{ t('demand.table.forecastedDemand') }}</th>
                <th>{{ t('demand.table.change') }}</th>
                <th>{{ t('demand.table.trend') }}</th>
                <th>{{ t('demand.table.period') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="forecast in forecasts" :key="forecast.id">
                <td><strong>{{ forecast.item_sku }}</strong></td>
                <td>{{ forecast.item_name }}</td>
                <td>{{ forecast.current_demand }}</td>
                <td><strong>{{ forecast.forecasted_demand }}</strong></td>
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
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Demand',
  setup() {
    const { t } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Filter forecasts based on inventory filters
    const forecasts = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allForecasts.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allForecasts.value.filter(f => validSkus.has(f.item_sku))
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadForecasts()
    })

    const getForecastsByTrend = (trend) => {
      return forecasts.value.filter(f => f.trend === trend)
    }

    const getChangePercent = (forecast) => {
      const change = ((forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand * 100).toFixed(1)
      return change > 0 ? `+${change}` : change
    }

    const getChangeColor = (forecast) => {
      const change = forecast.forecasted_demand - forecast.current_demand
      const changePercent = Math.abs((change / forecast.current_demand) * 100)

      // If change is within ±2%, consider it stable and show blue
      if (changePercent <= 2) {
        return '#3b82f6' // Blue for stable
      }

      if (change > 0) return '#10b981' // Green for increasing
      if (change < 0) return '#ef4444' // Red for decreasing
      return '#3b82f6' // Blue for no change
    }

    const translatePeriod = (period) => {
      // Period values like "Next 3 months", "Q1 2025", "30 days", etc.
      const { currentLocale } = useI18n()
      if (currentLocale.value === 'ja') {
        return period
          .replace(/Next\s+/i, '次の')
          .replace(/\s+months/i, 'か月')
          .replace(/\s+month/i, 'か月')
          .replace(/\s+days/i, '日間')
          .replace(/\s+day/i, '日')
          .replace('Q1', '第1四半期')
          .replace('Q2', '第2四半期')
          .replace('Q3', '第3四半期')
          .replace('Q4', '第4四半期')
      }
      return period
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      forecasts,
      getForecastsByTrend,
      getChangePercent,
      getChangeColor,
      translatePeriod
    }
  }
}
</script>

<style scoped>
.demand-trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

/* Same surface, border, radius and padding as the global .card; the 4px left
   border carries the semantic trend color. */
.trend-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.trend-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-strong);
}

.increasing-card {
  border-left: 4px solid var(--color-success);
}

.stable-card {
  border-left: 4px solid var(--color-info);
}

.decreasing-card {
  border-left: 4px solid var(--color-danger);
}

/* Mirrors the global .card-header treatment */
.trend-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

/* 48px icon tile has no spacing token equivalent besides --space-12 (48px) */
.trend-icon {
  width: var(--space-12);
  height: var(--space-12);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-card);
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  flex-shrink: 0;
}

.increasing-card .trend-icon {
  background: var(--color-success-tint);
  color: var(--color-success);
}

.stable-card .trend-icon {
  background: var(--color-info-tint);
  color: var(--color-info);
}

.decreasing-card .trend-icon {
  background: var(--color-danger-tint);
  color: var(--color-danger);
}

.trend-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trend-count {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-heading);
  margin-top: var(--space-1);
  letter-spacing: -0.025em;
}

.trend-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg);
  border-radius: var(--radius-control);
  transition: background-color 0.15s ease;
}

.trend-item:hover {
  background: var(--color-hover);
}

.item-name {
  font-size: var(--text-base);
  color: var(--color-heading);
  font-weight: var(--weight-medium);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: var(--space-4);
}

.item-change {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  flex-shrink: 0;
}

.increasing-card .item-change {
  color: var(--color-success);
}

.stable-card .item-change {
  color: var(--color-info);
}

.decreasing-card .item-change {
  color: var(--color-danger);
}

.item-change.neutral {
  color: var(--color-text-muted);
}

.more-items {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-style: italic;
  text-align: center;
  padding: var(--space-2);
}

@media (prefers-reduced-motion: reduce) {
  .trend-card,
  .trend-item {
    transition: none;
  }
}
</style>
