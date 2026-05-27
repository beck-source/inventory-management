import { createApp } from 'vue'
import { createRouter } from './router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Restocking from './views/Restocking.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'
import Backlog from './views/Backlog.vue'

const router = createRouter([
  { path: '/', component: Dashboard },
  { path: '/inventory', component: Inventory },
  { path: '/orders', component: Orders },
  { path: '/demand', component: Demand },
  { path: '/restocking', component: Restocking },
  { path: '/spending', component: Spending },
  { path: '/reports', component: Reports },
  { path: '/backlog', component: Backlog }
])

const app = createApp(App)
app.use(router)
app.mount('#app')
