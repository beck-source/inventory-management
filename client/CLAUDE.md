# CLAUDE.md - Client

This file provides guidance to Claude Code (claude.ai/code) when working with the Vue 3 frontend.

## Running the Client

```bash
npm run dev      # http://localhost:3000
npm run build    # output: client/dist/
```

## Component Pattern

This codebase uses Composition API via `export default { setup() {...} }`, **not** `<script setup>`. Follow the existing style in `views/*.vue` when adding components:

```vue
<script>
import { ref, computed, onMounted } from 'vue'
import { useFilters } from '../composables/useFilters'
import { api } from '../api'

export default {
  name: 'ComponentName',
  setup() {
    const { getCurrentFilters } = useFilters()
    const data = ref([])

    const loadData = async () => {
      data.value = await api.getSomething(getCurrentFilters())
    }

    onMounted(loadData)

    return { data }
  }
}
</script>
```

## Composables

- `useFilters` — module-level singleton holding the 4 shared filters (period/warehouse/category/status). Call `getCurrentFilters()` to build API query params.
- `useI18n` — translation lookup (`t('key.path')`) over `locales/en.js` / `locales/ja.js`, plus `currentCurrency` (USD/JPY) and `translateProductName`/`translateWarehouse`/`translateCustomerName` helpers for translating data values that aren't static UI strings.
- `useAuth` — fully mocked; don't build real auth flows against it.

Use `formatCurrency`/`convertAmount` from `utils/currency.js` for any displayed monetary value so JPY conversion stays consistent — don't hardcode `$`.

## Adding a Route

New top-level pages need a `<router-view>` route registered in `src/main.js`, not just a view file — see `Backlog.vue` for an example view that exists but was never wired into the router.

## Conventions

- v-for keys must be unique data fields (`sku`, `id`, `month`) — never array `index`
- Validate dates before calling `.getMonth()` — order dates aren't guaranteed well-formed
- API calls go through `src/api.js` only, never inline `axios` calls in components
