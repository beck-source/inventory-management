import axios from 'axios'

const API_BASE_URL = 'http://localhost:8001/api'

export const api = {
  async getInventory(filters = {}, { signal } = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)

    const response = await axios.get(`${API_BASE_URL}/inventory?${params.toString()}`, { signal })
    return response.data
  },

  async getInventoryItem(id) {
    const response = await axios.get(`${API_BASE_URL}/inventory/${id}`)
    return response.data
  },

  async getOrders(filters = {}, { signal } = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await axios.get(`${API_BASE_URL}/orders?${params.toString()}`, { signal })
    return response.data
  },

  async getOrder(id) {
    const response = await axios.get(`${API_BASE_URL}/orders/${id}`)
    return response.data
  },

  async getDemandForecasts({ signal } = {}) {
    const response = await axios.get(`${API_BASE_URL}/demand`, { signal })
    return response.data
  },

  async getBacklog({ signal } = {}) {
    const response = await axios.get(`${API_BASE_URL}/backlog`, { signal })
    return response.data
  },

  async getDashboardSummary(filters = {}, { signal } = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await axios.get(`${API_BASE_URL}/dashboard/summary?${params.toString()}`, { signal })
    return response.data
  },

  async getSpendingSummary({ signal } = {}) {
    const response = await axios.get(`${API_BASE_URL}/spending/summary`, { signal })
    return response.data
  },

  async getMonthlySpending({ signal } = {}) {
    const response = await axios.get(`${API_BASE_URL}/spending/monthly`, { signal })
    return response.data
  },

  async getCategorySpending({ signal } = {}) {
    const response = await axios.get(`${API_BASE_URL}/spending/categories`, { signal })
    return response.data
  },

  async getTransactions({ signal } = {}) {
    const response = await axios.get(`${API_BASE_URL}/spending/transactions`, { signal })
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

  async getQuarterlyReports(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    const response = await axios.get(`${API_BASE_URL}/reports/quarterly?${params.toString()}`)
    return response.data
  },

  async getMonthlyTrends(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    const response = await axios.get(`${API_BASE_URL}/reports/monthly-trends?${params.toString()}`)
    return response.data
  }
}
