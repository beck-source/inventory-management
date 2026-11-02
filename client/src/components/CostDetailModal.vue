<template>
  <!-- Dialog provides Escape-to-close, focus trap and scroll lock; the guard keeps the body from rendering with null data. -->
  <!-- `a && b` yields the data object, not a Boolean; reka-ui Dialog needs a real Boolean for its open/focus-trap props -->
  <Dialog :open="!!(isOpen && costData)" @update:open="(open) => { if (!open) close() }">
    <!-- p-0/gap-0 so header, body and footer own their padding; sm:max-w-[90vw] matches the old container width -->
    <DialogContent class="sm:max-w-[90vw] max-h-[90vh] p-0 gap-0 overflow-hidden flex flex-col">
      <DialogHeader class="p-6 border-b border-border">
        <DialogTitle class="text-base font-semibold text-[var(--ink-primary)]">{{ costData.month }} Cost Breakdown</DialogTitle>
        <DialogDescription class="sr-only">{{ costData.month }} Cost Breakdown</DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-y-auto p-6">
        <Card class="total-card"><CardContent>
          <div class="summary-label">Total Costs</div>
          <div class="summary-value">{{ currencySymbol }}{{ totalCosts.toLocaleString() }}</div>
        </CardContent></Card>

        <div class="cost-breakdown">
          <div class="cost-item cost-item-accent">
            <div class="cost-header">
              <div class="cost-icon" style="background: var(--accent);">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <rect x="4" y="6" width="16" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                  <path d="M8 6V4M16 6V4M4 10H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="cost-info">
                <div class="cost-name">Procurement</div>
                <div class="cost-amount">{{ currencySymbol }}{{ costData.procurement.toLocaleString() }}</div>
              </div>
            </div>
            <div class="cost-percentage">{{ getProcurementPercentage() }}% of total</div>
          </div>

          <div class="cost-item cost-item-accent2">
            <div class="cost-header">
              <div class="cost-icon" style="background: var(--accent-2);">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="2"/>
                  <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="cost-info">
                <div class="cost-name">Operational</div>
                <div class="cost-amount">{{ currencySymbol }}{{ costData.operational.toLocaleString() }}</div>
              </div>
            </div>
            <div class="cost-percentage">{{ getOperationalPercentage() }}% of total</div>
          </div>

          <div class="cost-item cost-item-success">
            <div class="cost-header">
              <div class="cost-icon" style="background: var(--success);">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                  <path d="M6 20C6 16.6863 8.68629 14 12 14C15.3137 14 18 16.6863 18 20" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="cost-info">
                <div class="cost-name">Labor</div>
                <div class="cost-amount">{{ currencySymbol }}{{ costData.labor.toLocaleString() }}</div>
              </div>
            </div>
            <div class="cost-percentage">{{ getLaborPercentage() }}% of total</div>
          </div>

          <div class="cost-item cost-item-warn">
            <div class="cost-header">
              <div class="cost-icon" style="background: var(--warn);">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M3 12L5 10M5 10L12 3L19 10M5 10V20C5 20.5523 5.44772 21 6 21H9M19 10L21 12M19 10V20C19 20.5523 18.5523 21 18 21H15M9 21C9 21 9 18 9 16C9 14 10 14 12 14C14 14 15 14 15 16C15 18 15 21 15 21M9 21H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="cost-info">
                <div class="cost-name">Overhead</div>
                <div class="cost-amount">{{ currencySymbol }}{{ costData.overhead.toLocaleString() }}</div>
              </div>
            </div>
            <div class="cost-percentage">{{ getOverheadPercentage() }}% of total</div>
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
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'

const { currentCurrency } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  costData: { type: Object, default: null }
})

const emit = defineEmits(['close'])

const totalCosts = computed(() => {
  if (!props.costData) return 0
  return props.costData.procurement + props.costData.operational +
         props.costData.labor + props.costData.overhead
})

const getProcurementPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.procurement / totalCosts.value) * 100).toFixed(1)
}

const getOperationalPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.operational / totalCosts.value) * 100).toFixed(1)
}

const getLaborPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.labor / totalCosts.value) * 100).toFixed(1)
}

const getOverheadPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.overhead / totalCosts.value) * 100).toFixed(1)
}

const close = () => emit('close')
</script>

<style scoped>
.total-card {
  margin-bottom: 24px;
  text-align: center;
  background: var(--accent);
}

.summary-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255,255,255,0.85);
  margin-bottom: 8px;
}

.summary-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--ink-inverse);
  line-height: 1.25;
}

.cost-breakdown {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cost-item {
  padding: 16px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
}

.cost-item-accent {
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.06);
}

.cost-item-accent2 {
  border-color: rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.06);
}

.cost-item-success {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.06);
}

.cost-item-warn {
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.06);
}

.cost-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.cost-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.cost-info {
  flex: 1;
}

.cost-name {
  font-weight: 600;
  color: var(--ink-primary);
  font-size: 14px;
  margin-bottom: 4px;
}

.cost-amount {
  font-size: 20px;
  font-weight: 700;
  color: var(--ink-primary);
}

.cost-percentage {
  font-size: 12px;
  color: var(--ink-muted);
  font-weight: 500;
}
</style>
