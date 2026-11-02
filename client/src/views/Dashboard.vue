<template>
  <div class="dashboard">
    <PageHeader title="Overview" />
    <FilterBar />

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <Card>
          <div class="kpi-label">{{ t('dashboard.kpi.inventoryTurnover') }}</div>
          <div class="kpi-value">4.2</div>
          <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 4.5 (-6.67%)</div>
          <div class="kpi-bar"><div class="kpi-bar-fill" style="width: 93%"></div></div>
        </Card>

        <Card>
          <div class="kpi-label">{{ t('dashboard.kpi.ordersFulfilled') }}</div>
          <div class="kpi-value">{{ ordersData.fulfilled }}</div>
          <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: {{ ordersData.goal }} ({{ calculatePercentage(ordersData.fulfilled, ordersData.goal) }}%)</div>
          <div class="kpi-bar"><div class="kpi-bar-fill" :style="{ width: calculatePercentage(ordersData.fulfilled, ordersData.goal) + '%' }"></div></div>
        </Card>

        <Card>
          <div class="kpi-label">{{ t('dashboard.kpi.orderFillRate') }}</div>
          <div class="kpi-value">{{ fillRate }}%</div>
          <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 95% ({{ fillRate - 95 > 0 ? '+' : '' }}{{ (fillRate - 95).toFixed(2) }}%)</div>
          <div class="kpi-bar"><div class="kpi-bar-fill success" :style="{ width: (fillRate / 95 * 100) + '%' }"></div></div>
        </Card>

        <Card>
          <div class="kpi-label">{{ t(selectedPeriod === 'all' ? 'dashboard.kpi.revenueYTD' : 'dashboard.kpi.revenueMTD') }}</div>
          <div class="kpi-value">{{ formatCurrency(Math.round(summary.total_orders_value), selectedCurrency) }}</div>
          <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: {{ formatCurrency(revenueGoal, selectedCurrency) }} ({{ summary.total_orders_value > revenueGoal ? '+' : '' }}{{ ((summary.total_orders_value / revenueGoal - 1) * 100).toFixed(1) }}%)</div>
          <div class="kpi-bar"><div class="kpi-bar-fill" :style="{ width: Math.min((summary.total_orders_value / revenueGoal * 100), 100) + '%' }"></div></div>
        </Card>

        <Card>
          <div class="kpi-label">{{ t('dashboard.kpi.avgProcessingTime') }}</div>
          <div class="kpi-value">2.8</div>
          <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 3.0 (-6.67%)</div>
          <div class="kpi-bar"><div class="kpi-bar-fill success" style="width: 93%"></div></div>
        </Card>
      </div>

      <!-- Charts Grid -->
      <div class="charts-grid">
        <!-- Order Health -->
        <Card>
          <template #title>{{ t('dashboard.orderHealth.title') }}</template>
          <div class="order-health-container">
            <div class="order-health-chart">
              <svg viewBox="0 0 200 200" class="donut-svg">
                <circle cx="100" cy="100" r="65" fill="none" stroke="var(--line)" stroke-width="25"/>
                <circle cx="100" cy="100" r="65" fill="none" stroke="var(--success)" stroke-width="25"
                  :stroke-dasharray="`${getCircleSegment(statusData.delivered)} 408`"
                  stroke-dashoffset="0" transform="rotate(-90 100 100)"/>
                <circle cx="100" cy="100" r="65" fill="none" stroke="var(--accent)" stroke-width="25"
                  :stroke-dasharray="`${getCircleSegment(statusData.shipped)} 408`"
                  :stroke-dashoffset="`-${getCircleSegment(statusData.delivered)}`"
                  transform="rotate(-90 100 100)"/>
                <circle cx="100" cy="100" r="65" fill="none" stroke="var(--warn)" stroke-width="25"
                  :stroke-dasharray="`${getCircleSegment(statusData.processing)} 408`"
                  :stroke-dashoffset="`-${getCircleSegment(statusData.delivered) + getCircleSegment(statusData.shipped)}`"
                  transform="rotate(-90 100 100)"/>
                <circle cx="100" cy="100" r="65" fill="none" stroke="var(--danger)" stroke-width="25"
                  :stroke-dasharray="`${getCircleSegment(statusData.backordered)} 408`"
                  :stroke-dashoffset="`-${getCircleSegment(statusData.delivered) + getCircleSegment(statusData.shipped) + getCircleSegment(statusData.processing)}`"
                  transform="rotate(-90 100 100)"/>
                <text x="100" y="92" text-anchor="middle" class="donut-center-label">{{ t('dashboard.orderHealth.total') }}</text>
                <text x="100" y="118" text-anchor="middle" class="donut-center-value">{{ orderHealthMetrics.totalOrders }}</text>
              </svg>
              <div class="donut-legend">
                <div class="legend-item"><span class="legend-dot" style="background: var(--success)"></span>{{ t('status.delivered') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background: var(--accent)"></span>{{ t('status.shipped') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background: var(--warn)"></span>{{ t('status.processing') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background: var(--danger)"></span>{{ t('status.backordered') }}</div>
              </div>
            </div>

            <div class="order-health-metrics">
              <div class="health-metric">
                <div class="health-metric-label">{{ t('dashboard.orderHealth.revenue') }}</div>
                <div class="health-metric-value">{{ formatCurrency(orderHealthMetrics.totalValue, selectedCurrency) }}</div>
              </div>
              <div class="health-metric">
                <div class="health-metric-label">{{ t('dashboard.orderHealth.avgOrderValue') }}</div>
                <div class="health-metric-value">{{ formatCurrency(orderHealthMetrics.avgOrderValue, selectedCurrency) }}</div>
              </div>
              <div class="health-metric">
                <div class="health-metric-label">{{ t('dashboard.orderHealth.onTimeRate') }}</div>
                <div class="health-metric-value" :class="{ 'metric-good': orderHealthMetrics.onTimeRate >= 90, 'metric-warning': orderHealthMetrics.onTimeRate < 90 && orderHealthMetrics.onTimeRate >= 75, 'metric-bad': orderHealthMetrics.onTimeRate < 75 }">
                  {{ orderHealthMetrics.onTimeRate.toFixed(1) }}%
                </div>
              </div>
              <div class="health-metric">
                <div class="health-metric-label">{{ t('dashboard.orderHealth.avgFulfillmentDays') }}</div>
                <div class="health-metric-value">{{ orderHealthMetrics.avgFulfillmentDays.toFixed(1) }}</div>
              </div>
            </div>
          </div>
        </Card>

        <!-- Inventory by Category -->
        <Card>
          <template #title>{{ t('dashboard.inventoryValue.title') }}</template>
          <div class="horizontal-bar-chart" v-if="categoryData.length > 0">
            <div v-for="cat in categoryData" :key="cat.name" class="h-bar-item">
              <div class="h-bar-label">{{ translateCategory(cat.name) }}</div>
              <div class="h-bar-track">
                <div class="h-bar-fill" :style="{ width: (cat.value / maxCategoryValue * 100) + '%' }">
                  <span class="h-bar-value">{{ selectedCurrency === 'JPY' ? formatCurrency(cat.value, selectedCurrency) : `$${(cat.value / 1000).toFixed(1)}K` }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-data">{{ t('dashboard.inventoryShortages.noData') }}</div>
        </Card>

        <!-- Inventory Shortages -->
        <Card class="full-width">
          <template #title>{{ t('dashboard.inventoryShortages.title') }} ({{ backlogItems.length }})</template>
          <EmptyState v-if="backlogItems.length === 0">
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="40" height="40" style="color: var(--success)">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
            </template>
            <template #title>{{ t('dashboard.inventoryShortages.noShortages') }}</template>
          </EmptyState>
          <div v-else class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('dashboard.inventoryShortages.orderId') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.sku') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.itemName') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.quantityNeeded') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.quantityAvailable') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.shortage') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.daysDelayed') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.priority') }}</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in backlogItems" :key="item.id">
                  <td @click="showBacklogDetail(item)" style="cursor: pointer;"><strong>{{ item.order_id }}</strong></td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer;"><strong>{{ item.item_sku }}</strong></td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer;">{{ translateProductName(item.item_name) }}</td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer;">{{ item.quantity_needed }}</td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer;">{{ item.quantity_available }}</td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer;">
                    <Badge variant="danger">{{ Math.abs(item.quantity_needed - item.quantity_available) }} {{ t('dashboard.inventoryShortages.unitsShort') }}</Badge>
                  </td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer;">
                    <span :style="{ color: item.days_delayed > 7 ? 'var(--danger)' : 'var(--warn)', fontWeight: 600 }">
                      {{ item.days_delayed }} {{ t('dashboard.inventoryShortages.days') }}
                    </span>
                  </td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer;">
                    <Badge :variant="item.priority === 'high' ? 'danger' : item.priority === 'medium' ? 'warn' : 'accent'">
                      {{ translatePriority(item.priority) }}
                    </Badge>
                  </td>
                  <td>
                    <Button
                      v-if="!item.purchase_order_id"
                      variant="primary"
                      size="sm"
                      @click.stop="openPOModal(item)"
                    >Create PO</Button>
                    <Button
                      v-else
                      variant="secondary"
                      size="sm"
                      @click.stop="viewPO(item)"
                    >View PO</Button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>

        <!-- Top Products -->
        <Card class="full-width">
          <template #title>{{ t('dashboard.topProducts.title') }}</template>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('dashboard.topProducts.product') }}</th>
                  <th>{{ t('dashboard.topProducts.sku') }}</th>
                  <th>{{ t('dashboard.topProducts.category') }}</th>
                  <th>{{ t('dashboard.topProducts.unitsOrdered') }}</th>
                  <th>{{ t('dashboard.topProducts.revenue') }}</th>
                  <th>{{ t('dashboard.topProducts.firstOrder') }}</th>
                  <th>{{ t('dashboard.topProducts.stockStatus') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in topProducts"
                  :key="item.sku"
                  class="clickable-row"
                  @click="showProductDetail(item)"
                >
                  <td><strong>{{ translateProductName(item.name) }}</strong></td>
                  <td>{{ item.sku }}</td>
                  <td>{{ translateCategory(item.category) }}</td>
                  <td>{{ item.unitsOrdered }}</td>
                  <td><strong>{{ formatCurrency(item.revenue, selectedCurrency) }}</strong></td>
                  <td>{{ formatDate(item.firstOrderDate) }}</td>
                  <td>
                    <Badge :variant="getStockBadge(item.stockLevel)">
                      {{ translateStockLevel(item.stockLevel) }}
                    </Badge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>

    <ProductDetailModal
      :is-open="showProductModal"
      :product="selectedProduct"
      @close="showProductModal = false"
    />

    <BacklogDetailModal
      :is-open="showBacklogModal"
      :backlog-item="selectedBacklogItem"
      @close="showBacklogModal = false"
    />

  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'
import PageHeader from '../components/ui/PageHeader.vue'
import Card from '../components/ui/Card.vue'
import Badge from '../components/ui/Badge.vue'
import Button from '../components/ui/Button.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import FilterBar from '../components/FilterBar.vue'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import BacklogDetailModal from '../components/BacklogDetailModal.vue'

export default {
  name: 'Dashboard',
  components: {
    PageHeader,
    Card,
    Badge,
    Button,
    EmptyState,
    FilterBar,
    ProductDetailModal,
    BacklogDetailModal
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const summary = ref({})
    const allOrders = ref([])
    const inventoryItems = ref([])

    const showProductModal = ref(false)
    const selectedProduct = ref(null)
    const showBacklogModal = ref(false)
    const selectedBacklogItem = ref(null)
    const showPOModal = ref(false)
    const selectedBacklogForPO = ref(null)
    const poModalMode = ref('create')

    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const ordersData = ref({ fulfilled: 187, goal: 200 })
    const fillRate = ref(96.8)

    const revenueGoal = computed(() => {
      const monthlyGoal = 800000
      if (selectedPeriod.value === 'all') {
        return monthlyGoal * 12
      }
      return monthlyGoal
    })

    const statusData = computed(() => {
      const counts = { delivered: 0, shipped: 0, processing: 0, backordered: 0 }
      allOrders.value.forEach(order => {
        const status = order.status.toLowerCase()
        if (counts[status] !== undefined) counts[status]++
      })
      return counts
    })

    const orderHealthMetrics = computed(() => {
      const totalOrders = allOrders.value.length
      const totalValue = allOrders.value.reduce((sum, order) => sum + (order.total_value || 0), 0)
      const avgOrderValue = totalOrders > 0 ? totalValue / totalOrders : 0

      const deliveredOrders = allOrders.value.filter(o => o.status.toLowerCase() === 'delivered')
      const onTimeDeliveries = deliveredOrders.filter(o => {
        if (o.actual_delivery && o.expected_delivery) {
          return new Date(o.actual_delivery) <= new Date(o.expected_delivery)
        }
        return false
      }).length
      const onTimeRate = deliveredOrders.length > 0 ? (onTimeDeliveries / deliveredOrders.length) * 100 : 0

      let totalDays = 0
      let countWithDates = 0
      deliveredOrders.forEach(o => {
        if (o.order_date && o.actual_delivery) {
          const orderDate = new Date(o.order_date)
          const deliveryDate = new Date(o.actual_delivery)
          const days = Math.round((deliveryDate - orderDate) / (1000 * 60 * 60 * 24))
          totalDays += days
          countWithDates++
        }
      })
      const avgFulfillmentDays = countWithDates > 0 ? totalDays / countWithDates : 0

      return { totalOrders, totalValue, avgOrderValue, onTimeRate, avgFulfillmentDays }
    })

    const categoryData = computed(() => {
      const categoryMap = {}
      const orderedSkus = new Set()
      allOrders.value.forEach(order => {
        if (order.items) {
          order.items.forEach(item => orderedSkus.add(item.sku))
        }
      })

      const itemsToInclude = selectedPeriod.value === 'all'
        ? inventoryItems.value
        : inventoryItems.value.filter(item => orderedSkus.has(item.sku))

      itemsToInclude.forEach(item => {
        const cat = item.category.toLowerCase()
        if (!categoryMap[cat]) {
          categoryMap[cat] = { name: item.category, value: 0, count: 0 }
        }
        categoryMap[cat].value += item.quantity_on_hand * item.unit_cost
        categoryMap[cat].count += 1
      })

      return Object.values(categoryMap)
    })

    const maxCategoryValue = computed(() => {
      if (categoryData.value.length === 0) return 1
      return Math.max(...categoryData.value.map(c => c.value))
    })

    const topProducts = computed(() => {
      const productMap = {}

      allOrders.value.forEach(order => {
        if (order.items) {
          order.items.forEach(item => {
            const sku = item.sku
            const invItem = inventoryItems.value.find(i => i.sku === sku)

            if (!invItem && (selectedLocation.value !== 'all' || selectedCategory.value !== 'all')) {
              return
            }

            if (!productMap[sku]) {
              productMap[sku] = {
                name: item.name,
                sku,
                category: invItem?.category || 'Unknown',
                warehouse: invItem?.warehouse || 'Unknown',
                unitsOrdered: 0,
                revenue: 0,
                stockLevel: invItem ? (invItem.quantity_on_hand > invItem.reorder_point ? 'In Stock' : 'Low Stock') : 'Unknown',
                firstOrderDate: order.order_date
              }
            } else {
              if (order.order_date && (!productMap[sku].firstOrderDate || order.order_date < productMap[sku].firstOrderDate)) {
                productMap[sku].firstOrderDate = order.order_date
              }
            }
            productMap[sku].unitsOrdered += item.quantity
            productMap[sku].revenue += item.quantity * item.unit_price
          })
        }
      })

      return Object.values(productMap)
        .sort((a, b) => {
          const dateA = new Date(a.firstOrderDate || '9999-12-31')
          const dateB = new Date(b.firstOrderDate || '9999-12-31')
          if (dateA.getTime() !== dateB.getTime()) {
            return dateA.getTime() - dateB.getTime()
          }
          return b.revenue - a.revenue
        })
        .slice(0, 12)
    })

    const allBacklogItems = ref([])

    const backlogItems = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allBacklogItems.value
      }
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allBacklogItems.value.filter(b => validSkus.has(b.item_sku))
    })

    const loadData = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [summaryData, ordersData, inventoryData, backlogData] = await Promise.all([
          api.getDashboardSummary(filters),
          api.getOrders(filters),
          api.getInventory(filters),
          api.getBacklog()
        ])

        summary.value = summaryData
        allOrders.value = ordersData
        inventoryItems.value = inventoryData
        allBacklogItems.value = backlogData
      } catch (err) {
        error.value = 'Failed to load dashboard data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const calculatePercentage = (value, goal) => {
      return ((value / goal) * 100).toFixed(2)
    }

    const totalOrders = computed(() => {
      return statusData.value.delivered + statusData.value.shipped +
             statusData.value.processing + statusData.value.backordered
    })

    const getCircleSegment = (value) => {
      return totalOrders.value > 0 ? (value / totalOrders.value) * 440 : 0
    }

    const getStockBadge = (level) => {
      if (level === 'In Stock') return 'success'
      if (level === 'Low Stock') return 'warn'
      return 'danger'
    }

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    const translateStockLevel = (stockLevel) => {
      const stockMap = {
        'In Stock': t('status.inStock'),
        'Low Stock': t('status.lowStock')
      }
      return stockMap[stockLevel] || stockLevel
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low'),
        'High': t('priority.high'),
        'Medium': t('priority.medium'),
        'Low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      const date = new Date(dateString)
      return date.toLocaleDateString(locale, { month: 'short', day: 'numeric', year: 'numeric' })
    }

    const showProductDetail = (product) => {
      selectedProduct.value = product
      showProductModal.value = true
    }

    const showBacklogDetail = (item) => {
      selectedBacklogItem.value = item
      showBacklogModal.value = true
    }

    const openPOModal = (item) => {
      selectedBacklogForPO.value = item
      poModalMode.value = 'create'
      showPOModal.value = true
    }

    const viewPO = (item) => {
      selectedBacklogForPO.value = item
      poModalMode.value = 'view'
      showPOModal.value = true
    }

    const handlePOCreated = (poData) => {
      const item = allBacklogItems.value.find(b => b.id === poData.backlog_item_id)
      if (item) {
        item.purchase_order_id = poData.id
        item.purchase_order = poData
      }
      showPOModal.value = false
    }

    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      summary,
      ordersData,
      fillRate,
      statusData,
      orderHealthMetrics,
      categoryData,
      maxCategoryValue,
      topProducts,
      backlogItems,
      calculatePercentage,
      getCircleSegment,
      getStockBadge,
      translateCategory,
      translateStockLevel,
      translatePriority,
      formatDate,
      revenueGoal,
      showProductModal,
      selectedProduct,
      showProductDetail,
      showBacklogModal,
      selectedBacklogItem,
      showBacklogDetail,
      selectedPeriod,
      selectedCurrency: currentCurrency,
      formatCurrency,
      Math,
      translateProductName,
      translateWarehouse,
      showPOModal,
      selectedBacklogForPO,
      poModalMode,
      openPOModal,
      viewPO
    }
  }
}
</script>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.kpi-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--ink-primary);
  line-height: 1.25;
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}

.kpi-goal {
  font-size: 12px;
  color: var(--ink-muted);
  margin-bottom: 12px;
}

.kpi-bar {
  width: 100%;
  height: 4px;
  background: var(--surface-muted);
  border-radius: 2px;
  overflow: hidden;
}

.kpi-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.6s ease;
}

.kpi-bar-fill.success {
  background: var(--success);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.full-width {
  grid-column: 1 / -1;
}

/* Order health */
.order-health-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: center;
  min-height: 0;
}

.order-health-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.donut-svg {
  width: 240px;
  height: 240px;
}

.donut-center-label {
  font-size: 11px;
  fill: var(--ink-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.donut-center-value {
  font-size: 32px;
  fill: var(--ink-primary);
  font-weight: 700;
}

.donut-legend {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ink-secondary);
  font-weight: 500;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.order-health-metrics {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.health-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.health-metric-label {
  font-size: 11px;
  color: var(--ink-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.health-metric-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--ink-primary);
  letter-spacing: -0.02em;
}

.metric-good { color: var(--success); }
.metric-warning { color: var(--warn); }
.metric-bad { color: var(--danger); }

/* Horizontal bar chart */
.horizontal-bar-chart {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0;
}

.h-bar-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.h-bar-label {
  width: 64px;
  min-width: 64px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-muted);
  flex-shrink: 0;
}

.h-bar-track {
  flex: 1;
  height: 32px;
  background: var(--surface-muted);
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  overflow: hidden;
}

.h-bar-fill {
  height: 100%;
  background: var(--ink-muted);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 12px;
  transition: width 0.6s ease;
  min-width: 40px;
}

.h-bar-value {
  font-size: 11px;
  font-weight: 700;
  color: white;
}

.no-data {
  padding: 32px;
  text-align: center;
  color: var(--ink-muted);
  font-size: 13px;
}

.clickable-row {
  cursor: pointer;
}

.clickable-row:hover {
  background: var(--surface-muted) !important;
}
</style>
