import { h } from 'vue'

// Inline stroke icons (20x20 grid) used by the sidebar. No icon library needed.
const icon = (paths) => ({
  name: 'NavIcon',
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 20 20',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': '1.6',
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'aria-hidden': 'true'
      },
      paths.map((d) => h('path', { d }))
    )
  }
})

export const OverviewIcon = icon(['M3 3h5.5v7H3z', 'M11.5 3H17v4h-5.5z', 'M11.5 10H17v7h-5.5z', 'M3 13h5.5v4H3z'])
export const InventoryIcon = icon(['M3 6.5L10 3l7 3.5v7L10 17l-7-3.5z', 'M3 6.5L10 10l7-3.5', 'M10 10v7'])
export const OrdersIcon = icon(['M5 3h10v14H5z', 'M8 7h4', 'M8 10h4', 'M8 13h2'])
export const FinanceIcon = icon(['M3 16.5h14', 'M5 13V9', 'M9 13V5', 'M13 13V8', 'M17 13v-3'])
export const DemandIcon = icon(['M3 14l4-4 3 3 7-7', 'M13 6h4v4'])
export const RestockingIcon = icon(['M16 10a6 6 0 11-1.76-4.24', 'M16 3.5V6h-2.5', 'M10 7v3l2 1.5'])
export const ReportsIcon = icon(['M6 3h6l4 4v10H6z', 'M12 3v4h4', 'M9 11h4', 'M9 14h4'])
export const MenuIcon = icon(['M3 5.5h14', 'M3 10h14', 'M3 14.5h14'])
export const CollapseIcon = icon(['M12.5 5L7.5 10l5 5'])
