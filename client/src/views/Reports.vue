<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
        </div>
        <div v-if="quarterlyData.length === 0" class="no-data">{{ t('common.noData') }}</div>
        <div v-else class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th>{{ t('reports.quarterly.totalOrders') }}</th>
                <th>{{ t('reports.quarterly.totalRevenue') }}</th>
                <th>{{ t('reports.quarterly.avgOrderValue') }}</th>
                <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ formatQuarter(q.quarter) }}</strong></td>
                <td>{{ q.total_orders }}</td>
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
          <h3 class="card-title">{{ t('reports.monthlyChart.title') }}</h3>
        </div>
        <div v-if="monthlyData.length === 0" class="no-data">{{ t('common.noData') }}</div>
        <div v-else class="chart-container">
          <div class="bar-chart" role="img" :aria-label="t('reports.monthlyChart.ariaLabel')">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatMoney(month.revenue)"
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
          <h3 class="card-title">{{ t('reports.monthOverMonth.title') }}</h3>
        </div>
        <div v-if="monthlyData.length === 0" class="no-data">{{ t('common.noData') }}</div>
        <div v-else class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.monthOverMonth.month') }}</th>
                <th>{{ t('reports.monthOverMonth.orders') }}</th>
                <th>{{ t('reports.monthOverMonth.revenue') }}</th>
                <th>{{ t('reports.monthOverMonth.change') }}</th>
                <th>{{ t('reports.monthOverMonth.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in monthOverMonth" :key="row.month">
                <td><strong>{{ formatMonth(row.month) }}</strong></td>
                <td>{{ row.order_count }}</td>
                <td>{{ formatMoney(row.revenue) }}</td>
                <td>
                  <span v-if="row.hasPrevious" :class="row.changeClass">{{ row.changeLabel }}</span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="row.hasPrevious" :class="row.changeClass">{{ row.growthLabel }}</span>
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
          <div class="stat-value">{{ formatMoney(summaryStats.totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(summaryStats.avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalOrders') }}</div>
          <div class="stat-value">{{ summaryStats.totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
          <div class="stat-value">
            {{ summaryStats.bestQuarter ? formatQuarter(summaryStats.bestQuarter) : '-' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

// Tallest bar in the chart, in pixels. Matches .bar-container's fixed height, so a bar can
// never overflow its track.
const MAX_BAR_HEIGHT = 200

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    const loadData = async () => {
      try {
        loading.value = true
        // Clear any prior failure, or a retry that succeeds would still render the old error.
        error.value = null

        const filters = getCurrentFilters()
        // Independent requests, so issue them together rather than in series.
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])

        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        error.value = `${t('reports.errors.load')} ${err.message}`
        console.error('Failed to load reports:', err)
      } finally {
        loading.value = false
      }
    }

    // Delegates to the shared currency util so amounts convert to JPY and use the locale's
    // digit grouping. The old hand-rolled formatter emitted a bare "$" in every locale.
    const formatMoney = (amount) => {
      return formatCurrencyWithDecimals(amount || 0, currentCurrency.value, 2)
    }

    // Summary figures are derived from the two responses, so they belong in a computed -
    // storing them in refs meant they could drift out of sync with the data they summarise.
    const summaryStats = computed(() => {
      const months = monthlyData.value
      const totalRevenue = months.reduce((sum, m) => sum + m.revenue, 0)
      const totalOrders = months.reduce((sum, m) => sum + m.order_count, 0)

      const best = quarterlyData.value.reduce(
        (top, q) => (top === null || q.total_revenue > top.total_revenue ? q : top),
        null
      )

      return {
        totalRevenue,
        avgMonthlyRevenue: months.length > 0 ? totalRevenue / months.length : 0,
        totalOrders,
        bestQuarter: best ? best.quarter : ''
      }
    })

    // One pass builds every month-over-month cell. The template previously reached back into
    // monthlyData[index - 1] and recomputed the same delta four times per row.
    const monthOverMonth = computed(() => {
      return monthlyData.value.map((month, index) => {
        const previous = index > 0 ? monthlyData.value[index - 1] : null
        if (!previous) {
          return { ...month, hasPrevious: false, changeClass: '', changeLabel: '', growthLabel: '' }
        }

        const delta = month.revenue - previous.revenue
        const sign = delta > 0 ? '+' : delta < 0 ? '-' : ''

        return {
          ...month,
          hasPrevious: true,
          changeClass: delta > 0 ? 'positive-change' : delta < 0 ? 'negative-change' : '',
          changeLabel: `${sign}${formatMoney(Math.abs(delta))}`,
          // A zero base makes percentage growth undefined rather than infinite.
          growthLabel: previous.revenue === 0
            ? t('reports.notAvailable')
            : `${delta > 0 ? '+' : ''}${((delta / previous.revenue) * 100).toFixed(1)}%`
        }
      })
    })

    // Computed once per data change instead of re-scanning every month for every bar rendered.
    const maxMonthlyRevenue = computed(() => {
      return monthlyData.value.reduce((max, m) => (m.revenue > max ? m.revenue : max), 0)
    })

    const getBarHeight = (revenue) => {
      if (maxMonthlyRevenue.value === 0) return 0
      return (revenue / maxMonthlyRevenue.value) * MAX_BAR_HEIGHT
    }

    const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    const formatMonth = (monthStr) => {
      // Guard the index lookup: an unexpected value used to render "undefined 2025".
      const [year, month] = String(monthStr || '').split('-')
      const index = parseInt(month, 10) - 1
      if (!year || Number.isNaN(index) || index < 0 || index > 11) return monthStr || '-'

      return t('reports.monthLabel', { month: t(`months.${MONTH_KEYS[index]}`), year })
    }

    const formatQuarter = (quarterStr) => {
      // Backend format is "Q1-2025"; anything else is passed through untouched.
      const match = /^Q([1-4])-(\d{4})$/.exec(String(quarterStr || ''))
      if (!match) return quarterStr || '-'

      const [, number, year] = match
      return t('reports.quarterLabel', { quarter: t(`reports.quarters.q${number}`), year })
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    // Reload whenever any global filter changes, matching Dashboard and Orders.
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], loadData)

    onMounted(loadData)

    return {
      t,
      currentLocale,
      loading,
      error,
      quarterlyData,
      monthlyData,
      monthOverMonth,
      summaryStats,
      getBarHeight,
      formatMoney,
      formatMonth,
      formatQuarter,
      getFulfillmentClass
    }
  }
}
</script>

<style scoped>
/* .card, .card-header, .card-title, .stats-grid, .stat-card, .badge, .loading and .error
   are all defined globally in App.vue - only Reports-specific rules belong here. */
.reports {
  padding: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: #f8fafc;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #64748b;
  border-bottom: 2px solid #e2e8f0;
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.reports-table tr:hover {
  background: #f8fafc;
}

.no-data {
  padding: 3rem;
  text-align: center;
  color: #64748b;
}

.chart-container {
  padding: 2rem 1rem;
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
  background: linear-gradient(to top, #3b82f6, #60a5fa);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, #2563eb, #3b82f6);
}

.bar-label {
  font-size: 0.75rem;
  color: #64748b;
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: 1.5rem;
}

.positive-change {
  color: #16a34a;
  font-weight: 600;
}

.negative-change {
  color: #dc2626;
  font-weight: 600;
}
</style>
