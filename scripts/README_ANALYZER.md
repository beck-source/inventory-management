# Vue Component Structure Analyzer & Optimizer

A comprehensive skill that analyzes Vue 3 Single File Components (SFC) for performance bottlenecks, code duplication, and structural improvements.

## Features

### Performance Analysis
- **v-for Key Issues**: Detects missing `:key` bindings and index-based keys (which break reactivity)
- **v-if + v-for Nesting**: Flags inefficient conditional rendering within loops
- **Complex Expressions**: Identifies overly complex template interpolations that should be computed properties
- **Watcher Patterns**: Detects redundant `watch` + `immediate` combined with `onMounted`

### Code Reuse Detection
- **Duplicated Methods**: Finds utility methods (translate*, format*, get*) repeated across components
- **Shared State Patterns**: Identifies multiple related refs that should be extracted into composables
- **Async Loading Pattern**: Detects repeated loading/error/try-catch blocks suitable for extraction

### Structural Analysis
- **Large Setup Functions**: Flags components with >150 line setup() functions
- **Return Object Size**: Identifies components exposing excessive internal state (>20 properties)
- **Component Imports**: Warns about too many component imports (>5) and suggests lazy loading
- **Cross-File Patterns**: Analyzes the entire codebase for duplicated methods across files

## Usage

### Basic Analysis
```bash
python scripts/analyze_vue.py
```

This scans all `.vue` files in `client/src/` and generates:
- **Console Report**: Readable summary with severity levels (ERROR/WARNING/INFO)
- **JSON Report**: Detailed `scripts/vue-analysis-report.json` for programmatic use

### Severity Levels

| Level | Count | Impact |
|-------|-------|--------|
| ❌ ERROR (3) | Critical issues breaking reactivity or performance | Exit code 1 |
| ⚠️ WARNING (3) | Significant refactoring opportunities | Continues analysis |
| ℹ️ INFO (53) | Nice-to-have optimizations | Informational only |

## Sample Findings

### Critical: Index-Based v-for Keys
```vue
<!-- ❌ BAD - breaks component state during filtering/reordering -->
<tr v-for="item in items" :key="index">

<!-- ✅ GOOD - stable identifier -->
<tr v-for="item in items" :key="item.id">
```

**Finding**: 3 instances in `Reports.vue`

### Large Components
**Dashboard.vue**: 411 lines in setup()
- **Suggestion**: Extract into composables
  - `useFilters()` - already exists, expand usage
  - `useDashboardData()` - API calls, data fetching
  - `useChartData()` - computed properties for charts
  - `useDashboardUI()` - modal states, user interactions

**Spending.vue**: 303 lines
- **Suggestion**: Extract `useFinancialMetrics()` composable

**Restocking.vue**: 171 lines
- **Suggestion**: Extract `useRestockingState()` composable

### Duplicated Utility Methods
50 utilities flagged across components:
- `formatDate()` - duplicated, move to `utils/date.js`
- `translate*()` - already in `useI18n()`, check imports
- `get*()` helpers - extract to relevant composables

## Optimization Strategy

### Phase 1: Fix Critical Issues (HIGH PRIORITY)
1. Fix v-for keys in `Reports.vue` (3 errors)
2. Extract `useAsync()` composable for loading patterns
3. Move duplicated `formatDate()` to utils

### Phase 2: Refactor Large Components (MEDIUM PRIORITY)
1. Dashboard.vue: Extract `useChartData()` composable
2. Spending.vue: Extract `useFinancialMetrics()` composable
3. Restocking.vue: Extract `useRestockingState()` composable

### Phase 3: Enhance Code Reuse (ONGOING)
1. Audit all translate* functions - use `useI18n()`
2. Create `useDateFormat()` composable
3. Extract percentage calculation helpers

## Architecture Improvements

### Proposed Composables

#### `useAsync()`
Consolidate loading/error pattern across all views:
```javascript
const { data, loading, error, execute } = useAsync(apiCall)
```

#### `useDashboardData()`
Encapsulate Dashboard data fetching:
```javascript
const { summary, orders, inventory, backlog } = useDashboardData(filters)
```

#### `useChartData()`
Extract chart computations:
```javascript
const { orderTrendData, categoryData, topProducts } = useChartData(orders)
```

#### `useFinancialMetrics()`
Consolidate spending calculations:
```javascript
const { totalRevenue, totalCosts, netProfit } = useFinancialMetrics(spending)
```

## Report Structure

```json
{
  "summary": {
    "total_issues": 59,
    "errors": 3,
    "warnings": 3,
    "info": 53,
    "components_analyzed": 19
  },
  "issues": [
    {
      "severity": "error",
      "category": "performance",
      "file": "path/to/component.vue",
      "line": 28,
      "message": "Using array index as v-for key",
      "suggestion": "Replace with unique identifier...",
      "code": ":key=\"index\""
    }
  ],
  "metrics": [
    {
      "file": "path/to/component.vue",
      "lines": 442,
      "methods_count": 12,
      "computed_count": 8,
      "hooks_count": 3,
      "imports_count": 5,
      "has_watch": true,
      "has_on_mounted": true,
      "data_refs": 6,
      "unique_issues": 2
    }
  ]
}
```

## Component Health Metrics

**Current State**:
- Avg 232 lines per component
- Avg 4 methods per component
- 8/19 components use watchers
- 19/19 analyzed successfully

**Target State**:
- <200 lines per component (or <100 in setup())
- <5 methods per component
- <3 watchers per component
- <5 component imports per view

## Files

- `scripts/analyze_vue.py` - Main analyzer script (1000+ lines)
- `scripts/vue-analysis-report.json` - Generated JSON report
- `scripts/README_ANALYZER.md` - This file

## Integration

### CI/CD Pipeline
```bash
# Fail on errors, warn on warnings
python scripts/analyze_vue.py
if [ $? -eq 1 ]; then
  echo "Fix critical performance issues before merging"
  exit 1
fi
```

### Pre-Commit Hook
```bash
#!/bin/bash
python scripts/analyze_vue.py --changed-files-only
```

## Next Steps

1. **Run the analyzer**: `python scripts/analyze_vue.py`
2. **Review findings**: Check `scripts/vue-analysis-report.json`
3. **Fix errors first**: v-for keys in Reports.vue
4. **Refactor systematically**: Extract composables for large components
5. **Re-run analyzer**: Track improvement over time

## Future Enhancements

- [ ] Watch integration with `watchEffect()` over `watch()` with immediate
- [ ] Detect unused imports and exports
- [ ] Props validation (missing type definitions)
- [ ] Emits documentation
- [ ] Lifecycle hook optimization
- [ ] Template syntax modernization
- [ ] Component composition suggestions
- [ ] Custom rule plugins
