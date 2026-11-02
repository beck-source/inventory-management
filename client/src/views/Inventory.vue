<template>
  <div class="inventory">
    <PageHeader :title="t('inventory.title')" />
    <FilterBar />

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <Card class="gap-4">
        <CardHeader>
          <CardTitle>{{ t('inventory.stockLevels') }} ({{ filteredItems.length }} {{ t('inventory.skus') }})</CardTitle>
          <CardAction class="self-center">
            <div class="search-box">
              <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
              </svg>
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="t('inventory.searchPlaceholder')"
                class="search-input"
              />
              <button v-if="searchQuery" @click="searchQuery = ''" class="clear-search">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </CardAction>
        </CardHeader>
        <CardContent>
          <div class="table-no-pad">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{{ t('inventory.table.sku') }}</TableHead>
                  <TableHead>{{ t('inventory.table.itemName') }}</TableHead>
                  <TableHead>{{ t('inventory.table.category') }}</TableHead>
                  <TableHead>{{ t('inventory.table.quantityOnHand') }}</TableHead>
                  <TableHead>{{ t('inventory.table.reorderPoint') }}</TableHead>
                  <TableHead>{{ t('inventory.table.unitCost') }}</TableHead>
                  <TableHead>{{ t('inventory.table.totalValue') }}</TableHead>
                  <TableHead>{{ t('inventory.table.location') }}</TableHead>
                  <TableHead>{{ t('inventory.table.status') }}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="item in filteredItems"
                  :key="item.id"
                  class="clickable-row"
                  @click="showItemDetail(item)"
                >
                  <TableCell><strong>{{ item.sku }}</strong></TableCell>
                  <TableCell>{{ translateProductName(item.name) }}</TableCell>
                  <TableCell>{{ translateCategory(item.category) }}</TableCell>
                  <TableCell><strong>{{ item.quantity_on_hand }}</strong></TableCell>
                  <TableCell>{{ item.reorder_point }}</TableCell>
                  <TableCell>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</TableCell>
                  <TableCell><strong>{{ currencySymbol }}{{ (item.quantity_on_hand * item.unit_cost).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong></TableCell>
                  <TableCell>{{ translateWarehouse(item.location) }}</TableCell>
                  <TableCell>
                    <Badge :variant="getStockStatusClass(item)">
                      {{ getStockStatus(item) }}
                    </Badge>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>

    <InventoryDetailModal
      :is-open="showItemModal"
      :inventory-item="selectedItem"
      @close="showItemModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import PageHeader from '../components/ui/PageHeader.vue'
import { Card, CardHeader, CardAction, CardTitle, CardContent } from '@/components/ui/card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import FilterBar from '../components/FilterBar.vue'
import InventoryDetailModal from '../components/InventoryDetailModal.vue'

export default {
  name: 'Inventory',
  components: {
    PageHeader,
    Card,
    CardHeader,
    CardAction,
    CardTitle,
    CardContent,
    Table,
    TableHeader,
    TableBody,
    TableRow,
    TableHead,
    TableCell,
    Badge,
    FilterBar,
    InventoryDetailModal
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const items = ref([])
    const searchQuery = ref('')

    const showItemModal = ref(false)
    const selectedItem = ref(null)

    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const STATUS_ORDER = { 'lowStock': 0, 'adequate': 1, 'inStock': 2 }

    const getStockStatusKey = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'lowStock'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'adequate'
      } else {
        return 'inStock'
      }
    }

    const filteredItems = computed(() => {
      let filtered = items.value

      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase().trim()
        filtered = filtered.filter(item =>
          item.name.toLowerCase().includes(query)
        )
      }

      return filtered.slice().sort((a, b) => {
        const statusA = getStockStatusKey(a)
        const statusB = getStockStatusKey(b)
        return STATUS_ORDER[statusA] - STATUS_ORDER[statusB]
      })
    })

    const loadInventory = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        items.value = await api.getInventory({
          warehouse: filters.warehouse,
          category: filters.category
        })
      } catch (err) {
        error.value = 'Failed to load inventory: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch([selectedLocation, selectedCategory], () => {
      loadInventory()
    })

    const getStockStatus = (item) => {
      const key = getStockStatusKey(item)
      return t(`status.${key}`)
    }

    const getStockStatusClass = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'danger'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'warn'
      } else {
        return 'success'
      }
    }

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

    const showItemDetail = (item) => {
      selectedItem.value = item
      showItemModal.value = true
    }

    onMounted(loadInventory)

    return {
      t,
      loading,
      error,
      items,
      searchQuery,
      filteredItems,
      getStockStatus,
      getStockStatusClass,
      translateCategory,
      showItemModal,
      selectedItem,
      showItemDetail,
      currencySymbol,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 240px;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--ink-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 36px 0 36px;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  font-size: 13px;
  color: var(--ink-primary);
  background: var(--surface-bg);
  font-family: inherit;
  transition: border-color 0.15s;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
  background: var(--surface-card);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-input::placeholder {
  color: var(--ink-muted);
}

.clear-search {
  position: absolute;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--ink-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.clear-search:hover {
  background: var(--line);
  color: var(--ink-primary);
}

.table-no-pad {
  margin: 0 calc(-1 * var(--sp-6));
  margin-bottom: calc(-1 * var(--sp-6));
}

.clickable-row {
  cursor: pointer;
}

.clickable-row:hover {
  background: var(--surface-muted) !important;
}
</style>
