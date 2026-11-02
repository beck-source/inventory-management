<template>
  <div class="reports">
    <PageHeader title="Performance Reports" />
    <FilterBar />

    <div v-if="loading" class="loading">Loading reports...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <Card class="gap-4 section-card">
        <CardHeader><CardTitle>Quarterly Performance</CardTitle></CardHeader>
        <CardContent>
          <div class="table-no-pad">
            <Table class="reports-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Quarter</TableHead>
                  <TableHead>Total Orders</TableHead>
                  <TableHead>Total Revenue</TableHead>
                  <TableHead>Avg Order Value</TableHead>
                  <TableHead>Fulfillment Rate</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="q in quarterlyData" :key="q.quarter">
                  <TableCell><strong>{{ q.quarter }}</strong></TableCell>
                  <TableCell>{{ q.total_orders }}</TableCell>
                  <TableCell>${{ formatNumber(q.total_revenue) }}</TableCell>
                  <TableCell>${{ formatNumber(q.avg_order_value) }}</TableCell>
                  <TableCell>
                    <Badge :variant="getFulfillmentVariant(q.fulfillment_rate)">
                      {{ q.fulfillment_rate }}%
                    </Badge>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <!-- Monthly Revenue Trend -->
      <Card class="gap-4 section-card">
        <CardHeader><CardTitle>Monthly Revenue Trend</CardTitle></CardHeader>
        <CardContent>
          <div class="chart-container">
            <div class="bar-chart">
              <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
                <div class="bar-container">
                  <div
                    class="bar"
                    :style="{ height: getBarHeight(month.revenue) + 'px' }"
                    :title="'$' + formatNumber(month.revenue)"
                  ></div>
                </div>
                <div class="bar-label">{{ formatMonth(month.month) }}</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Month-over-Month -->
      <Card class="gap-4 section-card">
        <CardHeader><CardTitle>Month-over-Month Analysis</CardTitle></CardHeader>
        <CardContent>
          <div class="table-no-pad">
            <Table class="reports-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Month</TableHead>
                  <TableHead>Orders</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>Growth Rate</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="(month, index) in monthlyData" :key="month.month">
                  <TableCell><strong>{{ formatMonth(month.month) }}</strong></TableCell>
                  <TableCell>{{ month.order_count }}</TableCell>
                  <TableCell>${{ formatNumber(month.revenue) }}</TableCell>
                  <TableCell>
                    <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                      {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                    </span>
                    <span v-else>-</span>
                  </TableCell>
                  <TableCell>
                    <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                      {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
                    </span>
                    <span v-else>-</span>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <Card>
          <CardContent>
            <div class="stat-label">Total Revenue (YTD)</div>
            <div class="stat-value">${{ formatNumber(totalRevenue) }}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div class="stat-label">Avg Monthly Revenue</div>
            <div class="stat-value">${{ formatNumber(avgMonthlyRevenue) }}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div class="stat-label">Total Orders (YTD)</div>
            <div class="stat-value">{{ totalOrders }}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div class="stat-label">Best Performing Quarter</div>
            <div class="stat-value quarter-value">{{ bestQuarter }}</div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import PageHeader from '../components/ui/PageHeader.vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import FilterBar from '../components/FilterBar.vue'

export default {
  name: 'Reports',
  components: {
    PageHeader,
    Card,
    CardHeader,
    CardTitle,
    CardContent,
    Table,
    TableHeader,
    TableBody,
    TableRow,
    TableHead,
    TableCell,
    Badge,
    FilterBar
  },
  data() {
    return {
      loading: true,
      error: null,
      quarterlyData: [],
      monthlyData: [],
      totalRevenue: 0,
      avgMonthlyRevenue: 0,
      totalOrders: 0,
      bestQuarter: ''
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    async loadData() {
      try {
        this.loading = true

        const quarterlyResponse = await axios.get('http://localhost:8001/api/reports/quarterly')
        this.quarterlyData = quarterlyResponse.data

        const monthlyResponse = await axios.get('http://localhost:8001/api/reports/monthly-trends')
        this.monthlyData = monthlyResponse.data

        this.calculateSummaryStats()
      } catch (err) {
        this.error = 'Failed to load reports: ' + err.message
      } finally {
        this.loading = false
      }
    },

    calculateSummaryStats() {
      var total = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        total = total + this.monthlyData[i].revenue
      }
      this.totalRevenue = total

      if (this.monthlyData.length > 0) {
        this.avgMonthlyRevenue = total / this.monthlyData.length
      } else {
        this.avgMonthlyRevenue = 0
      }

      var orders = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        orders = orders + this.monthlyData[i].order_count
      }
      this.totalOrders = orders

      var bestQ = ''
      var bestRevenue = 0
      for (var i = 0; i < this.quarterlyData.length; i++) {
        if (this.quarterlyData[i].total_revenue > bestRevenue) {
          bestRevenue = this.quarterlyData[i].total_revenue
          bestQ = this.quarterlyData[i].quarter
        }
      }
      this.bestQuarter = bestQ
    },

    formatNumber(num) {
      var str = num.toString()
      var parts = str.split('.')
      var intPart = parts[0]
      var decPart = parts.length > 1 ? parts[1] : '00'

      var formatted = ''
      var count = 0
      for (var i = intPart.length - 1; i >= 0; i--) {
        if (count > 0 && count % 3 === 0) {
          formatted = ',' + formatted
        }
        formatted = intPart[i] + formatted
        count++
      }

      if (decPart.length === 1) decPart = decPart + '0'
      if (decPart.length > 2) decPart = decPart.substring(0, 2)
      return formatted + '.' + decPart
    },

    formatMonth(monthStr) {
      var parts = monthStr.split('-')
      var month = parts[1]
      var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      var monthIndex = parseInt(month) - 1
      return monthNames[monthIndex]
    },

    getBarHeight(revenue) {
      var maxRevenue = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        if (this.monthlyData[i].revenue > maxRevenue) {
          maxRevenue = this.monthlyData[i].revenue
        }
      }
      if (maxRevenue === 0) return 0
      return (revenue / maxRevenue) * 200
    },

    getFulfillmentVariant(rate) {
      if (rate >= 90) return 'success'
      if (rate >= 75) return 'warn'
      return 'danger'
    },

    getChangeValue(current, previous) {
      var change = current - previous
      if (change > 0) return '+$' + this.formatNumber(change)
      if (change < 0) return '-$' + this.formatNumber(Math.abs(change))
      return '$0.00'
    },

    getChangeClass(current, previous) {
      var change = current - previous
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    },

    getGrowthRate(current, previous) {
      if (previous === 0) return 'N/A'
      var rate = ((current - previous) / previous) * 100
      var sign = rate > 0 ? '+' : ''
      return sign + rate.toFixed(1) + '%'
    }
  }
}
</script>

<style scoped>
.section-card {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
  gap: 24px;
}

.stat-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--ink-primary);
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.quarter-value {
  font-size: 24px;
}

.table-no-pad {
  margin: 0 calc(-1 * var(--sp-6));
  margin-bottom: calc(-1 * var(--sp-6));
}

.reports-table {
  width: 100%;
}

.chart-container {
  padding: 32px 16px;
  min-height: 240px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 240px;
  gap: 8px;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 64px;
}

.bar-container {
  height: 240px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: var(--accent);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
  min-height: 4px;
}

.bar:hover {
  background: var(--accent-2);
}

.bar-label {
  margin-top: 24px;
  font-size: 11px;
  color: var(--ink-muted);
  text-align: center;
  font-weight: 500;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.positive-change {
  color: var(--success);
  font-weight: 600;
}

.negative-change {
  color: var(--danger);
  font-weight: 600;
}
</style>
