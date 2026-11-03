<template>
  <!-- Dialog provides Escape-to-close, focus trap and scroll lock; the guard keeps the body from rendering with null data. -->
  <!-- `a && b` yields the data object, not a Boolean; reka-ui Dialog needs a real Boolean for its open/focus-trap props -->
  <Dialog :open="!!(isOpen && product)" @update:open="(open) => { if (!open) close() }">
    <!-- p-0/gap-0 so header, body and footer own their padding; sm:max-w-[90vw] matches the old container width -->
    <DialogContent class="sm:max-w-[90vw] max-h-[90vh] p-0 gap-0 overflow-hidden flex flex-col">
      <DialogHeader class="p-6 border-b border-border">
        <DialogTitle class="text-base font-semibold text-[var(--ink-primary)]">Product Details</DialogTitle>
        <DialogDescription class="sr-only">Product Details</DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-y-auto p-6">
        <div class="product-header">
          <div class="product-icon">
            <svg width="24" height="24" viewBox="0 0 48 48" fill="none">
              <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5"/>
              <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="product-title-section">
            <h4 class="product-name">{{ product.name }}</h4>
            <div class="product-sku">SKU: {{ product.sku }}</div>
          </div>
          <Badge :variant="getStockVariant(product.stockLevel)">
            {{ product.stockLevel }}
          </Badge>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">Category</div>
            <div class="info-value">{{ product.category }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Warehouse</div>
            <div class="info-value">{{ product.warehouse }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Units Ordered</div>
            <div class="info-value">{{ product.unitsOrdered }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Total Revenue</div>
            <div class="info-value accent-value">{{ currencySymbol }}{{ product.revenue.toLocaleString() }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Current Stock</div>
            <div class="info-value">{{ product.quantityOnHand }} units</div>
          </div>
          <div class="info-item">
            <div class="info-label">Reorder Point</div>
            <div class="info-value">{{ product.reorderPoint }} units</div>
          </div>
          <div class="info-item">
            <div class="info-label">First Order Date</div>
            <div class="info-value">{{ formatDate(product.firstOrderDate) }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Stock Status</div>
            <div class="info-value">
              <Badge :variant="getStockVariant(product.stockLevel)">{{ product.stockLevel }}</Badge>
            </div>
          </div>
        </div>
      </div>

      <DialogFooter class="p-6 border-t border-border">
        <Button variant="ghost" @click="close">Close</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'

const { currentCurrency } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  product: { type: Object, default: null }
})

const emit = defineEmits(['close'])

const close = () => emit('close')

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const getStockVariant = (stockLevel) => {
  if (stockLevel === 'In Stock') return 'success'
  if (stockLevel === 'Low Stock') return 'warn'
  if (stockLevel === 'Out of Stock') return 'danger'
  return 'neutral'
}
</script>

<style scoped>
.product-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 24px;
}

.product-icon {
  width: 48px;
  height: 48px;
  background: var(--accent);
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.product-title-section {
  flex: 1;
  min-width: 0;
}

.product-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--ink-primary);
  margin: 0 0 4px 0;
}

.product-sku {
  font-size: 12px;
  color: var(--ink-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-muted);
}

.info-value {
  font-size: 13px;
  color: var(--ink-primary);
  font-weight: 500;
}

.accent-value {
  font-size: 14px;
  color: var(--accent);
  font-weight: 700;
}
</style>
