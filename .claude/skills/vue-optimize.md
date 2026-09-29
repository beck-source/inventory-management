# Vue Component Optimizer

Analyze Vue components for performance optimizations and best practices aligned with Vue 3 Composition API patterns.

## Usage

```
/vue-optimize [file_or_directory]
```

- **Single file**: `/vue-optimize client/src/views/Orders.vue`
- **Directory**: `/vue-optimize client/src/components`
- **Component tree**: `/vue-optimize client/src/views` (analyzes all .vue files and relationships)

## Analysis Framework

When analyzing Vue components, evaluate these dimensions:

### 1. Reactivity & State Management
- [ ] Reactive refs vs computed properties (unnecessary refs that could be computed?)
- [ ] Computed properties that should use `computed()` wrapper
- [ ] Watchers that could be replaced with computed properties
- [ ] Deep watching when shallow watch would suffice
- [ ] Unnecessary reactivity for static data

**Example**: If a component has:
```javascript
const total = ref(0)
watch([budget, items], () => { total.value = calculateTotal() })
```
Suggest: Use `computed` instead to eliminate manual synchronization.

### 2. Component Extraction & Reuse
- [ ] Components larger than 200 lines (candidates for splitting)
- [ ] Duplicate template sections (extract to sub-components)
- [ ] Repeated logic patterns (candidates for composables)
- [ ] Props that could be a shared type/interface
- [ ] Multiple concerns in one component (separation of concerns)

**Example**: A component mixing data fetching, filtering, and display logic should extract the data/filter logic into a composable.

### 3. Composition API Patterns
- [ ] Setup function organization (group by feature)
- [ ] Exposing only necessary properties
- [ ] Unused imports or computed properties
- [ ] Composable extraction opportunities
- [ ] Lifecycle hook consolidation

**Example**: Component with separate `onMounted`, `onUpdated`, `onUnmounted` watchers could consolidate into a single composable.

### 4. Performance & Rendering
- [ ] Unnecessary re-renders (check v-for keys, watch dependencies)
- [ ] v-if vs v-show usage (toggle frequency)
- [ ] Prop mutations (data flowing down, events flowing up)
- [ ] Expensive computations in templates
- [ ] Memory leaks in event listeners/watchers

**Example**: 
```javascript
// ❌ Recomputes every render
{{ items.filter(x => x.active).length }}

// ✅ Computed property
const activeCount = computed(() => items.value.filter(x => x.active).length)
```

### 5. i18n & Maintainability
- [ ] Hardcoded strings vs i18n keys
- [ ] Translation keys properly namespaced
- [ ] Unused translation keys
- [ ] Missing translations for user-facing text

### 6. Type Safety & Validation
- [ ] Props without validation
- [ ] Magic numbers/strings (should be constants)
- [ ] Response data structure assumptions
- [ ] Error handling completeness

## Output Format

Generate a markdown report with structure:

```markdown
# Vue Component Analysis

## File: [path]
**Status**: ✅ Good | ⚠️ Needs Review | 🔴 Critical Issues

### 🎯 Key Findings
- Finding 1 (priority)
- Finding 2 (priority)

### ✅ What's Working Well
- Pattern 1
- Pattern 2

### 🔧 Optimization Opportunities
#### 1. [Category] - [Priority]
**Current**: Code snippet
**Issue**: Explanation
**Suggestion**: Recommended approach
**Impact**: Performance/maintainability improvement

#### 2. [Category] - [Priority]
...

### 📊 Metrics
- Lines of code: X
- Computed properties: Y
- Watchers: Z
- Components referenced: N
- Recommendation: Extract into N sub-components

### 🔗 Related Components
- parent-component.vue (uses this)
- child-component.vue (used by this)
- shared-logic.js (can be extracted from here)
```

## Priority Levels

- **🔴 Critical**: Performance issues, memory leaks, pattern anti-patterns
- **🟠 High**: Code reuse opportunities, component extraction (affects 3+ other files)
- **🟡 Medium**: Code organization, single-concern extraction
- **🟢 Low**: Style consistency, minor optimizations

## Analysis Tips

1. **Component Tree Analysis**: When analyzing a directory, identify:
   - Deeply nested components that could be flattened
   - Duplicate components with similar logic
   - Props drilling through many levels (composable opportunity)
   - Circular dependencies

2. **Performance Analysis**: Look for:
   - Computed properties that watch unnecessary dependencies
   - Templates with expensive filters/sorts
   - Inefficient v-for loops without keys
   - Global watchers that should be local

3. **Pattern Alignment**: Check against project conventions in CLAUDE.md:
   - Uses Composition API (not Options API)
   - Follows Vue 3 best practices
   - Consistent with existing component patterns
   - Proper i18n usage

## Project Context

This project uses:
- Vue 3 Composition API
- Vite bundler
- i18n for English/Japanese translations
- Pydantic backend validation
- Filter system for data views

## Deliverable

Provide markdown report (in artifact if analyzing multiple files/directory) with:
- Clear, actionable recommendations
- Code examples showing before/after
- Priority ranking
- Estimated effort to implement
- Which recommendations are interdependent
