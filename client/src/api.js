import axios from 'axios'

// Override with VITE_API_URL to run the backend on a non-default port
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api'

export const api = {
  async getInventory(filters = {}, config = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)

    const response = await axios.get(`${API_BASE_URL}/inventory?${params.toString()}`, config)
    return response.data
  },

  async getInventoryItem(id) {
    const response = await axios.get(`${API_BASE_URL}/inventory/${id}`)
    return response.data
  },

  async getOrders(filters = {}, config = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await axios.get(`${API_BASE_URL}/orders?${params.toString()}`, config)
    return response.data
  },

  async getOrder(id) {
    const response = await axios.get(`${API_BASE_URL}/orders/${id}`)
    return response.data
  },

  async getDemandForecasts(config = {}) {
    const response = await axios.get(`${API_BASE_URL}/demand`, config)
    return response.data
  },

  async getBacklog(config = {}) {
    const response = await axios.get(`${API_BASE_URL}/backlog`, config)
    return response.data
  },

  async getDashboardSummary(filters = {}, config = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await axios.get(`${API_BASE_URL}/dashboard/summary?${params.toString()}`, config)
    return response.data
  },

  async getQuarterlyReports(filters = {}, config = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await axios.get(`${API_BASE_URL}/reports/quarterly?${params.toString()}`, config)
    return response.data
  },

  async getMonthlyTrends(filters = {}, config = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await axios.get(`${API_BASE_URL}/reports/monthly-trends?${params.toString()}`, config)
    return response.data
  },

  async getSpendingSummary(config = {}) {
    const response = await axios.get(`${API_BASE_URL}/spending/summary`, config)
    return response.data
  },

  async getMonthlySpending(config = {}) {
    const response = await axios.get(`${API_BASE_URL}/spending/monthly`, config)
    return response.data
  },

  async getCategorySpending(config = {}) {
    const response = await axios.get(`${API_BASE_URL}/spending/categories`, config)
    return response.data
  },

  async getTransactions(config = {}) {
    const response = await axios.get(`${API_BASE_URL}/spending/transactions`, config)
    return response.data
  },

  async getTasks() {
    const response = await axios.get(`${API_BASE_URL}/tasks`)
    return response.data
  },

  async createTask(taskData) {
    const response = await axios.post(`${API_BASE_URL}/tasks`, taskData)
    return response.data
  },

  async deleteTask(taskId) {
    const response = await axios.delete(`${API_BASE_URL}/tasks/${taskId}`)
    return response.data
  },

  async toggleTask(taskId) {
    const response = await axios.patch(`${API_BASE_URL}/tasks/${taskId}`)
    return response.data
  },

  async createPurchaseOrder(purchaseOrderData) {
    const response = await axios.post(`${API_BASE_URL}/purchase-orders`, purchaseOrderData)
    return response.data
  },

  async getPurchaseOrderByBacklogItem(backlogItemId) {
    const response = await axios.get(`${API_BASE_URL}/purchase-orders/${backlogItemId}`)
    return response.data
  },

  // Budget is always sent in USD, regardless of display currency
  async getRestockRecommendations(budget) {
    const response = await axios.get(`${API_BASE_URL}/restocking/recommendations`, { params: { budget } })
    return response.data
  },

  async submitRestockOrder(items) {
    const response = await axios.post(`${API_BASE_URL}/restocking/orders`, { items })
    return response.data
  },

  async getSubmittedOrders() {
    const response = await axios.get(`${API_BASE_URL}/restocking/orders`)
    return response.data
  },
}
