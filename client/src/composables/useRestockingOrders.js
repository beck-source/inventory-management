import { ref } from 'vue'

// Singleton in-memory store shared between Restocking and Orders views
const submittedOrders = ref([])

export function useRestockingOrders() {
  const submitOrder = (order) => {
    submittedOrders.value.unshift(order)
  }

  return {
    submittedOrders,
    submitOrder
  }
}
