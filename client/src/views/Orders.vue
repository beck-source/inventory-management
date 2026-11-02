<template>
  <div class="orders">
    <PageHeader :title="t('orders.title')" />
    <FilterBar />

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <Card>
          <CardContent>
            <div class="stat-label">{{ t('status.delivered') }}</div>
            <div class="stat-value success">{{ getOrdersByStatus('Delivered').length }}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div class="stat-label">{{ t('status.shipped') }}</div>
            <div class="stat-value accent">{{ getOrdersByStatus('Shipped').length }}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div class="stat-label">{{ t('status.processing') }}</div>
            <div class="stat-value warn">{{ getOrdersByStatus('Processing').length }}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div class="stat-label">{{ t('status.backordered') }}</div>
            <div class="stat-value danger">{{ getOrdersByStatus('Backordered').length }}</div>
          </CardContent>
        </Card>
      </div>

      <Card class="gap-4">
        <CardHeader><CardTitle>{{ t('orders.allOrders') }} ({{ orders.length }})</CardTitle></CardHeader>
        <CardContent>
          <div class="table-no-pad">
            <Table class="orders-table">
              <TableHeader>
                <TableRow>
                  <TableHead class="col-order-number">{{ t('orders.table.orderNumber') }}</TableHead>
                  <TableHead class="col-customer">{{ t('orders.table.customer') }}</TableHead>
                  <TableHead class="col-items">{{ t('orders.table.items') }}</TableHead>
                  <TableHead class="col-status">{{ t('orders.table.status') }}</TableHead>
                  <TableHead class="col-date">{{ t('orders.table.orderDate') }}</TableHead>
                  <TableHead class="col-date">{{ t('orders.table.expectedDelivery') }}</TableHead>
                  <TableHead class="col-value">{{ t('orders.table.totalValue') }}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="order in orders" :key="order.id">
                  <TableCell class="col-order-number"><strong>{{ order.order_number }}</strong></TableCell>
                  <TableCell class="col-customer">{{ translateCustomerName(order.customer) }}</TableCell>
                  <TableCell class="col-items">
                    <details class="items-details">
                      <summary class="items-summary">
                        {{ t('orders.itemsCount', { count: order.items.length }) }}
                      </summary>
                      <div class="items-dropdown">
                        <div v-for="(item, idx) in order.items" :key="item.sku" class="item-entry">
                          <span class="item-name">{{ translateProductName(item.name) }}</span>
                          <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol }}{{ item.unit_price }}</span>
                        </div>
                      </div>
                    </details>
                  </TableCell>
                  <TableCell class="col-status">
                    <Badge :variant="getOrderStatusVariant(order.status)">
                      {{ t(`status.${order.status.toLowerCase()}`) }}
                    </Badge>
                  </TableCell>
                  <TableCell class="col-date">{{ formatDate(order.order_date) }}</TableCell>
                  <TableCell class="col-date">{{ formatDate(order.expected_delivery) }}</TableCell>
                  <TableCell class="col-value"><strong>{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</strong></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import PageHeader from '../components/ui/PageHeader.vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import FilterBar from '../components/FilterBar.vue'

export default {
  name: 'Orders',
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
  setup() {
    const { t, currentCurrency, translateProductName, translateCustomerName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })
    const loading = ref(true)
    const error = ref(null)
    const orders = ref([])

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

    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadOrders()
    })

    const getOrdersByStatus = (status) => {
      return orders.value.filter(order => order.status === status)
    }

    const getOrderStatusVariant = (status) => {
      const map = {
        'Delivered': 'success',
        'Shipped': 'accent',
        'Processing': 'warn',
        'Backordered': 'danger'
      }
      return map[status] || 'neutral'
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

    return {
      t,
      loading,
      error,
      orders,
      getOrdersByStatus,
      getOrderStatusVariant,
      formatDate,
      currencySymbol,
      translateProductName,
      translateCustomerName
    }
  }
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
  gap: 24px;
  margin-bottom: 24px;
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

.stat-value.success { color: var(--success); }
.stat-value.accent { color: var(--accent); }
.stat-value.warn { color: var(--warn); }
.stat-value.danger { color: var(--danger); }

.table-no-pad {
  margin: 0 calc(-1 * var(--sp-6));
  margin-bottom: calc(-1 * var(--sp-6));
}

.orders-table {
  table-layout: fixed;
  width: 100%;
}

.col-order-number { width: 10%; }
.col-customer { width: 16%; }
.col-items { width: 20%; }
.col-status { width: 10%; }
.col-date { width: 12%; }
.col-value { width: 10%; }

.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: var(--accent);
  font-weight: 500;
  list-style: none;
  user-select: none;
  display: inline-block;
  font-size: 13px;
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: '▶';
  display: inline-block;
  margin-right: 6px;
  font-size: 11px;
  transition: transform 0.2s;
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  background: var(--surface-card);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  padding: 12px;
  z-index: 10;
  min-width: 240px;
  max-width: none;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border-bottom: 1px solid var(--surface-muted);
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-primary);
}

.item-meta {
  font-size: 12px;
  color: var(--ink-muted);
}
</style>
