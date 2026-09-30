// Restocking composable - manages restocking recommendations and orders
// Orders are persisted to localStorage since there is no backend endpoint for them yet.

const STORAGE_KEY = 'restocking-orders'

const readOrders = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch (err) {
    console.error('Failed to read restocking orders from localStorage:', err)
    return []
  }
}

const writeOrders = (orders) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(orders))
  } catch (err) {
    console.error('Failed to save restocking orders to localStorage:', err)
  }
}

const generateOrderId = () => {
  const timestamp = Date.now()
  const randomId = Math.random().toString(36).slice(2, 8)
  return `RESTOCK-${timestamp}-${randomId}`
}

export function useRestocking() {
  // Read all restocking orders, newest first
  const getRestockingOrders = () => {
    return readOrders().sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
  }

  // Lead time: 3 day base + 1 day per 5 items ordered, rounded up
  const calculateLeadTime = (itemCount) => {
    const count = Number(itemCount) || 0
    if (count <= 0) return 3
    return 3 + Math.ceil(count / 5)
  }

  // Save a new restocking order to localStorage. Starts as unsaved (synced: false).
  // order = { items: [{ sku, name, quantity, unitCost, cost }], totalCost, budget }
  const addRestockingOrder = (order) => {
    const orders = readOrders()

    const itemCount = order.items.reduce((sum, item) => sum + item.quantity, 0)
    const leadTimeDays = calculateLeadTime(itemCount)
    const createdAt = new Date().toISOString()
    const estimatedDelivery = new Date(Date.now() + leadTimeDays * 24 * 60 * 60 * 1000).toISOString()

    const newOrder = {
      id: generateOrderId(),
      items: order.items,
      itemCount,
      totalCost: order.totalCost,
      budget: order.budget,
      leadTimeDays,
      createdAt,
      estimatedDelivery,
      synced: false
    }

    orders.push(newOrder)
    writeOrders(orders)
    return newOrder
  }

  // Mark an existing order as synced (saved) in localStorage
  const markOrderAsSaved = (orderId) => {
    const orders = readOrders()
    const index = orders.findIndex(o => o.id === orderId)
    if (index === -1) return null

    orders[index] = { ...orders[index], synced: true }
    writeOrders(orders)
    return orders[index]
  }

  // Normalize a product name for matching (case/whitespace-insensitive)
  const normalizeName = (name) => (name || '').trim().toLowerCase()

  // Build recommendations from demand forecasts + inventory, capped by budget.
  // Highest forecasted demand is prioritized first.
  //
  // NOTE: The demand API's `item_sku` values (e.g. "WDG-001") do not correspond to
  // the inventory API's `sku` values (e.g. "PCB-001") - the two mock datasets use
  // unrelated SKU numbering. Both datasets do share a human-readable product name
  // (`item_name` on demand forecasts, `name` on inventory items), so we correlate
  // records by normalized name instead of SKU.
  const recommendItems = (budget, demandForecasts = [], inventoryItems = []) => {
    const inventoryByName = new Map(
      inventoryItems.map(item => [normalizeName(item.name), item])
    )

    const candidates = demandForecasts
      .map(forecast => {
        const inventoryItem = inventoryByName.get(normalizeName(forecast.item_name))
        if (!inventoryItem) return null

        // Suggested quantity covers the gap between forecasted demand and current stock
        const suggestedQuantity = Math.max(forecast.forecasted_demand - inventoryItem.quantity_on_hand, 0)

        return {
          sku: inventoryItem.sku,
          name: inventoryItem.name,
          category: inventoryItem.category,
          currentStock: inventoryItem.quantity_on_hand,
          demandForecast: forecast.forecasted_demand,
          unitCost: inventoryItem.unit_cost,
          suggestedQuantity
        }
      })
      .filter(item => item && item.suggestedQuantity > 0)
      .sort((a, b) => b.demandForecast - a.demandForecast)

    // Allocate remaining budget across candidates, highest demand first
    let remainingBudget = Number(budget) || 0
    const recommendations = []

    for (const candidate of candidates) {
      if (remainingBudget <= 0) break
      if (candidate.unitCost <= 0) continue

      const maxAffordable = Math.floor(remainingBudget / candidate.unitCost)
      if (maxAffordable <= 0) continue

      const quantity = Math.min(candidate.suggestedQuantity, maxAffordable)
      if (quantity <= 0) continue

      const cost = quantity * candidate.unitCost
      remainingBudget -= cost

      recommendations.push({ ...candidate, quantity, cost })
    }

    return recommendations
  }

  return {
    getRestockingOrders,
    addRestockingOrder,
    calculateLeadTime,
    recommendItems,
    markOrderAsSaved
  }
}
