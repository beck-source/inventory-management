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

      <div v-if="submittedOrders.length > 0" class="card restocking-card">
        <div class="card-header">
          <h3 class="card-title">Submitted Restocking Orders</h3>
          <p class="card-subtitle">
            {{ submittedOrders.length }} {{ submittedOrders.length === 1 ? 'order' : 'orders' }} submitted this session
          </p>
        </div>
        <div class="table-container">
          <table class="restocking-table">
            <thead>
              <tr>
                <th class="text-left">Order #</th>
                <th class="text-left">Items</th>
                <th class="text-right">Total</th>
                <th class="text-left">Status</th>
                <th class="text-left">Submitted</th>
                <th class="text-left">Expected Delivery</th>
                <th class="text-right">Lead Time</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ro in submittedOrders" :key="ro.order_number">
                <td class="mono"><strong>{{ ro.order_number }}</strong></td>
                <td>{{ ro.items.length }} items</td>
                <td class="text-right">
                  <strong>${{ Number(ro.total_cost).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
                </td>
                <td>
                  <span class="badge-submitted">Submitted</span>
                </td>
                <td>{{ shortDate(ro.submitted_at || ro.order_date) }}</td>
                <td>{{ shortDate(ro.expected_delivery) }}</td>
                <td class="text-right">{{ ro.lead_time_days }} days</td>
              </tr>
            </tbody>
          </table>
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
    const submittedOrders = ref([])

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

    // Independent fetch for restocking orders — failure here should not break
    // the main orders view, so we handle errors locally.
    const loadSubmittedRestockingOrders = async () => {
      try {
        const data = await api.getRestockingOrders()
        submittedOrders.value = Array.isArray(data) ? data : []
      } catch (err) {
        // Silent failure: leave list empty so the card simply does not render
        submittedOrders.value = []
        console.error('Failed to load restocking orders:', err)
      }
    }

    // Short ISO-style date (YYYY-MM-DD) for the restocking orders table
    const shortDate = (value) => {
      if (!value) return ''
      const s = String(value)
      // If value is already an ISO string, slicing the first 10 chars yields YYYY-MM-DD
      if (s.length >= 10 && s[4] === '-' && s[7] === '-') {
        return s.slice(0, 10)
      }
      const d = new Date(value)
      if (isNaN(d.getTime())) return ''
      return d.toISOString().slice(0, 10)
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

    onMounted(() => {
      // Fire both fetches in parallel; they are independent of each other.
      Promise.all([loadOrders(), loadSubmittedRestockingOrders()])
    })

    return {
      t,
      loading,
      error,
      orders,
      submittedOrders,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      shortDate,
      currencySymbol,
      translateProductName,
      translateCustomerName
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

/* Submitted restocking orders card */
.restocking-card {
  margin-bottom: 1.5rem;
}

.card-subtitle {
  font-size: 0.813rem;
  color: #64748b;
  margin: 0.25rem 0 0 0;
}

.restocking-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.restocking-table thead th {
  text-align: left;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid #e2e8f0;
}

.restocking-table tbody td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  color: #0f172a;
}

.restocking-table tbody tr:last-child td {
  border-bottom: none;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.mono {
  font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, 'Courier New', monospace;
  font-size: 0.813rem;
}

.badge-submitted {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: #dbeafe;
  color: #1d4ed8;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
