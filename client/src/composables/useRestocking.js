import { ref } from 'vue'

// Module-level ref (singleton) - shared across the Restocking and Orders views.
// Restock orders are kept client-side only (the app has no POST /orders endpoint),
// so these reset on a full page refresh, consistent with tasks/purchase orders.
const submittedOrders = ref([])

export function useRestocking() {
  // Add a newly placed restock order to the front of the shared list
  const addSubmittedOrder = (order) => {
    submittedOrders.value.unshift(order)
  }

  return {
    submittedOrders,
    addSubmittedOrder
  }
}
