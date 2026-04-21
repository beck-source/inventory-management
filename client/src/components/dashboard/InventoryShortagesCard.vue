<template>
  <div class="card chart-card full-width">
    <div class="card-header">
      <h3 class="card-title">{{ t('dashboard.inventoryShortages.title') }} ({{ backlogItems.length }})</h3>
    </div>
    <div v-if="backlogItems.length === 0" class="no-backlog">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="success-icon">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
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
            <th>{{ t('dashboard.inventoryShortages.quantityNeeded') }}</th>
            <th>{{ t('dashboard.inventoryShortages.quantityAvailable') }}</th>
            <th>{{ t('dashboard.inventoryShortages.shortage') }}</th>
            <th>{{ t('dashboard.inventoryShortages.daysDelayed') }}</th>
            <th>{{ t('dashboard.inventoryShortages.priority') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in backlogItems"
            :key="item.id"
          >
            <td @click="$emit('show-detail', item)" style="cursor: pointer;"><strong>{{ item.order_id }}</strong></td>
            <td @click="$emit('show-detail', item)" style="cursor: pointer;"><strong>{{ item.item_sku }}</strong></td>
            <td @click="$emit('show-detail', item)" style="cursor: pointer;">{{ translateProductName(item.item_name) }}</td>
            <td @click="$emit('show-detail', item)" style="cursor: pointer;">{{ item.quantity_needed }}</td>
            <td @click="$emit('show-detail', item)" style="cursor: pointer;">{{ item.quantity_available }}</td>
            <td @click="$emit('show-detail', item)" style="cursor: pointer;">
              <span class="badge danger">
                {{ Math.abs(item.quantity_needed - item.quantity_available) }} {{ t('dashboard.inventoryShortages.unitsShort') }}
              </span>
            </td>
            <td @click="$emit('show-detail', item)" style="cursor: pointer;">
              <span :style="{ color: item.days_delayed > 7 ? '#ef4444' : '#f59e0b', fontWeight: 600 }">
                {{ item.days_delayed }} {{ t('dashboard.inventoryShortages.days') }}
              </span>
            </td>
            <td @click="$emit('show-detail', item)" style="cursor: pointer;">
              <span :class="['badge', item.priority]">
                {{ translatePriority(item.priority) }}
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

export default {
  name: 'InventoryShortagesCard',
  props: {
    backlogItems: {
      type: Array,
      required: true
    }
  },
  emits: ['show-detail'],
  setup() {
    const { t, translateProductName } = useI18n()

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low'),
        'High': t('priority.high'),
        'Medium': t('priority.medium'),
        'Low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    return {
      t,
      translateProductName,
      translatePriority,
      Math
    }
  }
}
</script>

<style scoped>
.no-backlog {
  padding: 3rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.success-icon {
  width: 48px;
  height: 48px;
  color: var(--color-success);
}

.no-backlog-text {
  font-size: 1.125rem;
  color: var(--color-success);
  font-weight: 600;
  margin: 0;
}
</style>
