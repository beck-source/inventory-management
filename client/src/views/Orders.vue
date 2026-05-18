<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t('orders.title') }}</h2>
      <p>{{ t('orders.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Submitted restock orders — shown only when at least one exists -->
      <div v-if="restockOrders.length > 0" class="card restock-section">
        <div class="card-header">
          <h3 class="card-title">Submitted Restock Orders ({{ restockOrders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="restock-orders-table">
            <thead>
              <tr>
                <th>Order Number</th>
                <th class="num-col">Items</th>
                <th class="num-col">Budget</th>
                <th class="num-col">Total Cost</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Expected Delivery</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in restockOrders" :key="order.id">
                <td><strong class="mono">{{ order.order_number }}</strong></td>
                <td class="num-col">{{ order.items.length }} item(s)</td>
                <td class="num-col">{{ formatCurrency(order.budget) }}</td>
                <td class="num-col"><strong>{{ formatCurrency(order.total_cost) }}</strong></td>
                <td><span class="badge info">{{ order.status }}</span></td>
                <td>{{ formatDate(order.created_date) }}</td>
                <td><strong>{{ formatDate(order.expected_delivery) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

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
    const restockOrders = ref([])

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

    const loadRestockOrders = async () => {
      try {
        restockOrders.value = await api.getRestockOrders()
      } catch (err) {
        console.error('Failed to load restock orders:', err)
      }
    }

    const formatCurrency = (val) =>
      Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD' })

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
      loadOrders()
      loadRestockOrders()
    })

    return {
      t,
      loading,
      error,
      orders,
      restockOrders,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      formatCurrency,
      currencySymbol,
      translateProductName,
      translateCustomerName
    }
  }
}
</script>

<style scoped>
.orders-table { table-layout: fixed; width: 100%; }
.col-order-number { width: 130px; }
.col-customer { width: 180px; }
.col-items { width: 200px; }
.col-status { width: 130px; }
.col-date { width: 140px; }
.col-value { width: 120px; }

.items-details { position: relative; }
.items-summary {
  cursor: pointer; color: var(--color-accent);
  font-family: var(--font-mono); font-size: 0.75rem;
  font-weight: 500; list-style: none;
  user-select: none; display: inline-block; letter-spacing: 0.02em;
}
.items-summary::-webkit-details-marker { display: none; }
.items-summary::before {
  content: '▶'; display: inline-block; margin-right: 0.375rem;
  font-size: 0.625rem; transition: transform 0.15s;
}
.items-details[open] .items-summary::before { transform: rotate(90deg); }
.items-summary:hover { color: #33deff; }

.items-dropdown {
  position: absolute; top: 100%; left: 0; margin-top: 0.375rem;
  background: var(--color-bg-overlay);
  border: 1px solid var(--color-border); border-radius: 6px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4); padding: 0.5rem;
  z-index: 10; min-width: 280px; max-width: 380px;
}
.item-entry {
  display: flex; flex-direction: column; gap: 0.125rem;
  padding: 0.4rem 0.5rem; border-bottom: 1px solid var(--color-border-subtle);
}
.item-entry:last-child { border-bottom: none; }
.item-name { font-size: 0.8rem; font-weight: 500; color: var(--color-text-primary); }
.item-meta { font-family: var(--font-mono); font-size: 0.7rem; color: var(--color-text-muted); }

.restock-section { border-left: 3px solid var(--color-accent); margin-bottom: 1rem; }
.mono { font-family: var(--font-mono); font-size: 0.75rem; letter-spacing: 0.02em; }
.num-col { text-align: right; font-family: var(--font-mono); }
.restock-orders-table { width: 100%; }
</style>
