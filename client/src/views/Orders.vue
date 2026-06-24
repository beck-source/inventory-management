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

      <!-- ── Submitted Restocking Orders ───────────────────────────────── -->
      <div class="card submitted-orders-section">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.submittedOrders.title') }}</h3>
          <span v-if="restockingOrders.length" class="submitted-count-badge">
            {{ restockingOrders.length }}
          </span>
        </div>

        <div v-if="restockingLoading" class="loading-inline">{{ t('common.loading') }}</div>

        <div v-else-if="restockingOrders.length === 0" class="empty-submitted">
          <span class="empty-icon">📦</span>
          <p>{{ t('restocking.submittedOrders.empty') }}</p>
        </div>

        <div v-else class="table-container">
          <table class="submitted-table">
            <thead>
              <tr>
                <th>{{ t('restocking.submittedOrders.table.orderNumber') }}</th>
                <th>{{ t('restocking.submittedOrders.table.orderDate') }}</th>
                <th>{{ t('restocking.submittedOrders.table.items') }}</th>
                <th>{{ t('restocking.submittedOrders.table.totalCost') }}</th>
                <th>{{ t('restocking.submittedOrders.table.status') }}</th>
                <th>{{ t('restocking.submittedOrders.table.expectedDelivery') }}</th>
                <th>{{ t('restocking.submittedOrders.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ro in restockingOrders" :key="ro.id">
                <td><strong>{{ ro.order_number }}</strong></td>
                <td>{{ formatDate(ro.order_date) }}</td>
                <td>
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: ro.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="(item, idx) in ro.items" :key="idx" class="item-entry">
                        <span class="item-name">{{ item.item_name }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol }}{{ item.unit_cost }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td><strong>{{ currencySymbol }}{{ ro.total_cost.toLocaleString() }}</strong></td>
                <td>
                  <span class="badge badge-submitted">{{ t('restocking.submittedOrders.statusSubmitted') }}</span>
                </td>
                <td>{{ formatDate(ro.expected_delivery) }}</td>
                <td>
                  <span class="lead-time-badge">
                    🕐 {{ ro.lead_time_days }} {{ t('restocking.submittedOrders.days') }}
                  </span>
                </td>
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

    // ── Submitted restocking orders ──────────────────────────────────────────
    const restockingOrders = ref([])
    const restockingLoading = ref(false)

    const loadRestockingOrders = async () => {
      try {
        restockingLoading.value = true
        restockingOrders.value = await api.getSubmittedRestockingOrders()
      } catch (err) {
        // Non-fatal – just show empty state
        console.error('Failed to load restocking orders:', err)
      } finally {
        restockingLoading.value = false
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

    onMounted(loadOrders)
    onMounted(loadRestockingOrders)

    return {
      t,
      loading,
      error,
      orders,
      restockingOrders,
      restockingLoading,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
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

/* ── Submitted restocking orders section ──────────────────────────────── */
.submitted-orders-section {
  margin-top: 1.5rem;
}
.submitted-orders-section .card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.submitted-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #3b82f6;
  color: #fff;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.05rem 0.5rem;
  min-width: 1.4rem;
}
.loading-inline {
  color: #64748b;
  font-size: 0.85rem;
  padding: 0.75rem 0;
}
.empty-submitted {
  text-align: center;
  padding: 2rem 1rem;
  color: #94a3b8;
}
.empty-icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }

.submitted-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}
.submitted-table th {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
  padding: 0.5rem 0.75rem;
  text-align: left;
  white-space: nowrap;
}
.submitted-table td {
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.submitted-table tbody tr:last-child td { border-bottom: none; }

.badge-submitted {
  background: #dbeafe;
  color: #1d4ed8;
  border-radius: 4px;
  padding: 0.18rem 0.5rem;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.lead-time-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  padding: 0.2rem 0.55rem;
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
}
</style>
