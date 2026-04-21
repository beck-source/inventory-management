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
        <div class="table-container">
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
              <tr v-for="q in filteredQuarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
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
      </div>

      <!-- Monthly Revenue Trend Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyRevenueTrend') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="month in filteredMonthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatCurrency(month.revenue, currentCurrency)"
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
          <h3 class="card-title">{{ t('reports.monthOverMonth') }}</h3>
        </div>
        <div class="table-container">
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
              <tr v-for="(month, index) in filteredMonthlyData" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td>{{ month.order_count }}</td>
                <td>{{ formatCurrency(month.revenue, currentCurrency) }}</td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, filteredMonthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, filteredMonthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, filteredMonthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, filteredMonthlyData[index - 1].revenue) }}
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
          <div class="stat-label">{{ t('reports.totalRevenueYTD') }}</div>
          <div class="stat-value">{{ formatCurrency(totalRevenue, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(avgMonthlyRevenue, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.totalOrdersYTD') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.bestPerformingQuarter') }}</div>
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
    const { t, currentCurrency } = useI18n()
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus
    } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const allQuarterlyData = ref([])
    const allMonthlyData = ref([])

    // Map period string to quarter identifier: 'Q1-2025', 'Q2-2025', etc.
    const periodToQuarter = (period) => {
      if (!period || period === 'all') return null
      // If it's already a quarter string like 'Q1-2025'
      if (/^Q[1-4]-\d{4}$/.test(period)) return period
      // If it's a YYYY-MM string, find the quarter
      const match = period.match(/^(\d{4})-(\d{2})$/)
      if (match) {
        const month = parseInt(match[2], 10)
        const year = match[1]
        const quarter = Math.ceil(month / 3)
        return `Q${quarter}-${year}`
      }
      return null
    }

    // Filter quarterly data based on selected period
    const filteredQuarterlyData = computed(() => {
      if (selectedPeriod.value === 'all') return allQuarterlyData.value
      const quarter = periodToQuarter(selectedPeriod.value)
      if (!quarter) return allQuarterlyData.value
      return allQuarterlyData.value.filter(q => q.quarter === quarter)
    })

    // Filter monthly data based on selected period
    const filteredMonthlyData = computed(() => {
      if (selectedPeriod.value === 'all') return allMonthlyData.value
      // If period is a quarter like 'Q1-2025', show months Jan/Feb/Mar 2025
      if (/^Q[1-4]-\d{4}$/.test(selectedPeriod.value)) {
        const qMatch = selectedPeriod.value.match(/^Q([1-4])-(\d{4})$/)
        if (qMatch) {
          const quarter = parseInt(qMatch[1], 10)
          const year = qMatch[2]
          const startMonth = (quarter - 1) * 3 + 1
          const months = [startMonth, startMonth + 1, startMonth + 2].map(
            m => `${year}-${String(m).padStart(2, '0')}`
          )
          return allMonthlyData.value.filter(m => months.includes(m.month))
        }
      }
      // If period is a single YYYY-MM month
      if (/^\d{4}-\d{2}$/.test(selectedPeriod.value)) {
        return allMonthlyData.value.filter(m => m.month === selectedPeriod.value)
      }
      return allMonthlyData.value
    })

    const totalRevenue = computed(() =>
      filteredMonthlyData.value.reduce((sum, m) => sum + (m.revenue || 0), 0)
    )

    const avgMonthlyRevenue = computed(() =>
      filteredMonthlyData.value.length > 0
        ? totalRevenue.value / filteredMonthlyData.value.length
        : 0
    )

    const totalOrders = computed(() =>
      filteredMonthlyData.value.reduce((sum, m) => sum + (m.order_count || 0), 0)
    )

    const bestQuarter = computed(() => {
      if (filteredQuarterlyData.value.length === 0) return '-'
      return filteredQuarterlyData.value.reduce(
        (best, q) => (q.total_revenue > best.total_revenue ? q : best),
        filteredQuarterlyData.value[0]
      ).quarter
    })

    const maxRevenue = computed(() => {
      if (filteredMonthlyData.value.length === 0) return 1
      return Math.max(...filteredMonthlyData.value.map(m => m.revenue || 0))
    })

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(),
          api.getMonthlyTrends()
        ])
        allQuarterlyData.value = quarterly
        allMonthlyData.value = monthly
      } catch (err) {
        error.value = t('reports.loadError')
        console.error('Failed to load reports:', err)
      } finally {
        loading.value = false
      }
    }

    const monthKeyMap = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    const formatMonth = (monthStr) => {
      if (!monthStr) return ''
      const parts = monthStr.split('-')
      if (parts.length !== 2) return monthStr
      const monthIndex = parseInt(parts[1], 10) - 1
      if (monthIndex < 0 || monthIndex > 11) return monthStr
      return t(`months.${monthKeyMap[monthIndex]}`) + ' ' + parts[0]
    }

    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0
      return (revenue / maxRevenue.value) * 200
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const getChangeValue = (current, previous) => {
      const change = current - previous
      if (change > 0) return '+' + formatCurrency(change, currentCurrency.value)
      if (change < 0) return '-' + formatCurrency(Math.abs(change), currentCurrency.value)
      return formatCurrency(0, currentCurrency.value)
    }

    const getChangeClass = (current, previous) => {
      const change = current - previous
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    const getGrowthRate = (current, previous) => {
      if (previous === 0) return 'N/A'
      const rate = ((current - previous) / previous) * 100
      return (rate > 0 ? '+' : '') + rate.toFixed(1) + '%'
    }

    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      filteredQuarterlyData,
      filteredMonthlyData,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      currentCurrency,
      formatCurrency,
      formatMonth,
      getBarHeight,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
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
  background: var(--color-accent);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: all 0.3s ease;
  cursor: pointer;
  opacity: 0.85;
}

.bar:hover {
  opacity: 1;
}

.bar-label {
  margin-top: 1.5rem;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.positive-change {
  color: var(--color-success);
  font-weight: 600;
}

.negative-change {
  color: var(--color-danger);
  font-weight: 600;
}
</style>
