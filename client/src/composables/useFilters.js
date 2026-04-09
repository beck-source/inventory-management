import { ref, computed } from 'vue'

// Shared filter state (singleton pattern)
const startMonth = ref('')  // YYYY-MM format, empty = no lower bound
const endMonth = ref('')    // YYYY-MM format, empty = no upper bound
const selectedLocation = ref('all')
const selectedCategory = ref('all')
const selectedStatus = ref('all')

export function useFilters() {
  // Check if any filters are active
  const hasActiveFilters = computed(() => {
    return startMonth.value !== '' ||
           endMonth.value !== '' ||
           selectedLocation.value !== 'all' ||
           selectedCategory.value !== 'all' ||
           selectedStatus.value !== 'all'
  })

  // Reset all filters to default
  const resetFilters = () => {
    startMonth.value = ''
    endMonth.value = ''
    selectedLocation.value = 'all'
    selectedCategory.value = 'all'
    selectedStatus.value = 'all'
  }

  // Get current filters as an object for API calls
  const getCurrentFilters = () => {
    const filters = {
      warehouse: selectedLocation.value,
      category: selectedCategory.value,
      status: selectedStatus.value
    }
    if (startMonth.value) filters.start_month = startMonth.value
    if (endMonth.value) filters.end_month = endMonth.value
    return filters
  }

  return {
    // State
    startMonth,
    endMonth,
    selectedLocation,
    selectedCategory,
    selectedStatus,

    // Computed
    hasActiveFilters,

    // Methods
    resetFilters,
    getCurrentFilters
  }
}
