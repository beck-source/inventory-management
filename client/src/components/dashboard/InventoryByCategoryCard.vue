<template>
  <div class="card chart-card">
    <div class="card-header">
      <h3 class="card-title">{{ t('dashboard.inventoryValue.title') }}</h3>
    </div>
    <div class="chart-content">
      <div class="horizontal-bar-chart" v-if="categoryData.length > 0">
        <div v-for="cat in categoryData" :key="cat.name" class="h-bar-item">
          <div class="h-bar-label">{{ translateCategory(cat.name) }}</div>
          <div class="h-bar-container">
            <div class="h-bar" :style="{ width: (cat.value / maxCategoryValue * 100) + '%', background: cat.color }">
              <span class="h-bar-value">{{ selectedCurrency === 'JPY' ? formatCurrency(cat.value, selectedCurrency) : `$${(cat.value / 1000).toFixed(1)}K` }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-data">{{ t('dashboard.inventoryShortages.noData') }}</div>
    </div>
  </div>
</template>

<script>
import { useI18n } from '../../composables/useI18n'
import { formatCurrency } from '../../utils/currency'

export default {
  name: 'InventoryByCategoryCard',
  props: {
    categoryData: {
      type: Array,
      required: true
    },
    maxCategoryValue: {
      type: Number,
      required: true
    },
    selectedCurrency: {
      type: String,
      required: true
    }
  },
  setup() {
    const { t } = useI18n()

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

    return {
      t,
      formatCurrency,
      translateCategory
    }
  }
}
</script>

<style scoped>
.chart-content {
  padding: 1rem;
}

.horizontal-bar-chart {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 0 1rem;
}

.h-bar-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.h-bar-label {
  width: 120px;
  min-width: 120px;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.h-bar-container {
  flex: 1;
  height: 32px;
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.h-bar {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 0.75rem;
  transition: width 0.6s ease;
}

.h-bar-value {
  font-size: 0.813rem;
  font-weight: 700;
  color: white;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-subtle);
  font-size: 0.875rem;
}
</style>
