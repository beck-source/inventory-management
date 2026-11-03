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

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.submitted.title') }} ({{ submittedOrders.length }})</h3>
        </div>
        <div v-if="submittedError" class="error">{{ submittedError }}</div>
        <div v-else-if="submittedLoading" class="loading">{{ t('common.loading') }}</div>
        <div v-else-if="submittedOrders.length === 0" class="empty-state">{{ t('restocking.submitted.empty') }}</div>
        <div v-else class="table-container">
          <table class="submitted-table">
            <thead>
              <tr>
                <th>{{ t('orders.table.orderNumber') }}</th>
                <th>{{ t('orders.table.items') }}</th>
                <th>{{ t('orders.table.totalValue') }}</th>
                <th>{{ t('orders.table.orderDate') }}</th>
                <th>{{ t('restocking.submitted.leadTime') }}</th>
                <th>{{ t('orders.table.expectedDelivery') }}</th>
                <th>{{ t('restocking.submitted.vendor') }}</th>
                <th>{{ t('restocking.submitted.deliveryNumber') }}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in submittedOrders" :key="order.id">
                <td><strong>{{ order.order_number }}</strong></td>
                <td>
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="item in order.items" :key="item.sku" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ formatMoney(item.unit_cost) }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td><strong>{{ formatMoney(order.total_value) }}</strong></td>
                <td>{{ formatDate(order.order_date) }}</td>
                <td>{{ t('restocking.submitted.leadTimeValue', { days: order.lead_time_days }) }}</td>
                <td>{{ formatDate(order.expected_delivery) }}</td>
                <td>
                  <select class="field" v-model="drafts[order.id].vendor" :disabled="saving[order.id]">
                    <option value="">{{ t('restocking.submitted.noVendor') }}</option>
                    <option v-for="v in vendors" :key="v" :value="v">{{ v }}</option>
                  </select>
                </td>
                <td>
                  <input
                    class="field"
                    type="text"
                    maxlength="64"
                    v-model="drafts[order.id].delivery_number"
                    :disabled="saving[order.id]"
                  />
                </td>
                <td class="actions-cell">
                  <button
                    type="button"
                    class="save-btn"
                    :disabled="!isDirty(order) || saving[order.id]"
                    @click="saveOrder(order)"
                  >{{ saving[order.id] ? t('restocking.submitted.saving') : t('restocking.submitted.save') }}</button>
                  <!-- Only link to https URLs (guards against javascript: etc.) -->
                  <a
                    v-if="safeTrackingUrl(order)"
                    class="track-link"
                    :href="safeTrackingUrl(order)"
                    target="_blank"
                    rel="noopener noreferrer"
                  >{{ t('restocking.submitted.trackDelivery') }}</a>
                  <div v-if="saveErrors[order.id]" class="row-error">{{ saveErrors[order.id] }}</div>
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
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

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

    // Submitted restocking orders: independent of the filters and of the orders table above,
    // so a failure here never blanks the existing table.
    const submittedOrders = ref([])
    const vendors = ref([])
    const submittedLoading = ref(true)
    const submittedError = ref(null)
    const drafts = reactive({}) // order id -> editable { vendor, delivery_number }
    const saving = reactive({})
    const saveErrors = reactive({})

    const resetDraft = (order) => {
      drafts[order.id] = {
        vendor: order.vendor || '',
        delivery_number: order.delivery_number || ''
      }
    }

    const loadSubmittedOrders = async () => {
      try {
        submittedLoading.value = true
        submittedError.value = null
        const [list, vendorData] = await Promise.all([
          api.getRestockingOrders(),
          api.getRestockingVendors()
        ])
        vendors.value = vendorData.vendors
        submittedOrders.value = list
        list.forEach(resetDraft)
      } catch (err) {
        submittedError.value = t('restocking.submitted.loadFailed')
        console.error('Submitted orders load error:', err)
      } finally {
        submittedLoading.value = false
      }
    }

    const isDirty = (order) => {
      const d = drafts[order.id]
      return !!d && (d.vendor !== (order.vendor || '') ||
        d.delivery_number !== (order.delivery_number || ''))
    }

    const saveOrder = async (order) => {
      if (saving[order.id] || !isDirty(order)) return
      saving[order.id] = true
      saveErrors[order.id] = null
      try {
        // Send only the fields that changed
        const d = drafts[order.id]
        const payload = {}
        if (d.vendor !== (order.vendor || '')) payload.vendor = d.vendor
        if (d.delivery_number !== (order.delivery_number || '')) payload.delivery_number = d.delivery_number
        const updated = await api.updateRestockingOrder(order.id, payload)
        const idx = submittedOrders.value.findIndex(o => o.id === order.id)
        if (idx !== -1) submittedOrders.value[idx] = updated
        resetDraft(updated)
      } catch (err) {
        const detail = err.response?.data?.detail
        saveErrors[order.id] = typeof detail === 'string' ? detail : t('restocking.submitted.saveFailed')
      } finally {
        saving[order.id] = false
      }
    }

    const safeTrackingUrl = (order) =>
      typeof order.tracking_url === 'string' && order.tracking_url.startsWith('https://')
        ? order.tracking_url
        : null

    const formatMoney = (amount) => formatCurrency(amount, currentCurrency.value)

    onMounted(() => {
      loadOrders()
      loadSubmittedOrders()
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
      submittedOrders,
      vendors,
      submittedLoading,
      submittedError,
      drafts,
      saving,
      saveErrors,
      isDirty,
      saveOrder,
      safeTrackingUrl,
      formatMoney
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

/* Submitted orders */
.submitted-table td {
  vertical-align: top;
}

.field {
  width: 100%;
  min-width: 120px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #0f172a;
  background: white;
}

.save-btn {
  padding: 0.25rem 0.75rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
}

.save-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.actions-cell {
  white-space: nowrap;
}

.track-link {
  display: block;
  margin-top: 0.375rem;
  font-size: 0.813rem;
  color: #2563eb;
}

.row-error {
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: #991b1b;
  white-space: normal;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
}
</style>
