<template>
  <div class="demand">
    <div class="page-header">
      <h2>{{ t('demand.title') }}</h2>
      <p>{{ t('demand.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Trend summary cards -->
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('demand.increasingDemand') }}</div>
          <div class="stat-value">{{ getForecastsByTrend('increasing').length }}</div>
          <div class="trend-items-preview">
            <div v-for="item in getForecastsByTrend('increasing').slice(0, 3)" :key="item.id" class="preview-row">
              <span class="preview-name">{{ item.item_name }}</span>
              <span class="preview-change positive">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('increasing').length > 3" class="preview-more">
              +{{ getForecastsByTrend('increasing').length - 3 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="stat-card info">
          <div class="stat-label">{{ t('demand.stableDemand') }}</div>
          <div class="stat-value">{{ getForecastsByTrend('stable').length }}</div>
          <div class="trend-items-preview">
            <div v-for="item in getForecastsByTrend('stable').slice(0, 3)" :key="item.id" class="preview-row">
              <span class="preview-name">{{ item.item_name }}</span>
              <span class="preview-change neutral">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('stable').length > 3" class="preview-more">
              +{{ getForecastsByTrend('stable').length - 3 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="stat-card danger">
          <div class="stat-label">{{ t('demand.decreasingDemand') }}</div>
          <div class="stat-value">{{ getForecastsByTrend('decreasing').length }}</div>
          <div class="trend-items-preview">
            <div v-for="item in getForecastsByTrend('decreasing').slice(0, 3)" :key="item.id" class="preview-row">
              <span class="preview-name">{{ item.item_name }}</span>
              <span class="preview-change negative">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('decreasing').length > 3" class="preview-more">
              +{{ getForecastsByTrend('decreasing').length - 3 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Demand Forecasts table -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">{{ t('demand.demandForecasts') }}</span>
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
                  <span :style="{ color: getChangeColor(forecast) }" class="change-value">
                    {{ getChangePercent(forecast) }}%
                  </span>
                </td>
                <td>
                  <span :class="['badge', forecast.trend]">
                    {{ t(`trends.${forecast.trend}`) }}
                  </span>
                </td>
                <td class="period-cell">{{ translatePeriod(forecast.period) }}</td>
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
/* Stat card trend preview items */
.trend-items-preview {
  margin-top: 0.875rem;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8125rem;
}

.preview-name {
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 0.5rem;
}

.preview-change {
  font-weight: 600;
  flex-shrink: 0;
  font-size: 0.8125rem;
}

.preview-change.positive { color: #059669; }
.preview-change.negative { color: #dc2626; }
.preview-change.neutral  { color: #3b82f6; }

.preview-more {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-style: italic;
  margin-top: 0.125rem;
}

/* Table extras */
.change-value {
  font-weight: 600;
}

.period-cell {
  color: var(--text-secondary);
  font-size: 0.8125rem;
}
</style>
