import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Overview', component: Dashboard },
    { path: '/inventory', name: 'Inventory', component: Inventory },
    { path: '/orders', name: 'Orders', component: Orders },
    { path: '/demand', name: 'Demand Forecast', component: Demand },
    { path: '/spending', name: 'Finance', component: Spending },
    { path: '/reports', name: 'Reports', component: Reports }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
