import axios from 'axios'

const API_BASE_URL = 'http://localhost:8001/api'

export const api = {
  async getInventory(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)

    const response = await axios.get(`${API_BASE_URL}/inventory?${params.toString()}`)
    return response.data
  },

  async getInventoryItem(id) {
    const response = await axios.get(`${API_BASE_URL}/inventory/${id}`)
    return response.data
  },

  async getOrders(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await axios.get(`${API_BASE_URL}/orders?${params.toString()}`)
    return response.data
  },

  async getOrder(id) {
    const response = await axios.get(`${API_BASE_URL}/orders/${id}`)
    return response.data
  },

  async getDemandForecasts() {
    const response = await axios.get(`${API_BASE_URL}/demand`)
    return response.data
  },

  async getBacklog() {
    const response = await axios.get(`${API_BASE_URL}/backlog`)
    return response.data
  },

  async getDashboardSummary(filters = {}) {
    const params = new URLSearchParams()
    if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
    if (filters.category && filters.category !== 'all') params.append('category', filters.category)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.month && filters.month !== 'all') params.append('month', filters.month)

    const response = await axios.get(`${API_BASE_URL}/dashboard/summary?${params.toString()}`)
    return response.data
  },

  async getSpendingSummary() {
    const response = await axios.get(`${API_BASE_URL}/spending/summary`)
    return response.data
  },

  async getMonthlySpending() {
    const response = await axios.get(`${API_BASE_URL}/spending/monthly`)
    return response.data
  },

  async getCategorySpending() {
    const response = await axios.get(`${API_BASE_URL}/spending/categories`)
    return response.data
  },

  async getTransactions() {
    const response = await axios.get(`${API_BASE_URL}/spending/transactions`)
    return response.data
  },

  getTasks() {
    const stored = localStorage.getItem('tasks')
    return stored ? JSON.parse(stored) : []
  },

  createTask(taskData) {
    const tasks = this.getTasks()
    const newTask = { ...taskData, id: Date.now() }
    tasks.unshift(newTask)
    localStorage.setItem('tasks', JSON.stringify(tasks))
    return newTask
  },

  deleteTask(taskId) {
    const tasks = this.getTasks().filter(t => t.id !== taskId)
    localStorage.setItem('tasks', JSON.stringify(tasks))
  },

  toggleTask(taskId) {
    const tasks = this.getTasks()
    const task = tasks.find(t => t.id === taskId)
    if (task) {
      task.status = task.status === 'pending' ? 'completed' : 'pending'
      localStorage.setItem('tasks', JSON.stringify(tasks))
    }
    return task
  },

  async createPurchaseOrder(purchaseOrderData) {
    const response = await axios.post(`${API_BASE_URL}/purchase-orders`, purchaseOrderData)
    return response.data
  },

  async getPurchaseOrderByBacklogItem(backlogItemId) {
    const response = await axios.get(`${API_BASE_URL}/purchase-orders/${backlogItemId}`)
    return response.data
  },

  async createRestockingOrder(payload) {
    const response = await axios.post(`${API_BASE_URL}/restocking-orders`, payload)
    return response.data
  }
}
