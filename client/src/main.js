import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'

// meta.titleKey drives the sidebar label via useI18n's t(); meta.icon
// selects the icon from components/Icon.vue. Keeping nav data on the route
// table (rather than a separate list) means the sidebar and router can't
// drift out of sync.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { titleKey: 'nav.overview', icon: 'grid' } },
    { path: '/inventory', component: Inventory, meta: { titleKey: 'nav.inventory', icon: 'box' } },
    { path: '/orders', component: Orders, meta: { titleKey: 'nav.orders', icon: 'cart' } },
    { path: '/demand', component: Demand, meta: { titleKey: 'nav.demandForecast', icon: 'trending' } },
    { path: '/spending', component: Spending, meta: { titleKey: 'nav.finance', icon: 'dollar' } },
    { path: '/reports', component: Reports, meta: { title: 'Reports', icon: 'chart' } }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
