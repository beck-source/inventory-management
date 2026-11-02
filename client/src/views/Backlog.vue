<template>
  <div class="backlog">
    <PageHeader title="Backlog Management" />
    <FilterBar />

    <div v-if="loading" class="loading">Loading backlog...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <Card>
          <div class="stat-label">High Priority</div>
          <div class="stat-value danger">{{ getBacklogByPriority('high').length }}</div>
        </Card>
        <Card>
          <div class="stat-label">Medium Priority</div>
          <div class="stat-value warn">{{ getBacklogByPriority('medium').length }}</div>
        </Card>
        <Card>
          <div class="stat-label">Low Priority</div>
          <div class="stat-value accent">{{ getBacklogByPriority('low').length }}</div>
        </Card>
        <Card>
          <div class="stat-label">Total Backlog Items</div>
          <div class="stat-value">{{ backlogItems.length }}</div>
        </Card>
      </div>

      <Card>
        <template #title>Backlog Items</template>
        <EmptyState v-if="backlogItems.length === 0">
          <template #icon>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="40" height="40" style="color: var(--success)">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </template>
          <template #title>No backlog items - all orders can be fulfilled!</template>
        </EmptyState>
        <div v-else class="table-no-pad">
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>SKU</th>
                  <th>Item Name</th>
                  <th>Quantity Needed</th>
                  <th>Quantity Available</th>
                  <th>Shortage</th>
                  <th>Days Delayed</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in backlogItems" :key="item.id">
                  <td><strong>{{ item.order_id }}</strong></td>
                  <td><strong>{{ item.item_sku }}</strong></td>
                  <td>{{ item.item_name }}</td>
                  <td>{{ item.quantity_needed }}</td>
                  <td>{{ item.quantity_available }}</td>
                  <td>
                    <Badge variant="danger">
                      {{ item.quantity_needed - item.quantity_available }} units short
                    </Badge>
                  </td>
                  <td>
                    <span :style="{ color: item.days_delayed > 7 ? 'var(--danger)' : 'var(--warn)', fontWeight: 600 }">
                      {{ item.days_delayed }} days
                    </span>
                  </td>
                  <td>
                    <Badge :variant="item.priority === 'high' ? 'danger' : item.priority === 'medium' ? 'warn' : 'accent'">
                      {{ item.priority }}
                    </Badge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import PageHeader from '../components/ui/PageHeader.vue'
import Card from '../components/ui/Card.vue'
import Badge from '../components/ui/Badge.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import FilterBar from '../components/FilterBar.vue'

export default {
  name: 'Backlog',
  components: {
    PageHeader,
    Card,
    Badge,
    EmptyState,
    FilterBar
  },
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const allBacklogItems = ref([])
    const inventoryItems = ref([])

    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const backlogItems = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allBacklogItems.value
      }
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allBacklogItems.value.filter(b => validSkus.has(b.item_sku))
    })

    const loadBacklog = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [backlogData, inventoryData] = await Promise.all([
          api.getBacklog(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allBacklogItems.value = backlogData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load backlog: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const getBacklogByPriority = (priority) => {
      return backlogItems.value.filter(item => item.priority === priority)
    }

    watch([selectedLocation, selectedCategory], () => {
      loadBacklog()
    })

    onMounted(loadBacklog)

    return {
      loading,
      error,
      backlogItems,
      getBacklogByPriority
    }
  }
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.stat-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--ink-primary);
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.stat-value.danger { color: var(--danger); }
.stat-value.warn { color: var(--warn); }
.stat-value.accent { color: var(--accent); }

.table-no-pad {
  margin: 0 calc(-1 * var(--sp-6));
  margin-bottom: calc(-1 * var(--sp-6));
}
</style>
