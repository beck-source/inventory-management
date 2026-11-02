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
          <h3 class="card-title">{{ t('reports.quarterlyPerformance') }}</h3>
        </div>
        <div v-if="quarterlyData.length" class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.table.quarter') }}</th>
                <th>{{ t('reports.table.totalOrders') }}</th>
                <th>{{ t('reports.table.totalRevenue') }}</th>
                <th>{{ t('reports.table.avgOrderValue') }}</th>
                <th>{{ t('reports.table.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ formatCount(q.total_orders) }}</td>
                <td>{{ formatCurrency(q.total_revenue, currentCurrency) }}</td>
                <td>{{ formatCurrency(q.avg_order_value, currentCurrency) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="loading">{{ t('reports.noData') }}</div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyRevenueTrend') }}</h3>
        </div>
        <div v-if="monthlyData.length" class="chart-container">
          <div class="bar-chart">
            <div v-for="m in monthlyData" :key="m.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(m.revenue) + 'px' }"
                  :title="formatCurrency(m.revenue, currentCurrency)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(m.month) }}</div>
            </div>
          </div>
        </div>
        <div v-else class="loading">{{ t('reports.noData') }}</div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth') }}</h3>
        </div>
        <div v-if="monthlyRows.length" class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.table.month') }}</th>
                <th>{{ t('reports.table.orders') }}</th>
                <th>{{ t('reports.table.revenue') }}</th>
                <th>{{ t('reports.table.change') }}</th>
                <th>{{ t('reports.table.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in monthlyRows" :key="m.month">
                <td><strong>{{ formatMonth(m.month) }}</strong></td>
                <td>{{ formatCount(m.order_count) }}</td>
                <td>{{ formatCurrency(m.revenue, currentCurrency) }}</td>
                <td>
                  <span :class="m.changeClass">{{ m.changeDisplay }}</span>
                </td>
                <td>
                  <span :class="m.changeClass">{{ m.growthDisplay }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="loading">{{ t('reports.noData') }}</div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalRevenueYTD') }}</div>
          <div class="stat-value">{{ formatCurrency(totalRevenue, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(avgMonthlyRevenue, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalOrdersYTD') }}</div>
          <div class="stat-value">{{ formatCount(totalOrders) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()

        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])

        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        console.error('Error loading reports:', err)
        error.value = t('reports.loadError')
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    // Max monthly revenue computed once for bar-height scaling
    const maxRevenue = computed(() => {
      if (!monthlyData.value.length) return 0
      return Math.max(...monthlyData.value.map(m => m.revenue))
    })

    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0
      return (revenue / maxRevenue.value) * 200
    }

    // Enriched monthly rows carrying month-over-month change relative to the
    // previous month, so the template needs no index arithmetic.
    const monthlyRows = computed(() => {
      const cur = currentCurrency.value
      return monthlyData.value.map((m, i) => {
        const prev = i > 0 ? monthlyData.value[i - 1] : null
        let changeDisplay = '—'
        let growthDisplay = '—'
        let changeClass = ''

        if (prev) {
          const diff = m.revenue - prev.revenue
          if (diff > 0) {
            changeDisplay = '+' + formatCurrency(diff, cur)
            changeClass = 'positive-change'
          } else if (diff < 0) {
            changeDisplay = '-' + formatCurrency(Math.abs(diff), cur)
            changeClass = 'negative-change'
          } else {
            changeDisplay = formatCurrency(0, cur)
          }

          if (prev.revenue !== 0) {
            const rate = (diff / prev.revenue) * 100
            const sign = rate > 0 ? '+' : ''
            growthDisplay = sign + rate.toFixed(1) + '%'
          }
        }

        return {
          month: m.month,
          order_count: m.order_count,
          revenue: m.revenue,
          changeDisplay,
          growthDisplay,
          changeClass
        }
      })
    })

    // Derived summary stats
    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
    )

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length ? totalRevenue.value / monthlyData.value.length : 0
    )

    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
    )

    const bestQuarter = computed(() => {
      if (!quarterlyData.value.length) return '—'
      let best = null
      for (const q of quarterlyData.value) {
        if (!best || q.total_revenue > best.total_revenue) {
          best = q
        }
      }
      return best ? best.quarter : '—'
    })

    const formatCount = (n) => {
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return Number(n).toLocaleString(locale)
    }

    const formatMonth = (monthStr) => {
      if (typeof monthStr !== 'string') return monthStr
      const parts = monthStr.split('-')
      if (parts.length < 2) return monthStr

      const year = parts[0]
      const monthIndex = parseInt(parts[1], 10) - 1
      const keys = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

      if (isNaN(monthIndex) || monthIndex < 0 || monthIndex > 11) {
        return monthStr
      }

      return t('months.' + keys[monthIndex]) + ' ' + year
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) {
        return 'badge success'
      } else if (rate >= 75) {
        return 'badge warning'
      } else {
        return 'badge danger'
      }
    }

    onMounted(loadData)

    return {
      t,
      currentCurrency,
      loading,
      error,
      quarterlyData,
      monthlyData,
      monthlyRows,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      getBarHeight,
      getFulfillmentClass,
      formatCount,
      formatMonth,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.card {
  background: white;
  border-radius: 0;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #161616;
  margin: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: #f4f4f4;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #6f6f6f;
  border-bottom: 2px solid #e0e0e0;
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e0e0e0;
}

.reports-table tr:hover {
  background: #f4f4f4;
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
  background: linear-gradient(to top, #0f62fe, #4589ff);
  border-radius: 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, #0043ce, #0f62fe);
}

.bar-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #6f6f6f;
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 0;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #0f62fe;
}

.stat-label {
  font-size: 0.875rem;
  color: #6f6f6f;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #161616;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.success {
  background: #defbe6;
  color: #0e6027;
}

.badge.warning {
  background: #fcf4d6;
  color: #684e00;
}

.badge.danger {
  background: #ffd7d9;
  color: #a2191f;
}

.positive-change {
  color: #0e6027;
  font-weight: 600;
}

.negative-change {
  color: #da1e28;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #6f6f6f;
}

.error {
  background: #ffd7d9;
  color: #a2191f;
  padding: 1rem;
  border-radius: 0;
  margin: 1rem 0;
}
</style>
