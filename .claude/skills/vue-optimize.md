# Vue Component Optimization Analyzer

Analyze Vue 3 components for performance optimizations and code reuse opportunities.

## Skill Invocation

This skill is invoked with `/vue-optimize [path]` where path can be:
- A specific .vue file
- A directory containing Vue components (will analyze all .vue files)
- Omitted (will analyze all Vue components in client/src/)

## Analysis Steps

When this skill is invoked:

1. **Locate Components**
   - Find all .vue files in the specified path or default to client/src/
   - List components to be analyzed

2. **Read and Parse Components**
   - Read each .vue file
   - Identify script, template, and style sections
   - Note the component structure

3. **Performance Analysis**
   
   Check for these performance issues:
   
   **Reactivity Issues:**
   - Large reactive objects that should be split
   - Reactive data that never changes (should be const)
   - Missing `ref()` or `reactive()` for state
   - Unnecessary deep reactivity with `reactive()` on large objects
   
   **Computed Properties:**
   - Expensive calculations in templates that should be computed
   - Missing computed properties for derived state
   - Computed properties with side effects
   
   **Watchers:**
   - Watchers that could be computed properties
   - Watchers without cleanup (memory leaks)
   - Deep watchers on large objects
   
   **Template Optimization:**
   - v-if vs v-show usage (v-show for frequent toggles)
   - Missing :key in v-for loops
   - v-for with v-if on same element (anti-pattern)
   - Inline functions in templates (create new functions on each render)
   
   **Component Loading:**
   - Missing lazy loading with defineAsyncComponent
   - Heavy components that should be code-split
   
   **Props & Events:**
   - Missing prop validation
   - Props being mutated directly
   - Too many props (component doing too much)

4. **Code Reuse Analysis**
   
   Identify opportunities for:
   
   **Composables:**
   - Duplicated logic across components (state + methods)
   - Complex logic that could be extracted (useXXX pattern)
   - API calls that could be shared
   - Form validation logic
   - Data fetching patterns
   
   **Component Extraction:**
   - Repeated UI patterns (buttons, cards, modals)
   - Large components that could be split
   - Template sections that appear in multiple places
   
   **Shared Utilities:**
   - Duplicated helper functions
   - Formatting logic (dates, currency, numbers)
   - Validation functions

5. **Best Practices Check**
   
   - Component naming (PascalCase for components)
   - Single responsibility principle
   - Props naming (camelCase)
   - Event naming (kebab-case)
   - Composition API usage (recommended over Options API)
   - TypeScript type safety

## Output Format

Provide findings in this structure:

```markdown
## Vue Component Optimization Report

### Components Analyzed
- List of analyzed files

### Performance Issues

#### Critical Issues
- Issue description
- File: path/to/component.vue:line
- Impact: High/Medium/Low
- Recommendation: Specific fix

#### Medium Priority Issues
...

#### Low Priority Issues
...

### Code Reuse Opportunities

#### Composables to Create
- Suggested composable name: `useXXX`
- Files that would benefit: [list]
- Shared logic: [description]
- Example implementation: [code snippet]

#### Components to Extract
- Suggested component name
- Current locations: [list]
- Reuse benefit: [description]

#### Shared Utilities
- Function name
- Current duplications: [list]
- Suggested location: utils/xxx.js

### Specific Recommendations

For each component, provide actionable recommendations:

**ComponentName.vue**
1. Move expensive calculation to computed property (line X)
2. Extract API logic to useProducts() composable
3. Add prop validation for `items` prop
...

### Summary
- Total issues found: X
- Critical: X, Medium: X, Low: X
- Code reuse opportunities: X composables, X components, X utilities
- Estimated performance improvement: [qualitative assessment]
```

## Example Invocations

```bash
# Analyze all components
/vue-optimize

# Analyze specific component
/vue-optimize client/src/components/Dashboard.vue

# Analyze directory
/vue-optimize client/src/views
```

## Notes

- Focus on actionable recommendations, not theoretical issues
- Prioritize issues by actual impact on performance
- Consider the project context (small app vs large app)
- Provide code examples for recommended changes
- Check for patterns across multiple components, not just individual issues
- Be specific about line numbers when identifying issues
