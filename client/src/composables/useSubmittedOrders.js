import { ref } from 'vue'

// Shared, module-level state (singleton) so restocking orders submitted on the
// Restocking tab are visible in the Orders tab without a backend round-trip.
// Note: this is frontend-only state and is cleared on a full page reload.
const submittedOrders = ref([])

let sequence = 1

export function useSubmittedOrders() {
  // items: [{ sku, name, quantity, unit_cost, lead_time_days }]
  const addSubmittedOrder = ({ budget, items }) => {
    const now = new Date()
    // Order-level lead time is the slowest item, since the order ships complete.
    const leadTimeDays = items.reduce((max, i) => Math.max(max, i.lead_time_days), 0)
    const expectedDelivery = new Date(now.getTime() + leadTimeDays * 24 * 60 * 60 * 1000)
    const totalValue = items.reduce((sum, i) => sum + i.quantity * i.unit_cost, 0)

    const order = {
      id: `restock-${sequence}`,
      order_number: `RO-${String(sequence).padStart(4, '0')}`,
      budget,
      items: items.map(i => ({
        sku: i.sku,
        name: i.name,
        quantity: i.quantity,
        unit_price: i.unit_cost,
        lead_time_days: i.lead_time_days
      })),
      status: 'Submitted',
      order_date: now.toISOString().slice(0, 10),
      expected_delivery: expectedDelivery.toISOString().slice(0, 10),
      lead_time_days: leadTimeDays,
      total_value: Math.round(totalValue * 100) / 100
    }
    sequence += 1
    submittedOrders.value = [order, ...submittedOrders.value]
    return order
  }

  return {
    submittedOrders,
    addSubmittedOrder
  }
}
