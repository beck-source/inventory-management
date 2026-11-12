<template>
  <div class="demand">
    <div class="page-header">
      <h2>{{ t('demand.title') }}</h2>
      <p>{{ t('demand.description') }}</p>
    </div>

    <AsyncStatus :loading="loading" :error="error" :loaded="loaded" @retry="reload">
      <div class="demand-trend-cards">
        <div class="trend-card increasing-card">
          <div class="trend-header">
            <div class="trend-icon">↑</div>
            <div>
              <div class="trend-label">{{ t('demand.increasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: forecastsByTrend.increasing.length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in forecastsByTrend.increasing.slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">+{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="forecastsByTrend.increasing.length > 5" class="more-items">
              +{{ forecastsByTrend.increasing.length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="trend-card stable-card">
          <div class="trend-header">
            <div class="trend-icon">→</div>
            <div>
              <div class="trend-label">{{ t('demand.stableDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: forecastsByTrend.stable.length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in forecastsByTrend.stable.slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change neutral">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="forecastsByTrend.stable.length > 5" class="more-items">
              +{{ forecastsByTrend.stable.length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </div>

        <div class="trend-card decreasing-card">
          <div class="trend-header">
            <div class="trend-icon">↓</div>
            <div>
              <div class="trend-label">{{ t('demand.decreasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: forecastsByTrend.decreasing.length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in forecastsByTrend.decreasing.slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="forecastsByTrend.decreasing.length > 5" class="more-items">
              +{{ forecastsByTrend.decreasing.length - 5 }} {{ t('demand.more') }}
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
                <th class="num">{{ t('demand.table.currentDemand') }}</th>
                <th class="num">{{ t('demand.table.forecastedDemand') }}</th>
                <th>{{ t('demand.table.change') }}</th>
                <th>{{ t('demand.table.trend') }}</th>
                <th>{{ t('demand.table.period') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="forecast in forecasts" :key="forecast.id">
                <td class="mono">
                  <strong>{{ forecast.item_sku }}</strong>
                </td>
                <td>{{ forecast.item_name }}</td>
                <td class="num">{{ forecast.current_demand }}</td>
                <td class="num">
                  <strong>{{ forecast.forecasted_demand }}</strong>
                </td>
                <td>
                  <span :style="{ color: getChangeColor(forecast) }"> {{ getChangePercent(forecast) }}% </span>
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
    </AsyncStatus>
  </div>
</template>

<script>
import AsyncStatus from '../components/AsyncStatus.vue'
import { useAsyncData } from '../composables/useAsyncData'
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Demand',
  components: { AsyncStatus },
  setup() {
    const { t, currentLocale } = useI18n()
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
      const validSkus = new Set(inventoryItems.value.map((item) => item.sku))
      return allForecasts.value.filter((f) => validSkus.has(f.item_sku))
    })

    // Reloads on filter change; previous forecasts stay visible meanwhile
    const { loading, error, loaded, reload } = useAsyncData(
      async ({ signal }) => {
        const filters = getCurrentFilters()
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts({ signal }),
          api.getInventory(
            {
              warehouse: filters.warehouse,
              category: filters.category,
            },
            { signal }
          ),
        ])
        return { forecastsData, inventoryData }
      },
      {
        watchSources: [selectedLocation, selectedCategory],
        onSuccess: ({ forecastsData, inventoryData }) => {
          allForecasts.value = forecastsData
          inventoryItems.value = inventoryData
        },
      }
    )

    // Group forecasts by trend in a single pass (cached) instead of re-filtering per card/usage
    const forecastsByTrend = computed(() => {
      const groups = { increasing: [], stable: [], decreasing: [] }
      for (const f of forecasts.value) {
        if (groups[f.trend]) groups[f.trend].push(f)
      }
      return groups
    })

    const getChangePercent = (forecast) => {
      const change = (((forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand) * 100).toFixed(
        1
      )
      return change > 0 ? `+${change}` : change
    }

    const getChangeColor = (forecast) => {
      const change = forecast.forecasted_demand - forecast.current_demand
      const changePercent = Math.abs((change / forecast.current_demand) * 100)

      // If change is within ±2%, consider it stable and show blue
      if (changePercent <= 2) {
        return 'var(--info)' // Blue for stable
      }

      if (change > 0) return 'var(--success)' // Green for increasing
      if (change < 0) return 'var(--danger)' // Red for decreasing
      return 'var(--info)' // Blue for no change
    }

    const translatePeriod = (period) => {
      // Period values like "Next 3 months", "Q1 2025", "30 days", etc.
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

    return {
      t,
      loading,
      error,
      loaded,
      reload,
      forecasts,
      forecastsByTrend,
      getChangePercent,
      getChangeColor,
      translatePeriod,
    }
  },
}
</script>

<style scoped>
.demand-trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.trend-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  transition: all var(--duration) var(--ease);
}

.trend-card:hover {
  box-shadow: var(--shadow-md);
}

.increasing-card {
  border-left: 4px solid var(--success);
}

.stable-card {
  border-left: 4px solid var(--info);
}

.decreasing-card {
  border-left: 4px solid var(--danger);
}

.trend-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--surface-muted);
}

.trend-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  font-size: var(--text-3xl);
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .trend-icon {
  background: var(--success-soft);
  color: var(--success-ink);
}

.stable-card .trend-icon {
  background: var(--info-soft);
  color: var(--info);
}

.decreasing-card .trend-icon {
  background: var(--danger-soft);
  color: var(--danger);
}

.trend-label {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trend-count {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text);
  margin-top: var(--space-1);
}

.trend-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--surface-subtle);
  border-radius: var(--radius-md);
  transition: background var(--duration) var(--ease);
}

.trend-item:hover {
  background: var(--surface-muted);
}

.item-name {
  font-size: var(--text-base);
  color: var(--text);
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: var(--space-4);
}

.item-change {
  font-size: var(--text-sm);
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .item-change {
  color: var(--success-ink);
}

.stable-card .item-change {
  color: var(--info);
}

.decreasing-card .item-change {
  color: var(--danger);
}

.item-change.neutral {
  color: var(--text-muted);
}

.more-items {
  font-size: var(--text-sm);
  color: var(--text-muted);
  font-style: italic;
  text-align: center;
  padding: var(--space-2);
}
</style>
