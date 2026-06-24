# Vue Component Analyzer - Quick Reference

## 🚀 One-Command Analysis

```bash
python scripts/analyze_vue.py
```

**Generates**:
- 📊 Console report (summary + findings)
- 📄 JSON report (`scripts/vue-analysis-report.json`)
- ⏱️ Execution time: <1 second

## 📊 What You Get

| Finding | Count | Severity | Action |
|---------|-------|----------|--------|
| v-for index keys | 3 | 🔴 ERROR | Fix immediately |
| Large components | 3 | 🟡 WARNING | Refactor this sprint |
| Duplicated methods | 50 | 🔵 INFO | Extract to composables |
| Complex expressions | 2 | 🔵 INFO | Move to computed |

## 🎯 Critical Issues to Fix Now

### Reports.vue - v-for :key="index" (3 errors)
```vue
<!-- BEFORE: Breaks reactivity -->
<tr v-for="item in items" :key="index">

<!-- AFTER: Stable key -->
<tr v-for="item in items" :key="item.id">
```

Locations: Lines 28, 51, 82
Time to fix: 5 minutes
Severity: High (breaks component state during filtering)

## 🔧 Top Refactorings (Next Sprint)

### 1. Dashboard.vue (411 → 120 lines)
Extract 3 composables:
- `useDashboardData()` - API calls
- `useDashboardCharts()` - Computed properties
- `useDashboardUI()` - Modal state

### 2. Spending.vue (303 → 100 lines)
Extract 2 composables:
- `useFinancialMetrics()` - Revenue calculations
- `useMonthlyData()` - Monthly aggregations

### 3. Restocking.vue (171 → 80 lines)
Extract 2 composables:
- `useRestockingState()` - Budget & selection
- `useRecommendations()` - Filtering/sorting

## 💡 Quick Wins (This Quarter)

### Extract formatDate() utility
```javascript
// Before: Duplicated in 5 components
const formatDate = (date) => new Date(date).toLocaleDateString()

// After: Import from utils
import { formatDate } from '@/utils/date'
```
Saves: 20+ lines

### Extract useAsync() composable
```javascript
// Before: 60-80 lines per view with loading/error/try-catch
// After: 5-line reusable hook
const { data, loading, error } = useAsync(apiCall)
```
Saves: 360+ lines across 6 components

### Add lazy loading to modals
```javascript
// Before: 11 component imports in Dashboard
// After: Load on demand
const ProductDetailModal = defineAsyncComponent(
  () => import('../components/ProductDetailModal.vue')
)
```
Savings: ~20KB bundle reduction

## 📈 Track Your Progress

```bash
# Week 1: Fix critical issues
python scripts/analyze_vue.py | grep "ERROR"
# Expected: 3 errors → 0 errors

# Week 2: First refactoring
python scripts/analyze_vue.py | grep "SUMMARY"
# Expected: 59 issues → 40 issues

# Week 4: Verify completion
python scripts/analyze_vue.py
# Expected: <10 issues total, 0 errors
```

## 📚 Documentation

| File | Purpose |
|------|---------|
| `OPTIMIZATION_GUIDE.md` | Detailed 4-week roadmap |
| `scripts/README_ANALYZER.md` | Technical reference |
| `scripts/quick_fix.py` | Interactive recommendations |
| `scripts/USAGE.sh` | Workflow examples |
| `SKILL_SUMMARY.md` | Complete overview |

## 🤖 Integrate with CI/CD

```yaml
# .gitlab-ci.yml
test:vue:
  script:
    - python scripts/analyze_vue.py
  allow_failure: false  # Fail on errors
```

## 📊 Current State (Baseline)

```
Components: 19
  • 1 root (App.vue)
  • 11 reusable (components/)
  • 7 pages (views/)

Issues: 59 total
  • 3 errors (critical)
  • 3 warnings (major)
  • 53 info (improvements)

Metrics:
  • Avg 232 lines/component
  • 411-line max setup
  • 50 duplicated methods
  • 8/19 use watchers
```

## 🎯 Target State (After All Fixes)

```
Components: 19 (same)
  • Better organized
  • Smaller setups

Issues: <10 total
  • 0 errors (critical)
  • 0 warnings (major)
  • <10 info (nice-to-haves)

Metrics:
  • Avg 140 lines/component (40% reduction)
  • 120-line max setup (71% reduction)
  • <5 duplicated methods (90% reduction)
  • 3/19 use watchers (65% reduction)
  • 10 composables for reuse
```

## 🚨 Most Important First

1. **TODAY**: Fix v-for keys in Reports.vue (5 min)
2. **THIS WEEK**: Create useAsync() composable (2 hours)
3. **NEXT WEEK**: Extract Dashboard composables (2 days)
4. **MONTH 2**: Refactor remaining components (3 days)

## 🆘 Need Help?

Check these in order:
1. `OPTIMIZATION_GUIDE.md` - Strategic guidance
2. `scripts/README_ANALYZER.md` - Technical details
3. `scripts/quick_fix.py` - Code snippets
4. JSON report - Raw data with line numbers

## ⚡ Pro Tips

1. Use `grep` to filter findings:
   ```bash
   python scripts/analyze_vue.py | grep "Dashboard"
   ```

2. Check JSON for specific issues:
   ```bash
   cat scripts/vue-analysis-report.json | jq '.issues[0:3]'
   ```

3. Compare improvements weekly:
   ```bash
   python scripts/analyze_vue.py > report_$(date +%u).txt
   diff report_1.txt report_7.txt
   ```

4. Focus on one category at a time:
   - Week 1: Fix all PERFORMANCEs
   - Week 2: Fix all STRUCTUREs
   - Week 3+: Fix all REUSEs

---

**Need detailed recommendations?** → Read `OPTIMIZATION_GUIDE.md`
**Need technical reference?** → Check `scripts/README_ANALYZER.md`
**Need to get started immediately?** → Run `python scripts/quick_fix.py`

---

*Generated: June 24, 2026 | Skill: Vue Component Structure Analyzer v1.0*
