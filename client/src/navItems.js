// Single source of truth for the sidebar and the header page title.
// label is an i18n key; icon is a NavIcon name.
export const navItems = [
  { to: '/', label: 'nav.overview', icon: 'home', exact: true },
  { to: '/inventory', label: 'nav.inventory', icon: 'box' },
  { to: '/orders', label: 'nav.orders', icon: 'cart' },
  { to: '/spending', label: 'nav.finance', icon: 'dollar' },
  { to: '/demand', label: 'nav.demandForecast', icon: 'trend' },
  { to: '/restocking', label: 'nav.restocking', icon: 'refresh' },
  { to: '/reports', label: 'nav.reports', icon: 'file' }
]
