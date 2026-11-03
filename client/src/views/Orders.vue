<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t("orders.title") }}</h2>
      <p>{{ t("orders.description") }}</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          {{ t("orders.submitted.title") }} ({{ submittedOrders.length }})
        </h3>
      </div>
      <ErrorState
        v-if="submittedLoading || submittedError"
        :loading="submittedLoading"
        :message="submittedError || ''"
        @retry="reloadSubmitted"
      />
      <div v-else-if="submittedOrders.length === 0" class="empty-state">
        {{ t("orders.submitted.empty") }}
      </div>
      <div v-else class="table-container">
        <table class="orders-table">
          <caption class="sr-only">
            {{
              t("orders.submitted.title")
            }}
          </caption>
          <thead>
            <tr>
              <th scope="col" class="col-order-number">
                {{ t("orders.table.orderNumber") }}
              </th>
              <th scope="col" class="col-date">
                {{ t("orders.table.submittedDate") }}
              </th>
              <th scope="col" class="col-items">
                {{ t("orders.table.items") }}
              </th>
              <th scope="col" class="col-value">
                {{ t("orders.table.totalValue") }}
              </th>
              <th scope="col" class="col-date">
                {{ t("orders.table.leadTime") }}
              </th>
              <th scope="col" class="col-date">
                {{ t("orders.table.expectedDelivery") }}
              </th>
              <th scope="col" class="col-status">
                {{ t("orders.table.status") }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in submittedOrders" :key="order.id">
              <td class="col-order-number">
                <strong>{{ order.order_number }}</strong>
              </td>
              <td class="col-date">{{ formatDate(order.submitted_at) }}</td>
              <td class="col-items">
                <details class="items-details">
                  <summary class="items-summary">
                    {{ t("orders.itemsCount", { count: order.items.length }) }}
                  </summary>
                  <div class="items-dropdown">
                    <div
                      v-for="item in order.items"
                      :key="item.sku"
                      class="item-entry"
                    >
                      <span class="item-name">{{
                        translateProductName(item.name)
                      }}</span>
                      <span class="item-meta"
                        >{{ t("orders.quantity") }}: {{ item.quantity }} @
                        {{ currencySymbol
                        }}{{ formatAmount(item.unit_cost) }}</span
                      >
                    </div>
                  </div>
                </details>
              </td>
              <td class="col-value">
                <strong
                  >{{ currencySymbol
                  }}{{ formatAmount(order.total_cost) }}</strong
                >
              </td>
              <td class="col-date">{{ order.lead_time_days }}</td>
              <td class="col-date">
                {{ formatDate(order.expected_delivery) }}
              </td>
              <td class="col-status">
                <span class="badge info">{{ t("status.submitted") }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ErrorState
      v-if="loading || error"
      :loading="loading"
      :message="error || ''"
      @retry="reload"
    />
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t("status.delivered") }}</div>
          <div class="stat-value">
            {{ getOrdersByStatus("Delivered").length }}
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t("status.shipped") }}</div>
          <div class="stat-value">
            {{ getOrdersByStatus("Shipped").length }}
          </div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t("status.processing") }}</div>
          <div class="stat-value">
            {{ getOrdersByStatus("Processing").length }}
          </div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t("status.backordered") }}</div>
          <div class="stat-value">
            {{ getOrdersByStatus("Backordered").length }}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t("orders.allOrders") }} ({{ orders.length }})
          </h3>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <caption class="sr-only">
              {{
                t("orders.allOrders")
              }}
            </caption>
            <thead>
              <tr>
                <th scope="col" class="col-order-number">
                  {{ t("orders.table.orderNumber") }}
                </th>
                <th scope="col" class="col-customer">
                  {{ t("orders.table.customer") }}
                </th>
                <th scope="col" class="col-items">
                  {{ t("orders.table.items") }}
                </th>
                <th scope="col" class="col-status">
                  {{ t("orders.table.status") }}
                </th>
                <th scope="col" class="col-date">
                  {{ t("orders.table.orderDate") }}
                </th>
                <th scope="col" class="col-date">
                  {{ t("orders.table.expectedDelivery") }}
                </th>
                <th scope="col" class="col-value">
                  {{ t("orders.table.totalValue") }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="col-order-number">
                  <strong>{{ order.order_number }}</strong>
                </td>
                <td class="col-customer">
                  {{ translateCustomerName(order.customer) }}
                </td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{
                        t("orders.itemsCount", { count: order.items.length })
                      }}
                    </summary>
                    <div class="items-dropdown">
                      <div
                        v-for="(item, idx) in order.items"
                        :key="idx"
                        class="item-entry"
                      >
                        <span class="item-name">{{
                          translateProductName(item.name)
                        }}</span>
                        <span class="item-meta"
                          >{{ t("orders.quantity") }}: {{ item.quantity }} @
                          {{ currencySymbol }}{{ item.unit_price }}</span
                        >
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status">
                  <span :class="['badge', getOrderStatusClass(order.status)]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td class="col-date">{{ formatDate(order.order_date) }}</td>
                <td class="col-date">
                  {{ formatDate(order.expected_delivery) }}
                </td>
                <td class="col-value">
                  <strong
                    >{{ currencySymbol
                    }}{{ order.total_value.toLocaleString() }}</strong
                  >
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
import { ref, watch, computed } from "vue";
import { api } from "../api";
import { useFilters } from "../composables/useFilters";
import { useI18n } from "../composables/useI18n";
import { useFilteredLoad } from "../composables/useFilteredLoad";
import ErrorState from "../components/ErrorState.vue";

export default {
  name: "Orders",
  components: { ErrorState },
  setup() {
    const { t, currentCurrency, translateProductName, translateCustomerName } =
      useI18n();

    const currencySymbol = computed(() => {
      return currentCurrency.value === "JPY" ? "¥" : "$";
    });
    const orders = ref([]);
    const submittedOrders = ref([]);

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters,
    } = useFilters();

    const { loading, error, reload } = useFilteredLoad(async () => {
      const fetchedOrders = await api.getOrders(getCurrentFilters());

      // Sort orders by order_date (earliest first)
      orders.value = fetchedOrders.sort((a, b) => {
        const dateA = new Date(a.order_date);
        const dateB = new Date(b.order_date);
        return dateA - dateB;
      });
    });

    // Watch for filter changes and reload data
    watch(
      [selectedPeriod, selectedLocation, selectedCategory, selectedStatus],
      reload,
    );

    const getOrdersByStatus = (status) => {
      return orders.value.filter((order) => order.status === status);
    };

    const getOrderStatusClass = (status) => {
      const statusMap = {
        Delivered: "success",
        Shipped: "info",
        Processing: "warning",
        Backordered: "danger",
      };
      return statusMap[status] || "info";
    };

    const formatAmount = (value) =>
      value.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n();
      const locale = currentLocale.value === "ja" ? "ja-JP" : "en-US";
      const dateOnly =
        typeof dateString === "string" &&
        /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateString);
      const date = dateOnly
        ? new Date(
            Number(dateOnly[1]),
            Number(dateOnly[2]) - 1,
            Number(dateOnly[3]),
          )
        : new Date(dateString);
      if (isNaN(date.getTime())) return dateString || "-";
      return date.toLocaleDateString(locale, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    };

    const {
      loading: submittedLoading,
      error: submittedError,
      reload: reloadSubmitted,
    } = useFilteredLoad(async () => {
      submittedOrders.value = await api.getSubmittedOrders();
    });

    return {
      formatAmount,
      t,
      loading,
      error,
      reload,
      reloadSubmitted,
      orders,
      submittedOrders,
      submittedLoading,
      submittedError,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      currencySymbol,
      translateProductName,
      translateCustomerName,
    };
  },
};
</script>

<style scoped>
/* Fixed table layout to prevent column shifting */
.orders-table {
  table-layout: fixed;
  width: 100%;
}

/* Column widths */
.col-order-number {
  width: 130px;
}

.col-customer {
  width: 180px;
}

.col-items {
  width: 200px;
}

.col-status {
  width: 130px;
}

.col-date {
  width: 140px;
}

.col-value {
  width: 120px;
}

/* Items details styling */
.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: var(--blue);
  font-weight: 500;
  list-style: none;
  user-select: none;
  display: inline-block;
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: "▶";
  display: inline-block;
  margin-right: 0.375rem;
  font-size: 0.75rem;
  transition: transform 0.2s;
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-summary:hover {
  color: var(--accent);
  text-decoration: underline;
}

/* Dropdown container */
.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 0.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow:
    0 4px 6px -1px var(--shadow-a),
    0 2px 4px -1px var(--shadow-a);
  padding: 0.75rem;
  z-index: 10;
  min-width: 300px;
  max-width: 400px;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
  border-bottom: 1px solid var(--border-subtle);
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-strong);
}

.item-meta {
  font-size: 0.813rem;
  color: var(--text-muted);
}

.empty-state {
  padding: 1.5rem;
  text-align: center;
  color: var(--text-muted);
}
</style>
