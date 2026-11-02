<template>
  <!-- Dialog provides Escape-to-close, focus trap and scroll lock; the guard keeps the body from rendering with null data. -->
  <!-- `a && b` yields the data object, not a Boolean; reka-ui Dialog needs a real Boolean for its open/focus-trap props -->
  <Dialog :open="!!(isOpen && backlogItem)" @update:open="(open) => { if (!open) close() }">
    <!-- p-0/gap-0 so header, body and footer own their padding; sm:max-w-[90vw] matches the old container width -->
    <DialogContent class="sm:max-w-[90vw] max-h-[90vh] p-0 gap-0 overflow-hidden flex flex-col">
      <DialogHeader class="p-6 border-b border-border">
        <DialogTitle class="text-base font-semibold text-[var(--ink-primary)]">Inventory Shortage Details</DialogTitle>
        <DialogDescription class="sr-only">Inventory Shortage Details</DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-y-auto p-6">
        <div class="shortage-header">
          <div class="shortage-icon">
            <svg width="24" height="24" viewBox="0 0 48 48" fill="none">
              <path d="M24 8L24 28M24 34L24 36" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
              <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="3"/>
            </svg>
          </div>
          <div class="shortage-title-section">
            <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
            <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
          </div>
          <Badge :variant="backlogItem.priority === 'high' ? 'danger' : backlogItem.priority === 'medium' ? 'warn' : 'accent'">
            {{ backlogItem.priority }} Priority
          </Badge>
        </div>

        <div class="shortage-summary">
          <Card><CardContent>
            <div class="summary-label">Shortage Amount</div>
            <div class="summary-value danger">{{ shortage }} units</div>
          </CardContent></Card>
          <Card><CardContent>
            <div class="summary-label">Days Delayed</div>
            <div class="summary-value warn">{{ backlogItem.days_delayed }} days</div>
          </CardContent></Card>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">Order ID</div>
            <div class="info-value mono">{{ backlogItem.order_id }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Item SKU</div>
            <div class="info-value mono">{{ backlogItem.item_sku }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Quantity Needed</div>
            <div class="info-value">{{ backlogItem.quantity_needed }} units</div>
          </div>
          <div class="info-item">
            <div class="info-label">Quantity Available</div>
            <div class="info-value">{{ backlogItem.quantity_available }} units</div>
          </div>
          <div class="info-item">
            <div class="info-label">Expected Date</div>
            <div class="info-value">{{ formatDate(backlogItem.expected_date) }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Status</div>
            <div class="info-value">
              <Badge variant="danger">Backordered</Badge>
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

const { translateProductName } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null }
})

const emit = defineEmits(['close'])

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const close = () => emit('close')

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<style scoped>
.shortage-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 24px;
}

.shortage-icon {
  width: 48px;
  height: 48px;
  background: var(--danger);
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.shortage-title-section {
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

.shortage-summary {
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

.summary-value.danger { color: var(--danger); }
.summary-value.warn { color: var(--warn); }

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

.info-value.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--accent);
}
</style>
