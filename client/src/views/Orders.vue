<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t('orders.title') }}</h2>
      <p>{{ t('orders.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('status.delivered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Delivered').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('status.shipped') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Shipped').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('status.processing') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Processing').length }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t('status.backordered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Backordered').length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('orders.allOrders') }} ({{ orders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th class="col-order-number">{{ t('orders.table.orderNumber') }}</th>
                <th class="col-customer">{{ t('orders.table.customer') }}</th>
                <th class="col-items">{{ t('orders.table.items') }}</th>
                <th class="col-status">{{ t('orders.table.status') }}</th>
                <th class="col-date">{{ t('orders.table.orderDate') }}</th>
                <th class="col-date">{{ t('orders.table.expectedDelivery') }}</th>
                <th class="col-value">{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
                <td class="col-customer">{{ translateCustomerName(order.customer) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="(item, idx) in order.items" :key="idx" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol }}{{ item.unit_price }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status">
                  <span :class="['badge', getOrderStatusClass(order.status)]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td class="col-date">{{ formatDate(order.order_date) }}</td>
                <td class="col-date">{{ formatDate(order.expected_delivery) }}</td>
                <td class="col-value"><strong>{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Submitted Restocking Orders -->
    <div class="card restocking-section">
      <div class="card-header">
        <span class="card-title">Submitted Restocking Orders</span>
        <span class="restocking-count">{{ restockingOrders.length }} order{{ restockingOrders.length !== 1 ? 's' : '' }}</span>
      </div>

      <div v-if="restockingLoading" class="loading">Loading...</div>

      <div v-else-if="!restockingOrders.length" class="restocking-empty">
        No restocking orders yet. Use the Restocking tab to place orders.
      </div>

      <div v-else class="table-container">
        <table class="restocking-table">
          <thead>
            <tr>
              <th>Order #</th>
              <th>SKU</th>
              <th>Item</th>
              <th>Qty</th>
              <th>Unit Cost</th>
              <th>Total Value</th>
              <th>Submitted</th>
              <th>Expected Delivery</th>
              <th>Lead Time</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in restockingOrders" :key="order.id">
              <td class="order-num">{{ order.order_number }}</td>
              <td class="sku-cell">{{ order.item_sku }}</td>
              <td>{{ order.item_name }}</td>
              <td>{{ order.quantity.toLocaleString() }}</td>
              <td>${{ order.unit_cost.toFixed(2) }}</td>
              <td class="total-cell">${{ order.total_value.toLocaleString(undefined, {minimumFractionDigits:2,maximumFractionDigits:2}) }}</td>
              <td>{{ formatRestockingDate(order.submitted_date) }}</td>
              <td>{{ formatRestockingDate(order.expected_delivery_date) }}</td>
              <td><span class="lead-time-badge">{{ daysUntilDelivery(order.expected_delivery_date) }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Orders',
  setup() {
    const { t, currentCurrency, translateProductName, translateCustomerName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })
    const loading = ref(true)
    const error = ref(null)
    const orders = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loadOrders = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        const fetchedOrders = await api.getOrders(filters)

        // Sort orders by order_date (earliest first)
        orders.value = fetchedOrders.sort((a, b) => {
          const dateA = new Date(a.order_date)
          const dateB = new Date(b.order_date)
          return dateA - dateB
        })
      } catch (err) {
        error.value = 'Failed to load orders: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadOrders()
    })

    const getOrdersByStatus = (status) => {
      return orders.value.filter(order => order.status === status)
    }

    const getOrderStatusClass = (status) => {
      const statusMap = {
        'Delivered': 'success',
        'Shipped': 'info',
        'Processing': 'warning',
        'Backordered': 'danger'
      }
      return statusMap[status] || 'info'
    }

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const restockingOrders = ref([])
    const restockingLoading = ref(false)

    const loadRestockingOrders = async () => {
      restockingLoading.value = true
      try {
        restockingOrders.value = await api.getRestockingOrders()
      } catch (err) {
        console.error('Failed to load restocking orders:', err)
      } finally {
        restockingLoading.value = false
      }
    }

    const formatRestockingDate = (dateStr) => {
      if (!dateStr) return '—'
      const date = new Date(dateStr)
      return isNaN(date.getTime()) ? '—' : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    }

    const daysUntilDelivery = (dateStr) => {
      if (!dateStr) return '—'
      const delivery = new Date(dateStr)
      if (isNaN(delivery.getTime())) return '—'
      const diff = Math.ceil((delivery - new Date()) / (1000 * 60 * 60 * 24))
      return diff > 0 ? `${diff}d` : 'Due'
    }

    onMounted(() => {
      loadOrders()
      loadRestockingOrders()
    })

    return {
      t,
      loading,
      error,
      orders,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      currencySymbol,
      translateProductName,
      translateCustomerName,
      restockingOrders,
      restockingLoading,
      formatRestockingDate,
      daysUntilDelivery
    }
  }
}
</script>

<style scoped>
/* Fixed table layout to prevent column shifting */
.orders-table {
  table-layout: fixed;
  width: 100%;
}

/* Column widths */
.col-order-number {
  width: 130px;
}

.col-customer {
  width: 180px;
}

.col-items {
  width: 200px;
}

.col-status {
  width: 130px;
}

.col-date {
  width: 140px;
}

.col-value {
  width: 120px;
}

/* Items details styling */
.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: #3b82f6;
  font-weight: 500;
  list-style: none;
  user-select: none;
  display: inline-block;
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: '▶';
  display: inline-block;
  margin-right: 0.375rem;
  font-size: 0.75rem;
  transition: transform 0.2s;
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-summary:hover {
  color: #2563eb;
  text-decoration: underline;
}

/* Dropdown container */
.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 0.5rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 0.75rem;
  z-index: 10;
  min-width: 300px;
  max-width: 400px;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #0f172a;
}

.item-meta {
  font-size: 0.813rem;
  color: #64748b;
}

.restocking-section { margin-top: 2rem; }
.restocking-count {
  font-size: 0.8rem;
  color: var(--text-secondary, #64748b);
  background: var(--surface-border, #e2e8f0);
  padding: 2px 10px;
  border-radius: 999px;
}
.restocking-empty {
  padding: 2rem;
  text-align: center;
  color: var(--text-muted, #94a3b8);
  font-size: 0.875rem;
}
.order-num {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--sidebar-active-border, #3b82f6);
}
.sku-cell {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  color: var(--text-secondary, #64748b);
}
.total-cell { font-weight: 600; }
.lead-time-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #eff6ff;
  color: #1e40af;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
}
</style>
