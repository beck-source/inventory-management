<template>
  <div class="backlog">
    <div class="page-header">
      <h2>{{ t("backlog.title") }}</h2>
      <p>{{ t("backlog.description") }}</p>
    </div>

    <ErrorState
      v-if="loading || error"
      :loading="loading"
      :message="error || ''"
      @retry="reload"
    />
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card danger">
          <div class="stat-label">{{ t("backlog.highPriority") }}</div>
          <div class="stat-value">
            {{ getBacklogByPriority("high").length }}
          </div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t("backlog.mediumPriority") }}</div>
          <div class="stat-value">
            {{ getBacklogByPriority("medium").length }}
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t("backlog.lowPriority") }}</div>
          <div class="stat-value">{{ getBacklogByPriority("low").length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t("backlog.totalItems") }}</div>
          <div class="stat-value">{{ backlogItems.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t("backlog.itemsHeading") }}</h3>
        </div>
        <div v-if="backlogItems.length === 0" class="empty-state">
          {{ t("backlog.empty") }}
        </div>
        <div v-else class="table-container">
          <table>
            <caption class="sr-only">
              {{
                t("backlog.itemsHeading")
              }}
            </caption>
            <thead>
              <tr>
                <th scope="col">{{ t("backlog.table.orderId") }}</th>
                <th scope="col">{{ t("backlog.table.sku") }}</th>
                <th scope="col">{{ t("backlog.table.itemName") }}</th>
                <th scope="col">{{ t("backlog.table.quantityNeeded") }}</th>
                <th scope="col">{{ t("backlog.table.quantityAvailable") }}</th>
                <th scope="col">{{ t("backlog.table.shortage") }}</th>
                <th scope="col">{{ t("backlog.table.daysDelayed") }}</th>
                <th scope="col">{{ t("backlog.table.priority") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in backlogItems" :key="item.id">
                <td>
                  <strong>{{ item.order_id }}</strong>
                </td>
                <td>
                  <strong>{{ item.item_sku }}</strong>
                </td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td>{{ item.quantity_needed }}</td>
                <td>{{ item.quantity_available }}</td>
                <td>
                  <span class="badge danger">
                    {{
                      t("backlog.unitsShort", {
                        n: item.quantity_needed - item.quantity_available,
                      })
                    }}
                  </span>
                </td>
                <td>
                  <span
                    :class="
                      item.days_delayed > 7 ? 'delay-severe' : 'delay-moderate'
                    "
                  >
                    {{ t("backlog.days", { n: item.days_delayed }) }}
                  </span>
                </td>
                <td>
                  <span :class="['badge', item.priority]">
                    {{ t("priority." + item.priority) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from "vue";
import { api } from "../api";
import { useFilters } from "../composables/useFilters";
import { useFilteredLoad } from "../composables/useFilteredLoad";
import { useI18n } from "../composables/useI18n";
import ErrorState from "../components/ErrorState.vue";

export default {
  name: "Backlog",
  components: { ErrorState },
  setup() {
    const { t, translateProductName } = useI18n();
    const allBacklogItems = ref([]);
    const inventoryItems = ref([]);

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } =
      useFilters();

    // Filter backlog based on inventory filters
    const backlogItems = computed(() => {
      if (
        selectedLocation.value === "all" &&
        selectedCategory.value === "all"
      ) {
        return allBacklogItems.value;
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map((item) => item.sku));
      return allBacklogItems.value.filter((b) => validSkus.has(b.item_sku));
    });

    const { loading, error, reload } = useFilteredLoad(async () => {
      const filters = getCurrentFilters();

      const [backlogData, inventoryData] = await Promise.all([
        api.getBacklog(),
        api.getInventory({
          warehouse: filters.warehouse,
          category: filters.category,
        }),
      ]);

      allBacklogItems.value = backlogData;
      inventoryItems.value = inventoryData;
    });

    const getBacklogByPriority = (priority) => {
      return backlogItems.value.filter((item) => item.priority === priority);
    };

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], reload);

    return {
      t,
      translateProductName,
      loading,
      error,
      reload,
      backlogItems,
      getBacklogByPriority,
    };
  },
};
</script>

<style scoped>
.empty-state {
  padding: 3rem;
  text-align: center;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--success-fg);
}

.delay-severe {
  color: var(--danger-fg);
}

.delay-moderate {
  color: var(--warning-fg);
}
</style>
