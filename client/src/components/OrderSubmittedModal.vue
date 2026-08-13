<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="handleClose">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              <svg class="check-icon" width="22" height="22" viewBox="0 0 22 22" fill="none">
                <circle cx="11" cy="11" r="10" fill="rgba(255,255,255,0.2)"/>
                <path d="M6.5 11L9.5 14L15.5 8" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ t('orderSubmitted.title') }}
            </h3>
            <button class="close-button" @click="handleClose" :aria-label="t('common.close')">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="order-details">
              <div class="detail-row">
                <span class="detail-label">{{ t('orderSubmitted.orderNumber') }}</span>
                <span class="detail-value order-number">{{ order?.order_number || '—' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">{{ t('orderSubmitted.totalItems') }}</span>
                <span class="detail-value">{{ itemCount }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">{{ t('orderSubmitted.totalValue') }}</span>
                <span class="detail-value">{{ currencySymbol }}{{ formattedTotalValue }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">{{ t('orderSubmitted.expectedDelivery') }}</span>
                <span class="detail-value">{{ formatDate(order?.expected_delivery) }}</span>
              </div>
            </div>

            <p class="forecast-note">{{ t('orderSubmitted.forecastNote') }}</p>

            <div class="items-section">
              <h4 class="items-heading">{{ t('orderSubmitted.orderItems') }}</h4>
              <ul v-if="orderItems.length > 0" class="items-list">
                <li v-for="item in orderItems" :key="item.sku" class="item-row">
                  <span class="item-name">{{ item.name || item.sku }}</span>
                  <span class="item-meta">(SKU: {{ item.sku }}) - {{ t('orders.quantity') }}: {{ item.quantity }}</span>
                </li>
              </ul>
              <p v-else class="no-items">{{ t('common.noData') }}</p>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="handleClose">{{ t('orderSubmitted.close') }}</button>
            <button class="btn-primary" @click="viewInOrders">{{ t('orderSubmitted.viewInOrders') }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../composables/useI18n'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  order: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

const router = useRouter()
const { t, currentLocale, currentCurrency } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const orderItems = computed(() => {
  return Array.isArray(props.order?.items) ? props.order.items : []
})

const itemCount = computed(() => orderItems.value.length)

const formattedTotalValue = computed(() => {
  const value = Number(props.order?.total_value)
  if (isNaN(value)) return '0'
  return value.toLocaleString()
})

const formatDate = (dateString) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '—'
  const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const handleClose = () => {
  emit('close')
}

const viewInOrders = () => {
  emit('close')
  router.push('/orders')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 480px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  background: #10b981;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: white;
  letter-spacing: -0.025em;
  margin: 0;
}

.check-icon {
  flex-shrink: 0;
}

.close-button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.order-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.detail-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
}

.detail-value {
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
  text-align: right;
}

.order-number {
  color: #10b981;
  font-family: 'SFMono-Regular', Consolas, monospace;
}

.forecast-note {
  margin: 0.75rem 0 0;
  font-size: 0.813rem;
  color: #94a3b8;
  font-style: italic;
}

.items-section {
  margin-top: 1.25rem;
}

.items-heading {
  font-size: 0.875rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.75rem;
}

.items-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 220px;
  overflow-y: auto;
}

.item-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.item-name {
  font-weight: 600;
  color: #0f172a;
  word-break: break-word;
}

.item-meta {
  color: #64748b;
  white-space: nowrap;
}

.no-items {
  font-size: 0.875rem;
  color: #94a3b8;
  font-style: italic;
  margin: 0;
}

.modal-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #10b981;
  border: 1px solid #10b981;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover {
  background: #059669;
  border-color: #059669;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}

@media (max-width: 480px) {
  .modal-container {
    max-width: 100%;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn-secondary,
  .btn-primary {
    width: 100%;
    text-align: center;
  }
}
</style>
