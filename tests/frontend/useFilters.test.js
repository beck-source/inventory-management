// Tests for client/src/composables/useFilters.js
//
// useFilters is a module-level singleton: all four filter refs live outside
// the exported function so they persist across test cases. Every test calls
// resetFilters() in beforeEach to start from a known clean state.

import { useFilters } from '../../client/src/composables/useFilters.js'

describe('useFilters', () => {
  let selectedPeriod, selectedLocation, selectedCategory, selectedStatus
  let hasActiveFilters, resetFilters, getCurrentFilters

  beforeEach(() => {
    ;({ selectedPeriod, selectedLocation, selectedCategory, selectedStatus,
        hasActiveFilters, resetFilters, getCurrentFilters } = useFilters())
    // Ensure we start from a pristine state regardless of prior test mutations.
    resetFilters()
  })

  // --- Default state ---

  it('initialises all four filters to "all"', () => {
    expect(selectedPeriod.value).toBe('all')
    expect(selectedLocation.value).toBe('all')
    expect(selectedCategory.value).toBe('all')
    expect(selectedStatus.value).toBe('all')
  })

  // --- hasActiveFilters ---

  it('reports no active filters when all are "all"', () => {
    expect(hasActiveFilters.value).toBe(false)
  })

  it('reports active filters when selectedPeriod differs from "all"', () => {
    selectedPeriod.value = '2024-01'
    expect(hasActiveFilters.value).toBe(true)
  })

  it('reports active filters when selectedLocation differs from "all"', () => {
    selectedLocation.value = 'San Francisco'
    expect(hasActiveFilters.value).toBe(true)
  })

  it('reports active filters when selectedCategory differs from "all"', () => {
    selectedCategory.value = 'Sensors'
    expect(hasActiveFilters.value).toBe(true)
  })

  it('reports active filters when selectedStatus differs from "all"', () => {
    selectedStatus.value = 'delivered'
    expect(hasActiveFilters.value).toBe(true)
  })

  it('reports active filters when multiple filters are set simultaneously', () => {
    selectedLocation.value = 'London'
    selectedCategory.value = 'Circuit Boards'
    expect(hasActiveFilters.value).toBe(true)
  })

  // --- resetFilters ---

  it('resetFilters returns every filter to "all"', () => {
    selectedPeriod.value = '2024-06'
    selectedLocation.value = 'Tokyo'
    selectedCategory.value = 'Controllers'
    selectedStatus.value = 'shipped'

    resetFilters()

    expect(selectedPeriod.value).toBe('all')
    expect(selectedLocation.value).toBe('all')
    expect(selectedCategory.value).toBe('all')
    expect(selectedStatus.value).toBe('all')
  })

  it('resetFilters causes hasActiveFilters to become false', () => {
    selectedLocation.value = 'London'
    expect(hasActiveFilters.value).toBe(true)

    resetFilters()

    expect(hasActiveFilters.value).toBe(false)
  })

  // --- getCurrentFilters ---

  it('getCurrentFilters shape includes warehouse, category, and status keys', () => {
    const filters = getCurrentFilters()
    expect(filters).toHaveProperty('warehouse')
    expect(filters).toHaveProperty('category')
    expect(filters).toHaveProperty('status')
  })

  it('getCurrentFilters maps selectedLocation to the warehouse key', () => {
    selectedLocation.value = 'San Francisco'
    const filters = getCurrentFilters()
    expect(filters.warehouse).toBe('San Francisco')
  })

  it('getCurrentFilters maps selectedCategory to the category key', () => {
    selectedCategory.value = 'Actuators'
    const filters = getCurrentFilters()
    expect(filters.category).toBe('Actuators')
  })

  it('getCurrentFilters maps selectedStatus to the status key', () => {
    selectedStatus.value = 'processing'
    const filters = getCurrentFilters()
    expect(filters.status).toBe('processing')
  })

  it('getCurrentFilters omits month key when period is "all"', () => {
    const filters = getCurrentFilters()
    expect(filters).not.toHaveProperty('month')
  })

  it('getCurrentFilters includes month key when period is set', () => {
    selectedPeriod.value = '2024-03'
    const filters = getCurrentFilters()
    expect(filters.month).toBe('2024-03')
  })

  it('getCurrentFilters returns "all" for each dimension when no filters are active', () => {
    const filters = getCurrentFilters()
    expect(filters.warehouse).toBe('all')
    expect(filters.category).toBe('all')
    expect(filters.status).toBe('all')
  })
})
