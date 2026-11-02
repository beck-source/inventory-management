<template>
  <div class="filters-bar">
    <div class="filters-grid">
      <div class="filter-group">
        <label>{{ t('filters.timePeriod') }}</label>
        <Select v-model="selectedPeriod">
          <SelectTrigger class="filter-select" :aria-label="t('filters.timePeriod')">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{{ t('filters.allMonths') }}</SelectItem>
            <SelectItem value="2025-01">{{ t('months.january') }}</SelectItem>
            <SelectItem value="2025-02">{{ t('months.february') }}</SelectItem>
            <SelectItem value="2025-03">{{ t('months.march') }}</SelectItem>
            <SelectItem value="2025-04">{{ t('months.april') }}</SelectItem>
            <SelectItem value="2025-05">{{ t('months.may') }}</SelectItem>
            <SelectItem value="2025-06">{{ t('months.june') }}</SelectItem>
            <SelectItem value="2025-07">{{ t('months.july') }}</SelectItem>
            <SelectItem value="2025-08">{{ t('months.august') }}</SelectItem>
            <SelectItem value="2025-09">{{ t('months.september') }}</SelectItem>
            <SelectItem value="2025-10">{{ t('months.october') }}</SelectItem>
            <SelectItem value="2025-11">{{ t('months.november') }}</SelectItem>
            <SelectItem value="2025-12">{{ t('months.december') }}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="filter-group">
        <label>{{ t('filters.location') }}</label>
        <Select v-model="selectedLocation">
          <SelectTrigger class="filter-select" :aria-label="t('filters.location')">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{{ t('filters.all') }}</SelectItem>
            <SelectItem value="San Francisco">{{ t('warehouses.sanFrancisco') }}</SelectItem>
            <SelectItem value="London">{{ t('warehouses.london') }}</SelectItem>
            <SelectItem value="Tokyo">{{ t('warehouses.tokyo') }}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="filter-group">
        <label>{{ t('filters.category') }}</label>
        <Select v-model="selectedCategory">
          <SelectTrigger class="filter-select" :aria-label="t('filters.category')">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{{ t('filters.all') }}</SelectItem>
            <SelectItem value="circuit boards">{{ t('categories.circuitBoards') }}</SelectItem>
            <SelectItem value="sensors">{{ t('categories.sensors') }}</SelectItem>
            <SelectItem value="actuators">{{ t('categories.actuators') }}</SelectItem>
            <SelectItem value="controllers">{{ t('categories.controllers') }}</SelectItem>
            <SelectItem value="power supplies">{{ t('categories.powerSupplies') }}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="filter-group">
        <label>{{ t('filters.orderStatus') }}</label>
        <Select v-model="selectedStatus">
          <SelectTrigger class="filter-select" :aria-label="t('filters.orderStatus')">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{{ t('filters.all') }}</SelectItem>
            <SelectItem value="delivered">{{ t('status.delivered') }}</SelectItem>
            <SelectItem value="shipped">{{ t('status.shipped') }}</SelectItem>
            <SelectItem value="processing">{{ t('status.processing') }}</SelectItem>
            <SelectItem value="backordered">{{ t('status.backordered') }}</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>

    <button
      class="reset-btn"
      @click="resetFilters"
      :disabled="!hasActiveFilters"
      title="Reset all filters"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
      </svg>
    </button>
  </div>
</template>

<script>
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'FilterBar',
  components: { Select, SelectContent, SelectItem, SelectTrigger, SelectValue },
  setup() {
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    } = useFilters()

    const { t } = useI18n()

    return {
      t,
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    }
  }
}
</script>

<style scoped>
.filters-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: 0 0 var(--sp-6);
  border-bottom: 1px solid var(--line);
  margin-bottom: var(--sp-6);
}

.filters-grid {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  flex: 1;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.filter-group label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-muted);
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Compact trigger look. Scoped rules are unlayered, so they win over the Select utility classes
   (class lands on the trigger root element, which receives this component's scope id). */
.filter-select {
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  font-size: 13px;
  color: var(--ink-primary);
  background: var(--surface-card);
  box-shadow: none;
  min-width: 0;
}

.filter-select:hover {
  border-color: var(--line-strong);
}

.filter-select:focus-visible {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.reset-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  color: var(--ink-muted);
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}

.reset-btn:hover:not(:disabled) {
  background: var(--surface-muted);
  border-color: var(--line-strong);
  color: var(--ink-primary);
}

.reset-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
</style>
