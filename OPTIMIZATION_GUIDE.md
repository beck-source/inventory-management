# Vue Component Optimization Guide

## Executive Summary

The Vue codebase has **59 optimization opportunities** across 19 components:
- **3 Critical**: v-for key issues breaking reactivity
- **3 Major**: Large setup functions (171-411 lines)
- **53 Minor**: Code duplication and structure improvements

**Estimated impact of all fixes**: 40% reduction in component complexity, +2 composables for reuse.

---

## Critical Issues (Must Fix)

### 1. v-for Index Keys in Reports.vue ❌

**Impact**: Breaks component state during list reordering/filtering
**Files**: `client/src/views/Reports.vue` (3 instances)

#### Issue Details
```vue
<!-- Line 28: Chart data -->
<div v-for="(month, index) in monthlyData" :key="index">

<!-- Line 51: Table rows -->
<tr v-for="(item, index) in items" :key="index">

<!-- Line 82: Forecast entries -->
<tr v-for="(entry, index) in forecasts" :key="index">
```

#### Why This is Bad
- React/Vue rerenders DOM nodes when index changes
- Component state (focus, input) lost during filtering
- Performance degrades with dynamic lists
- Violates Vue best practices

#### Solution
Use stable, unique identifiers:

```vue
<!-- Line 28 -->
<div v-for="month in monthlyData" :key="month.month">

<!-- Line 51 -->
<tr v-for="item in items" :key="item.id">

<!-- Line 82 -->
<tr v-for="entry in forecasts" :key="entry.id">
```

**Effort**: 5 minutes | **Priority**: ASAP

---

## Major Issues (This Sprint)

### 2. Large Component Setup Functions ⚠️

**Impact**: Hard to test, reuse, and maintain
**Components**: Dashboard (411 lines), Spending (303), Restocking (171)

#### Dashboard.vue Refactoring

**Current**: 411-line `setup()` function
```javascript
setup() {
  // Line 1-50: State management
  const loading = ref(true)
  const error = ref(null)
  const summary = ref({})
  // ... 10+ more refs
  
  // Line 50-150: Data fetching
  const loadData = async () => { ... }
  
  // Line 150-300: Computed properties
  const statusData = computed(() => { ... })
  const categoryData = computed(() => { ... })
  const orderTrendData = computed(() => { ... })
  // ... 10+ more computed
  
  // Line 300-400: Helper methods
  const calculatePercentage = () => { ... }
  const getStockBadge = () => { ... }
  const formatDate = () => { ... }
  // ... 20+ more helpers
  
  // Line 400-411: Return 40+ properties
  return {
    loading, error, summary, allOrders, inventoryItems,
    statusData, orderHealthMetrics, categoryData, orderTrendData, topProducts,
    calculatePercentage, getStockBadge, formatDate,
    // ... 30 more exports
  }
}
```

#### Proposed Structure

```javascript
// composables/useDashboardData.js
export function useDashboardData() {
  const { selectedPeriod, selectedLocation, ... } = useFilters()
  const loading = ref(true)
  const error = ref(null)
  const summary = ref({})
  const allOrders = ref([])
  const inventoryItems = ref([])
  
  const loadData = async () => { ... }
  
  return { loading, error, summary, allOrders, inventoryItems, loadData }
}

// composables/useDashboardCharts.js
export function useDashboardCharts(allOrders, inventoryItems) {
  const statusData = computed(() => { ... })
  const categoryData = computed(() => { ... })
  const orderTrendData = computed(() => { ... })
  const topProducts = computed(() => { ... })
  
  return { statusData, categoryData, orderTrendData, topProducts }
}

// composables/useDashboardUI.js
export function useDashboardUI() {
  const showProductModal = ref(false)
  const showBacklogModal = ref(false)
  const showPOModal = ref(false)
  
  const showProductDetail = (product) => { ... }
  const showBacklogDetail = (item) => { ... }
  
  return { showProductModal, showBacklogModal, showPOModal, ... }
}

// Views/Dashboard.vue (refactored)
<script>
export default {
  setup() {
    const { loading, error, summary, allOrders, inventoryItems, loadData } = useDashboardData()
    const { statusData, categoryData, orderTrendData, topProducts } = useDashboardCharts(allOrders, inventoryItems)
    const { showProductModal, selectedProduct, showProductDetail, ... } = useDashboardUI()
    
    onMounted(loadData)
    return {
      loading, error, statusData, categoryData, orderTrendData, topProducts,
      showProductModal, selectedProduct, showProductDetail, ...
    }
  }
}
</script>
```

**Result**: Setup function ~120 lines (70% reduction)

---

## Code Reuse Opportunities (This Quarter)

### 3. Extract useAsync() Composable

**Affected**: Dashboard, Inventory, Orders, Spending, Restocking, Reports
**Pattern**: All views repeat:

```javascript
const loading = ref(true)
const error = ref(null)

const loadData = async () => {
  try {
    loading.value = true
    const data = await api.call()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
```

**Solution**: Create `useAsync()` composable

```javascript
// composables/useAsync.js
export function useAsync(asyncFn, immediate = true) {
  const loading = ref(false)
  const error = ref(null)
  const data = ref(null)
  
  const execute = async () => {
    loading.value = true
    error.value = null
    try {
      data.value = await asyncFn()
    } catch (err) {
      error.value = err.message ?? 'Unknown error'
    } finally {
      loading.value = false
    }
  }
  
  onMounted(() => {
    if (immediate) execute()
  })
  
  return { data, loading, error, execute }
}

// Usage in Dashboard.vue
const { data: summary, loading, error, execute } = useAsync(
  () => api.getDashboardSummary(getCurrentFilters()),
  false // Don't auto-load, we'll trigger on filter change
)

watch([selectedPeriod, selectedLocation], () => execute())
```

**Benefit**: 60+ lines saved per component × 6 components = 360 lines

---

### 4. Consolidate Utility Functions

**Issue**: Duplicated across components
- `formatDate()` - 3 copies
- `translateCategory()` - 5 copies
- `getStockStatus()` - 4 copies
- Percentage calculations - 6 copies

**Solution**: Create utils and use them consistently

```javascript
// utils/formatting.js
export function formatDate(dateString, locale = 'en-US') {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString(locale, { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric' 
  })
}

export function getStockStatus(item) {
  if (item.quantity_on_hand <= item.reorder_point) {
    return 'critical'
  } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
    return 'low'
  }
  return 'adequate'
}

// utils/calculations.js
export function getPercentage(value, total) {
  return total > 0 ? (value / total * 100).toFixed(2) : 0
}

export function getProcurementPercentage(costs) {
  return getPercentage(costs.procurement, costs.total)
}

// Usage
import { formatDate, getStockStatus, getProcurementPercentage } from '@/utils'

const status = getStockStatus(item)
const procurementPct = getProcurementPercentage(costs)
```

**Benefit**: +5 KB saved, +20 copies avoided

---

## Architecture Recommendations

### Proposed Composable Library

| Composable | Purpose | Usage |
|-----------|---------|-------|
| `useAsync()` | Loading/error state | All data-fetching views |
| `useFilters()` | ✓ Exists - expand usage | All filtered views |
| `useI18n()` | ✓ Exists - verify use | All components |
| `useDashboardData()` | Dashboard data fetching | Dashboard.vue |
| `useDashboardCharts()` | Chart computations | Dashboard.vue |
| `useFinancialMetrics()` | Revenue/cost calculations | Spending.vue, Reports.vue |
| `useRestockingState()` | Budget + selection | Restocking.vue |
| `useDateFormat()` | Date/time formatting | All components |

### File Structure

```
client/src/
├── composables/
│   ├── useAsync.js           [NEW]
│   ├── useFilters.js         [EXISTING]
│   ├── useI18n.js            [EXISTING]
│   ├── useDashboardData.js    [NEW]
│   ├── useDashboardCharts.js  [NEW]
│   ├── useFinancialMetrics.js [NEW]
│   └── useRestockingState.js  [NEW]
├── utils/
│   ├── currency.js           [EXISTING]
│   ├── formatting.js         [NEW]
│   ├── calculations.js       [NEW]
│   └── validators.js         [NEW]
└── views/
    ├── Dashboard.vue         [REFACTOR]
    ├── Spending.vue          [REFACTOR]
    └── Restocking.vue        [REFACTOR]
```

---

## Implementation Timeline

### Week 1: Critical Fixes
- [ ] Day 1: Fix v-for keys in Reports.vue (5 min)
- [ ] Day 2-3: Create `useAsync()` composable + tests
- [ ] Day 4: Update 3 views to use `useAsync()` (Dashboard, Inventory, Orders)
- [ ] Day 5: Update remaining 3 views, merge PR

**PR**: "fix: replace loading patterns with useAsync composable"

### Week 2: Dashboard Refactoring
- [ ] Day 1: Extract `useDashboardData()` + tests
- [ ] Day 2: Extract `useDashboardCharts()` + tests
- [ ] Day 3: Extract `useDashboardUI()` + tests
- [ ] Day 4: Refactor Dashboard.vue, verify no regressions
- [ ] Day 5: Code review, merge

**PR**: "refactor: extract Dashboard composables (70% complexity reduction)"

### Week 3: Utility Extraction
- [ ] Day 1-2: Create `utils/formatting.js` + `utils/calculations.js`
- [ ] Day 3-4: Update all components to use utilities
- [ ] Day 5: Remove duplication, merge

**PR**: "refactor: consolidate utility functions"

### Week 4: Polish & Verification
- [ ] Day 1-2: Refactor Spending.vue and Restocking.vue
- [ ] Day 3: Add lazy loading to modal components
- [ ] Day 4: Run analyzer, document remaining issues
- [ ] Day 5: Performance testing, merge

**PR**: "refactor: complete Vue optimization suite"

---

## Verification Checklist

After implementing optimizations:

```bash
# Before
python scripts/analyze_vue.py
# Expected: 59 issues, 3 errors, 3 warnings

# After
python scripts/analyze_vue.py
# Expected: <10 issues, 0 errors, 0 warnings

# Check component sizes
wc -l client/src/views/*.vue
# Expected: all <300 lines

# Check composables
ls -la client/src/composables/
# Expected: 7+ composables

# Test functionality
npm run test
# Expected: 100% pass rate

# Check bundle size
npm run build
# Expected: <5% change (should be similar or smaller)
```

---

## Long-term Maintenance

### Prevent Regression
1. **Pre-commit hook**: Run analyzer on changed .vue files
2. **CI/CD**: Fail builds if error count increases
3. **Code review**: Check for patterns that should be composables
4. **Documentation**: Update component guidelines

### Continuous Improvement
- [ ] Monthly analyzer reports
- [ ] Track metric trends (avg setup size, duplication, etc.)
- [ ] Establish component size limits
- [ ] Composable reuse percentage targets

---

## Additional Resources

- Vue 3 Composition API: https://vuejs.org/guide/extras/composition-api-faq.html
- Composables Best Practices: https://vuejs.org/guide/reusability/composables.html
- Performance Guide: https://vuejs.org/guide/best-practices/performance.html
- Analyzer Report: `scripts/vue-analysis-report.json`

---

**Generated**: June 24, 2026
**Next Review**: June 26, 2026 (after critical fixes)
