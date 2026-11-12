<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <AsyncStatus
      :loading="loading"
      :error="error"
      :loaded="loaded"
      :loading-text="t('reports.loading')"
      @retry="reload"
    >
      <div v-if="quarterlyData.length === 0 && monthlyRows.length === 0" class="card empty-state">
        {{ t('reports.noData') }}
      </div>
      <div v-else>
        <!-- Quarterly Performance -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
          </div>
          <div v-if="quarterlyData.length === 0" class="empty-state">{{ t('reports.noData') }}</div>
          <div v-else class="table-container">
            <table class="reports-table">
              <thead>
                <tr>
                  <th>{{ t('reports.quarterly.quarter') }}</th>
                  <th class="num">{{ t('reports.quarterly.totalOrders') }}</th>
                  <th class="num">{{ t('reports.quarterly.totalRevenue') }}</th>
                  <th class="num">{{ t('reports.quarterly.avgOrderValue') }}</th>
                  <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="q in quarterlyData" :key="q.quarter">
                  <td>
                    <strong>{{ q.quarter }}</strong>
                  </td>
                  <td class="num">{{ q.total_orders }}</td>
                  <td class="num">{{ formatCurrency(q.total_revenue, currentCurrency) }}</td>
                  <td class="num">{{ formatCurrency(q.avg_order_value, currentCurrency) }}</td>
                  <td>
                    <span :class="getFulfillmentClass(q.fulfillment_rate)"> {{ q.fulfillment_rate }}% </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Monthly Trends Chart -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.trend.title') }}</h3>
          </div>
          <div v-if="monthlyRows.length === 0" class="empty-state">{{ t('reports.noData') }}</div>
          <div v-else class="chart-container">
            <div class="bar-chart">
              <div v-for="row in monthlyRows" :key="row.month" class="bar-wrapper">
                <div class="bar-container">
                  <div
                    class="bar"
                    :style="{ height: getBarHeight(row.revenue) + 'px' }"
                    :title="formatCurrency(row.revenue, currentCurrency)"
                  ></div>
                </div>
                <div class="bar-label">{{ row.label }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Month-over-Month Comparison -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.mom.title') }}</h3>
          </div>
          <div v-if="monthlyRows.length === 0" class="empty-state">{{ t('reports.noData') }}</div>
          <div v-else class="table-container">
            <table class="reports-table">
              <thead>
                <tr>
                  <th>{{ t('reports.mom.month') }}</th>
                  <th class="num">{{ t('reports.mom.orders') }}</th>
                  <th class="num">{{ t('reports.mom.revenue') }}</th>
                  <th>{{ t('reports.mom.change') }}</th>
                  <th>{{ t('reports.mom.growthRate') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in monthlyRows" :key="row.month">
                  <td>
                    <strong>{{ row.label }}</strong>
                  </td>
                  <td class="num">{{ row.order_count }}</td>
                  <td class="num">{{ formatCurrency(row.revenue, currentCurrency) }}</td>
                  <td>
                    <span v-if="row.hasPrevious" :class="row.changeClass">{{ row.changeText }}</span>
                    <span v-else>-</span>
                  </td>
                  <td>
                    <span v-if="row.hasPrevious" :class="row.changeClass">{{ row.growthText }}</span>
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
            <div class="stat-label">{{ t('reports.stats.totalRevenue') }}</div>
            <div class="stat-value">{{ formatCurrency(totalRevenue, currentCurrency) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
            <div class="stat-value">{{ formatCurrency(avgMonthlyRevenue, currentCurrency) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('reports.stats.totalOrders') }}</div>
            <div class="stat-value">{{ totalOrders }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
            <div class="stat-value">{{ bestQuarter || '-' }}</div>
          </div>
        </div>
      </div>
    </AsyncStatus>
  </div>
</template>

<script>
import AsyncStatus from '../components/AsyncStatus.vue'
import { useAsyncData } from '../composables/useAsyncData'
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

export default {
  name: 'Reports',
  components: { AsyncStatus },
  setup() {
    const { t, currentCurrency } = useI18n()

    // Raw data in refs; everything derived is computed
    const quarterlyData = ref([])
    const monthlyData = ref([])

    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, getCurrentFilters } = useFilters()

    // Reloads on filter change; previous data stays visible meanwhile
    const { loading, error, loaded, reload } = useAsyncData(
      async ({ signal }) => {
        const filters = getCurrentFilters()
        // Independent requests: run in parallel
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters, { signal }),
          api.getMonthlyTrends(filters, { signal }),
        ])
        return { quarterly, monthly }
      },
      {
        watchSources: [selectedPeriod, selectedLocation, selectedCategory, selectedStatus],
        onSuccess: ({ quarterly, monthly }) => {
          quarterlyData.value = quarterly
          monthlyData.value = monthly
        },
      }
    )

    // 'YYYY-MM' -> localized month label; falls back to the raw string if malformed
    const formatMonth = (monthStr) => {
      const [year, month] = String(monthStr).split('-')
      const key = MONTH_KEYS[parseInt(month, 10) - 1]
      return key ? `${t('months.' + key)} ${year}` : monthStr
    }

    const maxRevenue = computed(() => monthlyData.value.reduce((max, m) => Math.max(max, m.revenue), 0))

    // Chart bar height in px (max 200)
    const getBarHeight = (revenue) => {
      return maxRevenue.value === 0 ? 0 : (revenue / maxRevenue.value) * 200
    }

    // Monthly rows with label and month-over-month change precomputed
    const monthlyRows = computed(() => {
      return monthlyData.value.map((m, index) => {
        const row = { ...m, label: formatMonth(m.month), hasPrevious: index > 0 }
        if (index > 0) {
          const prev = monthlyData.value[index - 1].revenue
          const change = m.revenue - prev
          const sign = change > 0 ? '+' : change < 0 ? '-' : ''
          row.changeText = sign + formatCurrencyWithDecimals(Math.abs(change), currentCurrency.value, 2)
          row.changeClass = change > 0 ? 'positive-change' : change < 0 ? 'negative-change' : ''
          // Growth is undefined when previous month had no revenue
          row.growthText = prev === 0 ? 'N/A' : (change > 0 ? '+' : '') + ((change / prev) * 100).toFixed(1) + '%'
        }
        return row
      })
    })

    const totalRevenue = computed(() => monthlyData.value.reduce((sum, m) => sum + m.revenue, 0))

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
    )

    const totalOrders = computed(() => monthlyData.value.reduce((sum, m) => sum + m.order_count, 0))

    // Empty string when there is no quarter with revenue
    const bestQuarter = computed(() => {
      let best = null
      for (const q of quarterlyData.value) {
        if (q.total_revenue > 0 && (!best || q.total_revenue > best.total_revenue)) best = q
      }
      return best ? best.quarter : ''
    })

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    return {
      t,
      currentCurrency,
      loading,
      error,
      loaded,
      reload,
      quarterlyData,
      monthlyRows,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      getBarHeight,
      getFulfillmentClass,
      formatCurrency,
    }
  },
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.chart-container {
  padding: var(--space-8) var(--space-4);
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: var(--space-2);
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
  background: var(--info);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: var(--info);
}

.bar-label {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: var(--space-6);
}

.positive-change {
  color: var(--success-ink);
  font-weight: 600;
}

.negative-change {
  color: var(--danger);
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: var(--space-12);
  color: var(--text-muted);
}
</style>
