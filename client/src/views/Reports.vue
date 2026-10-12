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
          <table class="reports-table" role="table" aria-label="Quarterly performance data">
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
              <tr v-for="(q, index) in quarterlyData" :key="index">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ currencySymbol }}{{ q.total_revenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</td>
                <td>{{ currencySymbol }}{{ q.avg_order_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</td>
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
          <h3 class="card-title">{{ t('reports.monthlyRevenueTrend') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart" role="img" :aria-label="t('reports.monthlyRevenueTrendAria')">
            <div v-for="(month, index) in monthlyData" :key="index" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="currencySymbol + month.revenue.toLocaleString()"
                  :aria-label="`${formatMonth(month.month)}: ${currencySymbol}${month.revenue.toLocaleString()}`"
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
          <h3 class="card-title">{{ t('reports.monthOverMonthAnalysis') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table" role="table" aria-label="Month-over-month comparison">
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
              <tr v-for="(month, index) in monthlyData" :key="index">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td>{{ month.order_count }}</td>
                <td>{{ currencySymbol }}{{ month.revenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
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
          <div class="stat-label">{{ t('reports.stats.totalRevenueYTD') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalRevenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ avgMonthlyRevenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalOrdersYTD') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestPerformingQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

const { t, currentCurrency } = useI18n()
const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus } = useFilters()

const loading = ref(true)
const error = ref(null)
const quarterlyData = ref([])
const monthlyData = ref([])

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const totalRevenue = computed(() => {
  return monthlyData.value.reduce((sum, month) => sum + month.revenue, 0)
})

const avgMonthlyRevenue = computed(() => {
  if (monthlyData.value.length === 0) return 0
  return totalRevenue.value / monthlyData.value.length
})

const totalOrders = computed(() => {
  return monthlyData.value.reduce((sum, month) => sum + month.order_count, 0)
})

const bestQuarter = computed(() => {
  if (quarterlyData.value.length === 0) return '-'

  let best = quarterlyData.value[0]
  for (const q of quarterlyData.value) {
    if (q.total_revenue > best.total_revenue) {
      best = q
    }
  }
  return best.quarter
})

const loadData = async () => {
  try {
    loading.value = true
    error.value = null

    // Build query parameters from filters
    const params = new URLSearchParams()
    if (selectedPeriod.value && selectedPeriod.value !== 'all') {
      params.append('month', selectedPeriod.value)
    }
    if (selectedLocation.value && selectedLocation.value !== 'all') {
      params.append('warehouse', selectedLocation.value)
    }
    if (selectedCategory.value && selectedCategory.value !== 'all') {
      params.append('category', selectedCategory.value)
    }
    if (selectedStatus.value && selectedStatus.value !== 'all') {
      params.append('status', selectedStatus.value)
    }

    const queryString = params.toString()
    const suffix = queryString ? `?${queryString}` : ''

    // Fetch data with filters
    const [quarterlyResponse, monthlyResponse] = await Promise.all([
      api.getReportsQuarterly(suffix),
      api.getReportsMonthly(suffix)
    ])

    quarterlyData.value = quarterlyResponse
    monthlyData.value = monthlyResponse

  } catch (err) {
    console.error('Error loading reports:', err)
    error.value = t('common.errorLoading')
  } finally {
    loading.value = false
  }
}

const formatMonth = (monthStr) => {
  if (!monthStr) return ''

  const [year, month] = monthStr.split('-')
  const monthNames = [
    t('months.january'), t('months.february'), t('months.march'),
    t('months.april'), t('months.may'), t('months.june'),
    t('months.july'), t('months.august'), t('months.september'),
    t('months.october'), t('months.november'), t('months.december')
  ]

  const monthIndex = parseInt(month) - 1
  const monthName = monthNames[monthIndex] || month

  return `${monthName} ${year}`
}

const getBarHeight = (revenue) => {
  if (monthlyData.value.length === 0) return 0

  const maxRevenue = Math.max(...monthlyData.value.map(m => m.revenue))
  if (maxRevenue === 0) return 0

  return (revenue / maxRevenue) * 200
}

const getFulfillmentClass = (rate) => {
  if (rate >= 90) return 'badge success'
  if (rate >= 75) return 'badge warning'
  return 'badge danger'
}

const getChangeValue = (current, previous) => {
  const change = current - previous
  const absChange = Math.abs(change)
  const formatted = absChange.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})

  if (change > 0) return `+${currencySymbol.value}${formatted}`
  if (change < 0) return `-${currencySymbol.value}${formatted}`
  return `${currencySymbol.value}0.00`
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
  const sign = rate > 0 ? '+' : ''

  return `${sign}${rate.toFixed(1)}%`
}

// Watch for filter changes
watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
  loadData()
})

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.reports {
  padding: 0;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.5rem 0;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
  margin: 0;
}

.card {
  background: white;
  border-radius: 12px;
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
  color: #0f172a;
  margin: 0;
}

.table-container {
  overflow-x: auto;
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
  font-size: 0.813rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  color: #0f172a;
}

.reports-table tr:hover {
  background: #f8fafc;
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
  margin-top: 1.5rem;
  font-size: 0.75rem;
  color: #64748b;
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #3b82f6;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.success {
  background: #dcfce7;
  color: #166534;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.positive-change {
  color: #16a34a;
  font-weight: 600;
}

.negative-change {
  color: #dc2626;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 1.125rem;
}

.error {
  background: #fee2e2;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  border: 1px solid #fecaca;
}
</style>
