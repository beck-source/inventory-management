<template>
  <!-- Dialog provides Escape-to-close, focus trap and scroll lock; the guard keeps the body from rendering with null data. -->
  <!-- `a && b` yields the data object, not a Boolean; reka-ui Dialog needs a real Boolean for its open/focus-trap props -->
  <Dialog :open="!!(isOpen && inventoryItem)" @update:open="(open) => { if (!open) close() }">
    <!-- p-0/gap-0 so header, body and footer own their padding; sm:max-w-[90vw] matches the old container width -->
    <DialogContent class="sm:max-w-[90vw] max-h-[90vh] p-0 gap-0 overflow-hidden flex flex-col">
      <DialogHeader class="p-6 border-b border-border">
        <DialogTitle class="text-base font-semibold text-[var(--ink-primary)]">Inventory Item Details</DialogTitle>
        <DialogDescription class="sr-only">Inventory Item Details</DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-y-auto p-6">
        <div class="item-header">
          <div class="item-icon" :class="getStockIconClass()">
            <svg width="24" height="24" viewBox="0 0 48 48" fill="none">
              <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5"/>
              <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M16 28H32M16 34H24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="item-title-section">
            <h4 class="item-name">{{ translateProductName(inventoryItem.name) }}</h4>
            <div class="item-sku">SKU: {{ inventoryItem.sku }}</div>
          </div>
          <Badge :variant="getStockStatusVariant()">{{ getStockStatus() }}</Badge>
        </div>

        <div class="stock-summary">
          <Card><CardContent>
            <div class="summary-label">Quantity on Hand</div>
            <div class="summary-value">{{ inventoryItem.quantity_on_hand }} units</div>
          </CardContent></Card>
          <Card><CardContent>
            <div class="summary-label">Stock Level</div>
            <div class="summary-value" :class="getStockStatusVariant()">{{ stockPercentage }}%</div>
            <div class="summary-subtitle">vs. reorder point</div>
          </CardContent></Card>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">Category</div>
            <div class="info-value">{{ inventoryItem.category }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Location</div>
            <div class="info-value">{{ inventoryItem.location }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Reorder Point</div>
            <div class="info-value">{{ inventoryItem.reorder_point }} units</div>
          </div>
          <div class="info-item">
            <div class="info-label">Units Remaining</div>
            <div class="info-value" :style="{ color: inventoryItem.quantity_on_hand <= inventoryItem.reorder_point ? 'var(--danger)' : 'var(--success)' }">
              {{ inventoryItem.quantity_on_hand - inventoryItem.reorder_point }} units
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">Unit Cost</div>
            <div class="info-value">{{ currencySymbol }}{{ inventoryItem.unit_cost.toFixed(2) }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Total Value</div>
            <div class="info-value accent-value">
              {{ currencySymbol }}{{ totalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">Warehouse</div>
            <div class="info-value">{{ translateWarehouse(inventoryItem.location) }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Status</div>
            <div class="info-value">
              <Badge :variant="getStockStatusVariant()">{{ getStockStatus() }}</Badge>
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
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'

const { currentCurrency, translateProductName, translateWarehouse } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  inventoryItem: { type: Object, default: null }
})

const emit = defineEmits(['close'])

const totalValue = computed(() => {
  if (!props.inventoryItem) return 0
  return props.inventoryItem.quantity_on_hand * props.inventoryItem.unit_cost
})

const stockPercentage = computed(() => {
  if (!props.inventoryItem || props.inventoryItem.reorder_point === 0) return 0
  return Math.round((props.inventoryItem.quantity_on_hand / props.inventoryItem.reorder_point) * 100)
})

const close = () => emit('close')

const getStockStatus = () => {
  if (!props.inventoryItem) return 'Unknown'
  if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point) return 'Low Stock'
  if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point * 1.5) return 'Adequate'
  return 'In Stock'
}

const getStockStatusVariant = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger'
  if (status === 'Adequate') return 'warn'
  return 'success'
}

const getStockIconClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'icon-danger'
  if (status === 'Adequate') return 'icon-warn'
  return 'icon-success'
}
</script>

<style scoped>
.item-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 24px;
}

.item-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.item-icon.icon-success { background: var(--success); }
.item-icon.icon-warn { background: var(--warn); }
.item-icon.icon-danger { background: var(--danger); }

.item-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--ink-primary);
  margin: 0 0 4px 0;
}

.item-sku {
  font-size: 12px;
  color: var(--ink-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.stock-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.summary-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-muted);
  margin-bottom: 8px;
}

.summary-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--ink-primary);
  line-height: 1.25;
}

.summary-value.success { color: var(--success); }
.summary-value.warn { color: var(--warn); }
.summary-value.danger { color: var(--danger); }

.summary-subtitle {
  font-size: 12px;
  color: var(--ink-muted);
  margin-top: 4px;
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
