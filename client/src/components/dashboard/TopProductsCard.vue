<template>
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
            @click="$emit('show-product', item)"
          >
            <td><strong>{{ translateProductName(item.name) }}</strong></td>
            <td>{{ item.sku }}</td>
            <td>{{ translateCategory(item.category) }}</td>
            <td>{{ item.unitsOrdered }}</td>
            <td><strong>{{ formatCurrency(item.revenue, selectedCurrency) }}</strong></td>
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
</template>

<script>
import { useI18n } from '../../composables/useI18n'
import { formatCurrency } from '../../utils/currency'

export default {
  name: 'TopProductsCard',
  props: {
    topProducts: {
      type: Array,
      required: true
    },
    selectedCurrency: {
      type: String,
      required: true
    }
  },
  emits: ['show-product'],
  setup() {
    const { t, currentLocale, translateProductName } = useI18n()

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

    const getStockBadge = (level) => {
      if (level === 'In Stock') return 'success'
      if (level === 'Low Stock') return 'warning'
      return 'danger'
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return '-'
      return date.toLocaleDateString(locale, { month: 'short', day: 'numeric', year: 'numeric' })
    }

    return {
      t,
      formatCurrency,
      translateProductName,
      translateCategory,
      translateStockLevel,
      getStockBadge,
      formatDate
    }
  }
}
</script>

<style scoped>
.clickable-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.clickable-row:hover {
  background: var(--color-accent-bg) !important;
}
</style>
