<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>{{ t('dashboard.title') }}</h2>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Key Performance Indicators -->
      <div class="kpi-section">
        <h3 class="section-title">{{ t('dashboard.kpi.title') }}</h3>
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t('dashboard.kpi.inventoryTurnover') }}</span>
            </div>
            <div class="kpi-value">4.2</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 4.5 (-6.67%)</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" style="width: 93.33%"></div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t('dashboard.kpi.ordersFulfilled') }}</span>
            </div>
            <div class="kpi-value">{{ ordersData.fulfilled }}</div>
            <div class="kpi-goal">
              {{ t('dashboard.kpi.goal') }}: {{ ordersData.goal }} ({{
                calculatePercentage(ordersData.fulfilled, ordersData.goal)
              }}%)
            </div>
            <div class="kpi-progress-bar">
              <div
                class="kpi-progress"
                :style="{ width: calculatePercentage(ordersData.fulfilled, ordersData.goal) + '%' }"
              ></div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t('dashboard.kpi.orderFillRate') }}</span>
            </div>
            <div class="kpi-value">{{ fillRate }}%</div>
            <div class="kpi-goal">
              {{ t('dashboard.kpi.goal') }}: 95% ({{ fillRate - 95 > 0 ? '+' : '' }}{{ (fillRate - 95).toFixed(2) }}%)
            </div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress success" :style="{ width: (fillRate / 95) * 100 + '%' }"></div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{
                t(selectedPeriod === 'all' ? 'dashboard.kpi.revenueYTD' : 'dashboard.kpi.revenueMTD')
              }}</span>
            </div>
            <div class="kpi-value">{{ formatCurrency(Math.round(summary.total_orders_value), selectedCurrency) }}</div>
            <div class="kpi-goal">
              {{ t('dashboard.kpi.goal') }}: {{ formatCurrency(revenueGoal, selectedCurrency) }} ({{
                summary.total_orders_value > revenueGoal ? '+' : ''
              }}{{ ((summary.total_orders_value / revenueGoal - 1) * 100).toFixed(1) }}%)
            </div>
            <div class="kpi-progress-bar">
              <div
                class="kpi-progress"
                :style="{ width: Math.min((summary.total_orders_value / revenueGoal) * 100, 100) + '%' }"
              ></div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-label">{{ t('dashboard.kpi.avgProcessingTime') }}</span>
            </div>
            <div class="kpi-value">2.8</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 3.0 (-6.67%)</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress success" style="width: 93.33%"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary Section -->
      <div class="summary-section">
        <h3 class="section-title">{{ t('dashboard.summary.title') }}</h3>
      </div>

      <!-- Charts Grid -->
      <div class="charts-grid">
        <!-- Order Health Dashboard -->
        <div class="card chart-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.orderHealth.title') }}</h3>
          </div>
          <div class="chart-content">
            <div class="order-health-container">
              <!-- Left: Donut Chart -->
              <div class="order-health-chart">
                <svg viewBox="0 0 200 200" class="donut-svg-compact">
                  <circle cx="100" cy="100" r="65" fill="none" stroke="var(--border)" stroke-width="25" />
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="var(--success)"
                    stroke-width="25"
                    :stroke-dasharray="`${getCircleSegment(statusData.delivered)} 408`"
                    stroke-dashoffset="0"
                    transform="rotate(-90 100 100)"
                  />
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="var(--info)"
                    stroke-width="25"
                    :stroke-dasharray="`${getCircleSegment(statusData.shipped)} 408`"
                    :stroke-dashoffset="`-${getCircleSegment(statusData.delivered)}`"
                    transform="rotate(-90 100 100)"
                  />
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="var(--warning)"
                    stroke-width="25"
                    :stroke-dasharray="`${getCircleSegment(statusData.processing)} 408`"
                    :stroke-dashoffset="`-${getCircleSegment(statusData.delivered) + getCircleSegment(statusData.shipped)}`"
                    transform="rotate(-90 100 100)"
                  />
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="var(--danger)"
                    stroke-width="25"
                    :stroke-dasharray="`${getCircleSegment(statusData.backordered)} 408`"
                    :stroke-dashoffset="`-${getCircleSegment(statusData.delivered) + getCircleSegment(statusData.shipped) + getCircleSegment(statusData.processing)}`"
                    transform="rotate(-90 100 100)"
                  />
                  <text x="100" y="90" text-anchor="middle" class="donut-center-label">
                    {{ t('dashboard.orderHealth.total') }}
                  </text>
                  <text x="100" y="120" text-anchor="middle" class="donut-center-value">
                    {{ orderHealthMetrics.totalOrders }}
                  </text>
                </svg>
                <div class="donut-legend-compact">
                  <div class="legend-item-compact">
                    <span class="legend-dot" style="background: var(--success)"></span>{{ t('status.delivered') }}
                  </div>
                  <div class="legend-item-compact">
                    <span class="legend-dot" style="background: var(--info)"></span>{{ t('status.shipped') }}
                  </div>
                  <div class="legend-item-compact">
                    <span class="legend-dot" style="background: var(--warning)"></span>{{ t('status.processing') }}
                  </div>
                  <div class="legend-item-compact">
                    <span class="legend-dot" style="background: var(--danger)"></span>{{ t('status.backordered') }}
                  </div>
                </div>
              </div>

              <!-- Right: Health Metrics -->
              <div class="order-health-metrics">
                <div class="health-metric">
                  <div class="health-metric-label">{{ t('dashboard.orderHealth.revenue') }}</div>
                  <div class="health-metric-value">
                    {{ formatCurrency(orderHealthMetrics.totalValue, selectedCurrency) }}
                  </div>
                </div>
                <div class="health-metric">
                  <div class="health-metric-label">{{ t('dashboard.orderHealth.avgOrderValue') }}</div>
                  <div class="health-metric-value">
                    {{ formatCurrency(orderHealthMetrics.avgOrderValue, selectedCurrency) }}
                  </div>
                </div>
                <div class="health-metric">
                  <div class="health-metric-label">{{ t('dashboard.orderHealth.onTimeRate') }}</div>
                  <div
                    class="health-metric-value"
                    :class="{
                      'metric-good': orderHealthMetrics.onTimeRate >= 90,
                      'metric-warning': orderHealthMetrics.onTimeRate < 90 && orderHealthMetrics.onTimeRate >= 75,
                      'metric-bad': orderHealthMetrics.onTimeRate < 75,
                    }"
                  >
                    {{ orderHealthMetrics.onTimeRate.toFixed(1) }}%
                  </div>
                </div>
                <div class="health-metric">
                  <div class="health-metric-label">{{ t('dashboard.orderHealth.avgFulfillmentDays') }}</div>
                  <div class="health-metric-value">{{ orderHealthMetrics.avgFulfillmentDays.toFixed(1) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Inventory by Category -->
        <div class="card chart-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.inventoryValue.title') }}</h3>
          </div>
          <div class="chart-content">
            <div class="horizontal-bar-chart" v-if="categoryData.length > 0">
              <div v-for="cat in categoryData" :key="cat.name" class="h-bar-item">
                <div class="h-bar-label">{{ translateCategory(cat.name) }}</div>
                <div class="h-bar-container">
                  <div
                    class="h-bar"
                    :style="{ width: (cat.value / maxCategoryValue) * 100 + '%', background: cat.color }"
                  >
                    <span class="h-bar-value">{{
                      selectedCurrency === 'JPY'
                        ? formatCurrency(cat.value, selectedCurrency)
                        : `$${(cat.value / 1000).toFixed(1)}K`
                    }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-data">{{ t('dashboard.inventoryShortages.noData') }}</div>
          </div>
        </div>

        <!-- Inventory Shortages -->
        <div class="card chart-card full-width">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.inventoryShortages.title') }} ({{ backlogItems.length }})</h3>
          </div>
          <div v-if="backlogItems.length === 0" class="no-backlog">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="success-icon">
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clip-rule="evenodd"
              />
            </svg>
            <p class="no-backlog-text">{{ t('dashboard.inventoryShortages.noShortages') }}</p>
          </div>
          <div v-else class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('dashboard.inventoryShortages.orderId') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.sku') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.itemName') }}</th>
                  <th class="num">{{ t('dashboard.inventoryShortages.quantityNeeded') }}</th>
                  <th class="num">{{ t('dashboard.inventoryShortages.quantityAvailable') }}</th>
                  <th class="num">{{ t('dashboard.inventoryShortages.shortage') }}</th>
                  <th class="num">{{ t('dashboard.inventoryShortages.daysDelayed') }}</th>
                  <th>{{ t('dashboard.inventoryShortages.priority') }}</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in backlogItems" :key="item.id">
                  <td @click="showBacklogDetail(item)" style="cursor: pointer">
                    <strong>{{ item.order_id }}</strong>
                  </td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer">
                    <strong>{{ item.item_sku }}</strong>
                  </td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer">
                    {{ translateProductName(item.item_name) }}
                  </td>
                  <td class="num" @click="showBacklogDetail(item)" style="cursor: pointer">
                    {{ item.quantity_needed }}
                  </td>
                  <td class="num" @click="showBacklogDetail(item)" style="cursor: pointer">
                    {{ item.quantity_available }}
                  </td>
                  <td class="num" @click="showBacklogDetail(item)" style="cursor: pointer">
                    <span class="badge danger">
                      {{ Math.abs(item.quantity_needed - item.quantity_available) }}
                      {{ t('dashboard.inventoryShortages.unitsShort') }}
                    </span>
                  </td>
                  <td class="num" @click="showBacklogDetail(item)" style="cursor: pointer">
                    <span
                      :style="{ color: item.days_delayed > 7 ? 'var(--danger)' : 'var(--warning)', fontWeight: 600 }"
                    >
                      {{ item.days_delayed }} {{ t('dashboard.inventoryShortages.days') }}
                    </span>
                  </td>
                  <td @click="showBacklogDetail(item)" style="cursor: pointer">
                    <span :class="['badge', item.priority]">
                      {{ translatePriority(item.priority) }}
                    </span>
                  </td>
                  <td>
                    <button v-if="!item.purchase_order_id" @click.stop="openPOModal(item)" class="po-button create">
                      {{ t('dashboard.inventoryShortages.createPO') }}
                    </button>
                    <button v-else @click.stop="viewPO(item)" class="po-button view">
                      {{ t('dashboard.inventoryShortages.viewPO') }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Top Products Table -->
        <div class="card chart-card full-width">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.topProducts.title') }}</h3>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('dashboard.topProducts.product') }}</th>
                  <th>{{ t('dashboard.topProducts.sku') }}</th>
                  <th>{{ t('dashboard.topProducts.category') }}</th>
                  <th class="num">{{ t('dashboard.topProducts.unitsOrdered') }}</th>
                  <th class="num">{{ t('dashboard.topProducts.revenue') }}</th>
                  <th>{{ t('dashboard.topProducts.firstOrder') }}</th>
                  <th>{{ t('dashboard.topProducts.stockStatus') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in topProducts" :key="item.sku" class="clickable-row" @click="showProductDetail(item)">
                  <td>
                    <strong>{{ translateProductName(item.name) }}</strong>
                  </td>
                  <td>{{ item.sku }}</td>
                  <td>{{ translateCategory(item.category) }}</td>
                  <td class="num">{{ item.unitsOrdered }}</td>
                  <td class="num">
                    <strong>{{ formatCurrency(item.revenue, selectedCurrency) }}</strong>
                  </td>
                  <td>{{ formatDate(item.firstOrderDate) }}</td>
                  <td>
                    <span :class="['badge', getStockBadge(item.stockLevel)]">
                      {{ translateStockLevel(item.stockLevel) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <ProductDetailModal :is-open="showProductModal" :product="selectedProduct" @close="showProductModal = false" />

    <BacklogDetailModal
      :is-open="showBacklogModal"
      :backlog-item="selectedBacklogItem"
      @close="showBacklogModal = false"
    />

    <PurchaseOrderModal
      :is-open="showPOModal"
      :backlog-item="selectedBacklogForPO"
      :mode="poModalMode"
      @close="showPOModal = false"
      @po-created="handlePOCreated"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import BacklogDetailModal from '../components/BacklogDetailModal.vue'
import PurchaseOrderModal from '../components/PurchaseOrderModal.vue'

export default {
  name: 'Dashboard',
  components: {
    ProductDetailModal,
    BacklogDetailModal,
    PurchaseOrderModal,
  },
  setup() {
    const { t, currentLocale, currentCurrency, translateProductName, translateWarehouse } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const summary = ref({})
    const allOrders = ref([])
    const inventoryItems = ref([])

    // Modal state
    const showProductModal = ref(false)
    const selectedProduct = ref(null)
    const showBacklogModal = ref(false)
    const selectedBacklogItem = ref(null)
    const showPOModal = ref(false)
    const selectedBacklogForPO = ref(null)
    const poModalMode = ref('create')

    // Use shared filters
    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, getCurrentFilters } = useFilters()

    const ordersData = ref({ fulfilled: 187, goal: 200 })
    const fillRate = ref(96.8)

    const revenueGoal = computed(() => {
      // $800K per month, so if looking at all months (12 months), goal is 12 * 800K = 9.6M
      const monthlyGoal = 800000
      if (selectedPeriod.value === 'all') {
        return monthlyGoal * 12 // $9,600,000 for the full year
      }
      return monthlyGoal // $800,000 for a single month
    })

    const revenueGoalDisplay = computed(() => {
      if (revenueGoal.value >= 1000000) {
        return `$${(revenueGoal.value / 1000000).toFixed(1)}M`
      }
      return `$${(revenueGoal.value / 1000).toFixed(0)}K`
    })

    const statusData = computed(() => {
      const counts = { delivered: 0, shipped: 0, processing: 0, backordered: 0 }
      allOrders.value.forEach((order) => {
        const status = order.status.toLowerCase()
        if (counts[status] !== undefined) counts[status]++
      })
      return counts
    })

    const orderHealthMetrics = computed(() => {
      const totalOrders = allOrders.value.length
      const totalValue = allOrders.value.reduce((sum, order) => sum + (order.total_value || 0), 0)
      const avgOrderValue = totalOrders > 0 ? totalValue / totalOrders : 0

      // Calculate on-time delivery rate (delivered orders that arrived on or before expected date)
      const deliveredOrders = allOrders.value.filter((o) => o.status.toLowerCase() === 'delivered')
      const onTimeDeliveries = deliveredOrders.filter((o) => {
        if (o.actual_delivery && o.expected_delivery) {
          return new Date(o.actual_delivery) <= new Date(o.expected_delivery)
        }
        return false
      }).length
      const onTimeRate = deliveredOrders.length > 0 ? (onTimeDeliveries / deliveredOrders.length) * 100 : 0

      // Calculate average fulfillment speed (days from order to delivery for delivered orders)
      let totalDays = 0
      let countWithDates = 0
      deliveredOrders.forEach((o) => {
        if (o.order_date && o.actual_delivery) {
          const orderDate = new Date(o.order_date)
          const deliveryDate = new Date(o.actual_delivery)
          const days = Math.round((deliveryDate - orderDate) / (1000 * 60 * 60 * 24))
          totalDays += days
          countWithDates++
        }
      })
      const avgFulfillmentDays = countWithDates > 0 ? totalDays / countWithDates : 0

      return {
        totalOrders,
        totalValue,
        avgOrderValue,
        onTimeRate,
        avgFulfillmentDays,
      }
    })

    const categoryData = computed(() => {
      // Group inventory by category and calculate values
      // Filter inventory items to only include those with orders in the selected period
      const categoryMap = {}

      // Use a single neutral slate/gray color for all categories
      const singleColor = 'var(--text-muted)' // Neutral slate gray color

      // Get SKUs from orders in the filtered time period
      const orderedSkus = new Set()
      allOrders.value.forEach((order) => {
        if (order.items) {
          order.items.forEach((item) => {
            orderedSkus.add(item.sku)
          })
        }
      })

      // Only include inventory items that have orders in the selected period
      // If no period is selected (all), include all inventory items
      const itemsToInclude =
        selectedPeriod.value === 'all'
          ? inventoryItems.value
          : inventoryItems.value.filter((item) => orderedSkus.has(item.sku))

      itemsToInclude.forEach((item) => {
        const cat = item.category.toLowerCase()
        if (!categoryMap[cat]) {
          categoryMap[cat] = {
            name: item.category,
            value: 0,
            color: singleColor,
            category: cat,
            count: 0,
          }
        }
        categoryMap[cat].value += item.quantity_on_hand * item.unit_cost
        categoryMap[cat].count += 1
      })

      return Object.values(categoryMap)
    })

    const maxCategoryValue = computed(() => {
      if (categoryData.value.length === 0) return 1
      return Math.max(...categoryData.value.map((c) => c.value))
    })

    const orderTrendData = computed(() => {
      // Group orders by month from the actual data
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

      // Initialize all months with 0 orders
      const monthMap = {}
      monthNames.forEach((month) => {
        monthMap[month] = { month, orders: 0 }
      })

      // Count orders for each month
      if (Array.isArray(allOrders.value)) {
        allOrders.value.forEach((order) => {
          if (order && order.order_date) {
            const date = new Date(order.order_date)
            const monthIndex = date.getMonth()
            // Check if monthIndex is valid (0-11)
            if (!isNaN(monthIndex) && monthIndex >= 0 && monthIndex <= 11) {
              const monthName = monthNames[monthIndex]
              monthMap[monthName].orders++
            }
          }
        })
      }

      // Return all months in order
      return monthNames.map((month) => monthMap[month])
    })

    const maxOrderCount = computed(() => {
      if (orderTrendData.value.length === 0) return 10
      const max = Math.max(...orderTrendData.value.map((d) => d.orders))
      // Round up to nearest 10 for cleaner axis, minimum 10
      return Math.max(10, Math.ceil(max / 10) * 10)
    })

    const topProducts = computed(() => {
      // Calculate top products from filtered order data
      const productMap = {}

      // allOrders is already filtered by API based on: month, warehouse, category, status
      allOrders.value.forEach((order) => {
        if (order.items) {
          order.items.forEach((item) => {
            const sku = item.sku

            // Find matching inventory item to get full product details
            // Note: inventoryItems is also filtered by API based on: warehouse, category
            const invItem = inventoryItems.value.find((i) => i.sku === sku)

            // Skip products that don't match current inventory filters
            // (e.g., if filtering by warehouse A, don't show products from warehouse B)
            if (!invItem && (selectedLocation.value !== 'all' || selectedCategory.value !== 'all')) {
              return // Skip this product as it doesn't match inventory filters
            }

            if (!productMap[sku]) {
              productMap[sku] = {
                name: item.name,
                sku: sku,
                category: invItem?.category || 'Unknown',
                warehouse: invItem?.warehouse || 'Unknown',
                unitsOrdered: 0,
                revenue: 0,
                stockLevel: invItem
                  ? invItem.quantity_on_hand > invItem.reorder_point
                    ? 'In Stock'
                    : 'Low Stock'
                  : 'Unknown',
                firstOrderDate: order.order_date,
              }
            } else {
              // Update to EARLIEST order date (to show January at top when selecting All Months)
              if (
                order.order_date &&
                (!productMap[sku].firstOrderDate || order.order_date < productMap[sku].firstOrderDate)
              ) {
                productMap[sku].firstOrderDate = order.order_date
              }
            }
            productMap[sku].unitsOrdered += item.quantity
            productMap[sku].revenue += item.quantity * item.unit_price
          })
        }
      })

      // Convert to array, sort by first order date (earliest first = January at top), then by revenue, and take top 12
      return Object.values(productMap)
        .sort((a, b) => {
          // Sort by first order date (earliest first)
          // This ensures products first ordered in January appear before those first ordered in December
          const dateA = new Date(a.firstOrderDate || '9999-12-31')
          const dateB = new Date(b.firstOrderDate || '9999-12-31')
          if (dateA.getTime() !== dateB.getTime()) {
            return dateA.getTime() - dateB.getTime() // Earlier dates come first
          }
          // If dates are equal, sort by revenue (highest first)
          return b.revenue - a.revenue
        })
        .slice(0, 12)
    })

    const allBacklogItems = ref([])

    // Filter backlog based on inventory filters
    const backlogItems = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allBacklogItems.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map((item) => item.sku))
      return allBacklogItems.value.filter((b) => validSkus.has(b.item_sku))
    })

    const loadData = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [summaryData, ordersData, inventoryData, backlogData] = await Promise.all([
          api.getDashboardSummary(filters),
          api.getOrders(filters),
          api.getInventory(filters),
          api.getBacklog(),
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

    // Compute total orders once for efficiency
    const totalOrders = computed(() => {
      return (
        statusData.value.delivered +
        statusData.value.shipped +
        statusData.value.processing +
        statusData.value.backordered
      )
    })

    const getCircleSegment = (value) => {
      return totalOrders.value > 0 ? (value / totalOrders.value) * 440 : 0
    }

    const getStockBadge = (level) => {
      if (level === 'In Stock') return 'success'
      if (level === 'Low Stock') return 'warning'
      return 'danger'
    }

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        Sensors: t('categories.sensors'),
        Actuators: t('categories.actuators'),
        Controllers: t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies'),
      }
      return categoryMap[category] || category
    }

    const translateStockLevel = (stockLevel) => {
      const stockMap = {
        'In Stock': t('status.inStock'),
        'Low Stock': t('status.lowStock'),
      }
      return stockMap[stockLevel] || stockLevel
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        high: t('priority.high'),
        medium: t('priority.medium'),
        low: t('priority.low'),
        High: t('priority.high'),
        Medium: t('priority.medium'),
        Low: t('priority.low'),
      }
      return priorityMap[priority] || priority
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
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

    const handlePOCreated = async (poData) => {
      // Optimistic update so the row flips to "View PO" immediately
      const item = allBacklogItems.value.find((b) => b.id === poData.backlog_item_id)
      if (item) {
        item.purchase_order_id = poData.id
        item.has_purchase_order = true
      }
      showPOModal.value = false
      // Refresh only the backlog (not the whole dashboard) to stay in sync with the server
      try {
        allBacklogItems.value = await api.getBacklog()
      } catch (err) {
        console.error('Failed to refresh backlog after PO creation', err)
      }
    }

    // Watch for filter changes and reload data
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
      orderTrendData,
      maxOrderCount,
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
      revenueGoalDisplay,
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
      viewPO,
      handlePOCreated,
    }
  },
}
</script>

<style scoped>
.header-meta {
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.kpi-section {
  margin-bottom: var(--space-6);
}

.section-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-4);
}

.kpi-header {
  margin-bottom: var(--space-3);
}

.kpi-goal {
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin-bottom: var(--space-3);
}

.kpi-progress-bar {
  width: 100%;
  height: 6px;
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.kpi-progress {
  height: 100%;
  background: var(--info);
  border-radius: var(--radius-sm);
  transition: width 0.6s ease;
}

.kpi-progress.success {
  background: var(--success);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-content {
  padding: var(--space-4);
}

.donut-chart {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-12);
}

.donut-svg {
  width: 200px;
  height: 200px;
}

.donut-legend {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
  color: var(--text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-sm);
}

/* Order Health Dashboard Styles */
.order-health-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
  align-items: center;
  padding: var(--space-4);
  min-height: 240px;
}

.order-health-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: 0 var(--space-4);
}

.donut-svg-compact {
  width: 200px;
  height: 200px;
}

.donut-center-label {
  font-size: var(--text-xs);
  fill: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.donut-center-value {
  font-size: var(--text-4xl);
  fill: var(--text);
  font-weight: 700;
}

.donut-legend-compact {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-2) var(--space-5);
}

.legend-item-compact {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
  color: var(--text-secondary);
  font-weight: 500;
}

.order-health-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  justify-content: center;
  align-items: center;
}

.health-metric {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  text-align: center;
  width: 100%;
}

.health-metric-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.health-metric-value {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.metric-good {
  color: var(--success);
}

.metric-warning {
  color: var(--warning);
}

.metric-bad {
  color: var(--danger);
}

.horizontal-bar-chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: 0 var(--space-4);
}

.h-bar-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.h-bar-label {
  width: 120px;
  min-width: 120px;
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.h-bar-container {
  flex: 1;
  height: 32px;
  background: var(--surface-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.h-bar {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: var(--space-3);
  transition: width 0.6s ease;
}

.h-bar-value {
  font-size: var(--text-sm);
  font-weight: 700;
  color: white;
}

.line-chart {
  display: flex;
  gap: var(--space-6);
  height: 280px;
}

.line-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: var(--space-4);
  font-size: var(--text-xs);
  color: var(--text-subtle);
  border-right: 1px solid var(--border);
}

.line-chart-area {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: var(--space-2);
}

.line-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
  gap: var(--space-2);
}

.line-bar-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
}

.line-bar {
  width: 100%;
  max-width: 60px;
  min-height: 8px;
  background: var(--info);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: var(--shadow-md);
}

.line-bar.empty-bar {
  background: var(--border);
  box-shadow: none;
  min-height: 4px;
}

.line-bar:hover {
  background: var(--info);
  transform: scaleY(1.05);
}

.line-bar.empty-bar:hover {
  background: var(--border-strong);
  transform: none;
}

.line-bar-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
}

.no-data {
  padding: var(--space-8);
  text-align: center;
  color: var(--text-subtle);
  font-size: var(--text-base);
}

.no-backlog {
  padding: var(--space-12);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

.success-icon {
  width: 48px;
  height: 48px;
  color: var(--success);
}

.no-backlog-text {
  font-size: var(--text-xl);
  color: var(--success);
  font-weight: 600;
  margin: 0;
}

/* Tasks Card Styles */
.tasks-card {
  margin-bottom: var(--space-8);
}

.tasks-content {
  padding: var(--space-6);
}

.task-input-container {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.task-input {
  flex: 1;
  padding: var(--space-3);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  font-size: var(--text-md);
  transition: border-color var(--duration) var(--ease);
}

.task-input:focus {
  outline: none;
  border-color: var(--accent);
}

.task-add-btn {
  padding: var(--space-3) var(--space-6);
  background: var(--accent);
  color: var(--accent-ink);
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 600;
  cursor: pointer;
  transition:
    transform var(--duration) var(--ease),
    opacity var(--duration) var(--ease);
}

.task-add-btn:hover:not(:disabled) {
  transform: none;
}

.task-add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.no-tasks {
  text-align: center;
  padding: var(--space-8);
  color: var(--text-muted);
  font-style: italic;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.task-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--surface-subtle);
  border-radius: var(--radius-lg);
  border: 2px solid transparent;
  transition: all var(--duration) var(--ease);
}

.task-item:hover {
  border-color: var(--border);
  background: var(--surface);
}

.task-item.completed {
  opacity: 0.6;
}

.task-item.completed .task-text {
  text-decoration: line-through;
  color: var(--text-subtle);
}

.task-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--accent);
}

.task-text {
  flex: 1;
  cursor: pointer;
  user-select: none;
  color: var(--text);
  font-size: var(--text-md);
}

.task-delete-btn {
  width: 28px;
  height: 28px;
  background: var(--danger);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-xl);
  line-height: 1;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.task-delete-btn:hover {
  background: var(--danger);
  transform: scale(1.1);
}

.po-button {
  padding: var(--space-2) var(--space-4);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  white-space: nowrap;
}

.po-button.create {
  background: var(--info);
  color: white;
}

.po-button.create:hover {
  background: var(--info);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.po-button.view {
  background: var(--text-muted);
  color: white;
}

.po-button.view:hover {
  background: var(--text-secondary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
</style>
