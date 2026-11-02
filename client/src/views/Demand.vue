<template>
  <div class="demand">
    <PageHeader :title="t('demand.title')" />
    <FilterBar />

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="trend-cards">
        <Card class="trend-card-increasing">
          <div class="trend-header">
            <div class="trend-icon-wrap increasing">↑</div>
            <div>
              <div class="trend-label">{{ t('demand.increasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('increasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('increasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <Badge variant="success">+{{ getChangePercent(item) }}%</Badge>
            </div>
            <div v-if="getForecastsByTrend('increasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('increasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </Card>

        <Card class="trend-card-stable">
          <div class="trend-header">
            <div class="trend-icon-wrap stable">→</div>
            <div>
              <div class="trend-label">{{ t('demand.stableDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('stable').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('stable').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <Badge variant="neutral">{{ getChangePercent(item) }}%</Badge>
            </div>
            <div v-if="getForecastsByTrend('stable').length > 5" class="more-items">
              +{{ getForecastsByTrend('stable').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </Card>

        <Card class="trend-card-decreasing">
          <div class="trend-header">
            <div class="trend-icon-wrap decreasing">↓</div>
            <div>
              <div class="trend-label">{{ t('demand.decreasingDemand') }}</div>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('decreasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('decreasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <Badge variant="danger">{{ getChangePercent(item) }}%</Badge>
            </div>
            <div v-if="getForecastsByTrend('decreasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('decreasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <template #title>{{ t('demand.demandForecasts') }}</template>
        <div class="table-no-pad">
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
                    <span :style="{ color: getChangeColor(forecast), fontWeight: 600 }">
                      {{ getChangePercent(forecast) }}%
                    </span>
                  </td>
                  <td>
                    <Badge :variant="getTrendVariant(forecast.trend)">
                      {{ t(`trends.${forecast.trend}`) }}
                    </Badge>
                  </td>
                  <td>{{ translatePeriod(forecast.period) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import PageHeader from '../components/ui/PageHeader.vue'
import Card from '../components/ui/Card.vue'
import Badge from '../components/ui/Badge.vue'
import FilterBar from '../components/FilterBar.vue'

export default {
  name: 'Demand',
  components: {
    PageHeader,
    Card,
    Badge,
    FilterBar
  },
  setup() {
    const { t } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const forecasts = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allForecasts.value
      }
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
      if (changePercent <= 2) return 'var(--accent)'
      if (change > 0) return 'var(--success)'
      if (change < 0) return 'var(--danger)'
      return 'var(--accent)'
    }

    const getTrendVariant = (trend) => {
      if (trend === 'increasing') return 'success'
      if (trend === 'decreasing') return 'danger'
      return 'neutral'
    }

    const translatePeriod = (period) => {
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
      getTrendVariant,
      translatePeriod
    }
  }
}
</script>

<style scoped>
.trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.trend-card-increasing {
  border-left: 3px solid var(--success);
}

.trend-card-stable {
  border-left: 3px solid var(--accent);
}

.trend-card-decreasing {
  border-left: 3px solid var(--danger);
}

.trend-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
}

.trend-icon-wrap {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--r-md);
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}

.trend-icon-wrap.increasing {
  background: rgba(16, 185, 129, 0.12);
  color: var(--success);
}

.trend-icon-wrap.stable {
  background: rgba(59, 130, 246, 0.12);
  color: var(--accent);
}

.trend-icon-wrap.decreasing {
  background: rgba(239, 68, 68, 0.12);
  color: var(--danger);
}

.trend-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.trend-count {
  font-size: 20px;
  font-weight: 700;
  color: var(--ink-primary);
  margin-top: 4px;
}

.trend-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--surface-muted);
  border-radius: var(--r-sm);
}

.item-name {
  font-size: 13px;
  color: var(--ink-primary);
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 16px;
}

.more-items {
  font-size: 12px;
  color: var(--ink-muted);
  font-style: italic;
  text-align: center;
  padding: 8px;
}

.table-no-pad {
  margin: 0 calc(-1 * var(--sp-6));
  margin-bottom: calc(-1 * var(--sp-6));
}
</style>
