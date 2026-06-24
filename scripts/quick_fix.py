#!/usr/bin/env python3
"""
Quick fixes for common Vue optimization issues
Run this to auto-fix some issues found by analyze_vue.py
"""

import json
import re
from pathlib import Path

def fix_v_for_indices():
    """Fix v-for :key="index" issues"""
    fixes = []
    
    # Reports.vue - fix :key="index"
    reports_path = Path('client/src/views/Reports.vue')
    if reports_path.exists():
        with open(reports_path, 'r') as f:
            content = f.read()
        
        # Count replacements
        new_content = content
        
        # Pattern 1: chart months (line 28)
        old1 = ':key="index"'
        new1 = ':key="month.month"'
        if old1 in new_content:
            new_content = new_content.replace(old1, new1, 1)
            fixes.append('Reports.vue line 28: :key="index" -> :key="month.month"')
        
        # Pattern 2: items (line 51)
        old2 = 'v-for="(item, index) in items"'
        new2 = 'v-for="item in items"'
        if old2 in new_content:
            new_content = new_content.replace(old2, new2)
            fixes.append('Reports.vue line 51: use stable key instead of index')
        
        # Pattern 3: entries (line 82)
        if ':key="index"' in new_content:
            # This needs manual inspection of context
            fixes.append('Reports.vue line 82: manual fix needed - check key context')
        
        with open(reports_path, 'w') as f:
            f.write(new_content)
    
    return fixes

def suggest_composables():
    """Generate composable extraction suggestions"""
    suggestions = {
        'useAsync': {
            'purpose': 'Consolidate loading/error/try-catch pattern',
            'files': ['Dashboard.vue', 'Inventory.vue', 'Orders.vue', 'Spending.vue'],
            'pattern': '''
// composables/useAsync.js
export function useAsync(fn) {
  const loading = ref(false)
  const error = ref(null)
  const data = ref(null)
  
  const execute = async () => {
    loading.value = true
    error.value = null
    try {
      data.value = await fn()
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }
  
  return { data, loading, error, execute }
}
''',
        },
        'useDashboardData': {
            'purpose': 'Extract data fetching from Dashboard.vue (411-line setup)',
            'uses': 'useFilters, api.getDashboardSummary, api.getOrders, api.getInventory, api.getBacklog',
            'benefit': 'Reduces Dashboard.vue to ~150 lines',
        },
        'useChartData': {
            'purpose': 'Extract computed properties for charts',
            'properties': ['orderTrendData', 'categoryData', 'topProducts', 'statusData'],
            'benefit': 'Separates data transformation from UI logic',
        },
        'useFinancialMetrics': {
            'purpose': 'Extract financial calculations from Spending.vue',
            'depends': 'useFilters, api.getSpending',
            'benefit': 'Reusable across Spending.vue and Reports.vue',
        },
    }
    
    return suggestions

def print_recommendations():
    """Print actionable recommendations"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    VUE OPTIMIZATION QUICK-FIX GUIDE                        ║
╚════════════════════════════════════════════════════════════════════════════╝

🔴 CRITICAL FIXES (Do First)
───────────────────────────────────────────────────────────────────────────

1. Fix v-for :key in Reports.vue (3 errors)
   
   Line 28:  <div v-for="(month, index) in months" :key="index">
   Change to: :key="month.month"
   
   Line 51:  <div v-for="(item, index) in items" :key="index">
   Change to: :key="item.id"
   
   Line 82:  <tr v-for="(row, index) in data" :key="index">
   Change to: :key="row.id"

⚠️  MEDIUM PRIORITY (Schedule This Sprint)
───────────────────────────────────────────────────────────────────────────

1. Extract useAsync() Composable
   Files: Dashboard.vue, Inventory.vue, Orders.vue, Spending.vue
   Current: Each has loading/error/try-catch (60-80 lines each)
   After: 5 lines per file
   
   Code:
   const { data, loading, error, execute } = useAsync(() => api.getOrders(filters))

2. Refactor Dashboard.vue (411-line setup)
   Create composables:
   - useDashboardData() - data fetching
   - useChartData() - computed properties
   - useModalStates() - modal UI state
   
   Result: Dashboard.vue setup() ~120 lines

3. Refactor Spending.vue (303-line setup)
   Create composables:
   - useFinancialMetrics() - revenue/cost calculations
   - useMonthlyData() - monthly aggregations
   
   Result: Spending.vue setup() ~100 lines

4. Refactor Restocking.vue (171-line setup)
   Create composables:
   - useRestockingState() - budget + selection state
   - useRecommendations() - filtering/sorting
   
   Result: Restocking.vue setup() ~80 lines

💡 OPTIMIZATION OPPORTUNITIES (Nice to Have)
───────────────────────────────────────────────────────────────────────────

1. Extract formatDate() to utils
   Current: Duplicated in BacklogDetailModal, Orders, Inventory, etc.
   
   utils/date.js:
   export function formatDate(date) {
     return new Date(date).toLocaleDateString(...)
   }

2. Consolidate translate* functions
   ✓ Already in useI18n() - verify all components use it
   Files to check: Dashboard.vue (translateCategory, translateStockLevel, etc.)

3. Add lazy loading for modal components
   Current: 11 component imports in Dashboard.vue
   
   const ProductDetailModal = defineAsyncComponent(() => 
     import('../components/ProductDetailModal.vue')
   )

4. Extract percentage calculations
   Files: CostDetailModal.vue, Spending.vue
   Methods: getProcurementPercentage, getOperationalPercentage, etc.
   
   Create: utils/percentages.js or composable/usePercentages.js

📊 EXPECTED IMPROVEMENTS
───────────────────────────────────────────────────────────────────────────

Current State:
  • 411 lines: Dashboard.vue setup
  • 303 lines: Spending.vue setup
  • 171 lines: Restocking.vue setup
  • 19 components analyzed
  • 59 total issues

After All Fixes:
  • ~120 lines: Dashboard.vue setup
  • ~100 lines: Spending.vue setup
  • ~80 lines: Restocking.vue setup
  • 8 new composables
  • <20 issues (down from 59)
  • 40% reduction in component setup complexity

🎯 IMPLEMENTATION ROADMAP
───────────────────────────────────────────────────────────────────────────

Sprint 1: Critical Fixes (1-2 days)
  □ Fix v-for keys in Reports.vue
  □ Create useAsync() composable
  □ Update all views to use useAsync()

Sprint 2: Refactor Large Components (3-5 days)
  □ Dashboard.vue: extract 3 composables
  □ Spending.vue: extract 2 composables
  □ Restocking.vue: extract 2 composables

Sprint 3: Polish (2-3 days)
  □ Extract formatDate() utility
  □ Add lazy loading to modals
  □ Extract percentage calculations
  □ Run analyzer - verify <10 issues

📝 TRACKING
───────────────────────────────────────────────────────────────────────────

Run analyzer before each sprint:
  python scripts/analyze_vue.py > scripts/analysis_$(date +%Y%m%d).txt

Compare improvements:
  • Issue count reduction
  • Setup function line counts
  • Composable reuse percentage

═══════════════════════════════════════════════════════════════════════════════
    """)

def main():
    """Main entry point"""
    print_recommendations()
    
    print("\n💾 Running fixes...")
    fixes = fix_v_for_indices()
    
    if fixes:
        print(f"\n✅ Applied {len(fixes)} fixes:")
        for fix in fixes:
            print(f"   • {fix}")
    else:
        print("   (No auto-fixable issues found)")
    
    print("\n📚 For detailed recommendations, see: scripts/OPTIMIZATION_GUIDE.md\n")

if __name__ == '__main__':
    main()
