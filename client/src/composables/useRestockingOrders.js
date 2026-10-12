import { ref } from 'vue'

// Module singleton — persists across navigation
const submittedOrders = ref([])
let orderCounter = 1

const LEAD_TIME_DAYS = { increasing: 3, stable: 7, decreasing: 14 }

function addDays(date, days) {
  const result = new Date(date)
  result.setDate(result.getDate() + days)
  return result.toISOString().split('T')[0]
}

export function useRestockingOrders() {
  const submitOrder = (recommendedItems, budgetUsed) => {
    const today = new Date().toISOString().split('T')[0]
    const maxLeadTime = recommendedItems.reduce((max, item) => {
      return Math.max(max, LEAD_TIME_DAYS[item.trend] ?? 7)
    }, 0)

    const order = {
      id: `rst-${Date.now()}`,
      order_number: `RST-2025-${String(orderCounter++).padStart(4, '0')}`,
      submitted_at: today,
      expected_delivery: addDays(today, maxLeadTime),
      lead_time_days: maxLeadTime,
      items: recommendedItems.map(item => ({
        sku: item.item_sku,
        name: item.item_name,
        quantity: item.restock_qty,
        unit_cost: item.unit_cost,
        trend: item.trend,
        lead_time_days: LEAD_TIME_DAYS[item.trend] ?? 7
      })),
      total_cost: recommendedItems.reduce(
        (sum, item) => sum + item.restock_qty * item.unit_cost, 0
      ),
      budget_used: budgetUsed,
      status: 'Submitted'
    }

    submittedOrders.value.unshift(order)
    return order
  }

  return { submittedOrders, submitOrder }
}
