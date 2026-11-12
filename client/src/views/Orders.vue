<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t('orders.title') }}</h2>
      <p>{{ t('orders.description') }}</p>
    </div>

    <AsyncStatus :loading="loading" :error="error" :loaded="loaded" @retry="reload">
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('status.delivered') }}</div>
          <div class="stat-value">{{ statusCounts.Delivered }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('status.shipped') }}</div>
          <div class="stat-value">{{ statusCounts.Shipped }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('status.processing') }}</div>
          <div class="stat-value">{{ statusCounts.Processing }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t('status.backordered') }}</div>
          <div class="stat-value">{{ statusCounts.Backordered }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('orders.submittedOrders') }} ({{ submittedOrders.length }})</h3>
        </div>
        <div v-if="submittedOrders.length === 0" class="empty-note">{{ t('orders.noSubmittedOrders') }}</div>
        <div v-else class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th class="col-order-number">{{ t('orders.table.orderNumber') }}</th>
                <th class="col-date">{{ t('orders.table.submittedDate') }}</th>
                <th class="col-items">{{ t('orders.table.items') }}</th>
                <th class="col-value num">{{ t('orders.table.totalValue') }}</th>
                <th class="col-status">{{ t('orders.table.status') }}</th>
                <th class="col-date">{{ t('orders.table.leadTime') }}</th>
                <th class="col-date">{{ t('orders.table.expectedDelivery') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in submittedOrders" :key="order.id">
                <td class="col-order-number">
                  <strong>{{ order.order_number }}</strong>
                </td>
                <td class="col-date">{{ formatDate(order.submitted_date) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="item in order.items" :key="item.sku" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta"
                          >{{ t('orders.quantity') }}: {{ item.quantity }} @
                          {{ formatCurrency(item.unit_cost, currentCurrency) }}</span
                        >
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-value num">
                  <strong>{{ formatCurrency(order.total_cost, currentCurrency) }}</strong>
                </td>
                <td class="col-status">
                  <span class="badge info">{{ t('status.submitted') }}</span>
                </td>
                <td class="col-date">{{ t('common.days', { n: order.lead_time_days }) }}</td>
                <td class="col-date">{{ formatDate(order.expected_delivery) }}</td>
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
                <th class="col-value num">{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="col-order-number">
                  <strong>{{ order.order_number }}</strong>
                </td>
                <td class="col-customer">{{ translateCustomerName(order.customer) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <!-- sku alone is not unique: the same SKU can repeat within one order, so combine with idx -->
                      <div v-for="(item, idx) in order.items" :key="`${item.sku}-${idx}`" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta"
                          >{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol
                          }}{{ item.unit_price }}</span
                        >
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
                <td class="col-value num">
                  <strong>{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </AsyncStatus>
  </div>
</template>

<script>
import AsyncStatus from '../components/AsyncStatus.vue'
import { useAsyncData } from '../composables/useAsyncData'
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Orders',
  components: { AsyncStatus },
  setup() {
    const { t, currentLocale, currentCurrency, translateProductName, translateCustomerName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })
    const orders = ref([])
    const submittedOrders = ref([])

    // Use shared filters
    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, getCurrentFilters } = useFilters()

    // Reloads on filter change; previous orders stay visible meanwhile
    const { loading, error, loaded, reload } = useAsyncData(
      ({ signal }) => api.getOrders(getCurrentFilters(), { signal }),
      {
        watchSources: [selectedPeriod, selectedLocation, selectedCategory, selectedStatus],
        onSuccess: (fetchedOrders) => {
          // Sort orders by order_date (earliest first)
          orders.value = fetchedOrders.sort((a, b) => {
            const dateA = new Date(a.order_date)
            const dateB = new Date(b.order_date)
            return dateA - dateB
          })
        },
      }
    )

    // Count orders per status in a single pass (cached) instead of filtering once per stat card
    const statusCounts = computed(() => {
      const counts = { Delivered: 0, Shipped: 0, Processing: 0, Backordered: 0 }
      for (const order of orders.value) {
        counts[order.status] = (counts[order.status] ?? 0) + 1
      }
      return counts
    })

    const getOrderStatusClass = (status) => {
      const statusMap = {
        Delivered: 'success',
        Shipped: 'info',
        Processing: 'warning',
        Backordered: 'danger',
      }
      return statusMap[status] || 'info'
    }

    const formatDate = (dateString) => {
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    }

    // Submitted restocking orders are independent of the page filters, so load them once
    const loadSubmittedOrders = async () => {
      try {
        submittedOrders.value = await api.getSubmittedOrders()
      } catch (err) {
        console.error('Failed to load submitted orders:', err)
      }
    }

    onMounted(() => {
      loadSubmittedOrders()
    })

    return {
      t,
      loading,
      error,
      loaded,
      reload,
      orders,
      submittedOrders,
      currentCurrency,
      formatCurrency,
      statusCounts,
      getOrderStatusClass,
      formatDate,
      currencySymbol,
      translateProductName,
      translateCustomerName,
    }
  },
}
</script>

<style scoped>
.empty-note {
  padding: var(--space-6);
  color: var(--text-muted);
  font-size: var(--text-base);
}

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
  color: var(--info);
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
  margin-right: var(--space-1);
  font-size: var(--text-xs);
  transition: transform var(--duration) var(--ease);
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-summary:hover {
  color: var(--info);
  text-decoration: underline;
}

/* Dropdown container */
.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: var(--space-2);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--space-3);
  z-index: 10;
  min-width: 300px;
  max-width: 400px;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2);
  border-bottom: 1px solid var(--surface-muted);
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--text);
}

.item-meta {
  font-size: var(--text-sm);
  color: var(--text-muted);
}
</style>
