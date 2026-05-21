import axios from "axios";

const API_BASE_URL = "http://localhost:8001/api";

export const api = {
  async getInventory(filters = {}) {
    const params = new URLSearchParams();
    if (filters.warehouse && filters.warehouse !== "all")
      params.append("warehouse", filters.warehouse);
    if (filters.category && filters.category !== "all")
      params.append("category", filters.category);

    const response = await axios.get(
      `${API_BASE_URL}/inventory?${params.toString()}`,
    );
    return response.data;
  },

  async getInventoryItem(id) {
    const response = await axios.get(`${API_BASE_URL}/inventory/${id}`);
    return response.data;
  },

  async getOrders(filters = {}) {
    const params = new URLSearchParams();
    if (filters.warehouse && filters.warehouse !== "all")
      params.append("warehouse", filters.warehouse);
    if (filters.category && filters.category !== "all")
      params.append("category", filters.category);
    if (filters.status && filters.status !== "all")
      params.append("status", filters.status);
    if (filters.month && filters.month !== "all")
      params.append("month", filters.month);

    const response = await axios.get(
      `${API_BASE_URL}/orders?${params.toString()}`,
    );
    return response.data;
  },

  async getOrder(id) {
    const response = await axios.get(`${API_BASE_URL}/orders/${id}`);
    return response.data;
  },

  // Submit a restocking order from the Restocking tab.
  // payload shape: { items: [{ sku, name, quantity, unit_price, lead_time_days }], customer?, warehouse?, category? }
  async submitOrder(payload) {
    const response = await axios.post(`${API_BASE_URL}/orders`, payload);
    return response.data;
  },

  async getDemandForecasts() {
    const response = await axios.get(`${API_BASE_URL}/demand`);
    return response.data;
  },

  async getBacklog() {
    const response = await axios.get(`${API_BASE_URL}/backlog`);
    return response.data;
  },

  async getDashboardSummary(filters = {}) {
    const params = new URLSearchParams();
    if (filters.warehouse && filters.warehouse !== "all")
      params.append("warehouse", filters.warehouse);
    if (filters.category && filters.category !== "all")
      params.append("category", filters.category);
    if (filters.status && filters.status !== "all")
      params.append("status", filters.status);
    if (filters.month && filters.month !== "all")
      params.append("month", filters.month);

    const response = await axios.get(
      `${API_BASE_URL}/dashboard/summary?${params.toString()}`,
    );
    return response.data;
  },

  async getSpendingSummary() {
    const response = await axios.get(`${API_BASE_URL}/spending/summary`);
    return response.data;
  },

  async getMonthlySpending() {
    const response = await axios.get(`${API_BASE_URL}/spending/monthly`);
    return response.data;
  },

  async getCategorySpending() {
    const response = await axios.get(`${API_BASE_URL}/spending/categories`);
    return response.data;
  },

  async getTransactions() {
    const response = await axios.get(`${API_BASE_URL}/spending/transactions`);
    return response.data;
  },

  // NOTE: /api/tasks and /api/purchase-orders endpoints were referenced here previously
  // but never implemented server-side. Removed in the Tier-1 audit cleanup to silence the
  // 404 storm on every page mount (security-findings #8, ux-findings #13, perf-findings P-14).
  // If task or purchase-order persistence is re-introduced, add Pydantic-validated routes
  // server-side first, then restore matching client methods here.
};
