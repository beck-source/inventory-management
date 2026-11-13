export default {
  // Navigation
  nav: {
    overview: 'Overview',
    inventory: 'Inventory',
    orders: 'Orders',
    finance: 'Finance',
    demandForecast: 'Demand Forecast',
    restocking: 'Restocking',
    companyName: 'Catalyst Components',
    subtitle: 'Inventory Management System'
  },

  // Dashboard
  dashboard: {
    title: 'Overview',
    kpi: {
      title: 'Key Performance Indicators',
      inventoryTurnover: 'Inventory Turnover Rate',
      ordersFulfilled: 'Orders Fulfilled',
      orderFillRate: 'Order Fill Rate',
      revenue: 'Revenue (Orders)',
      revenueYTD: 'Revenue (Orders) YTD',
      revenueMTD: 'Revenue (Orders) MTD',
      avgProcessingTime: 'Avg Processing Time (Days)',
      goal: 'Goal'
    },
    summary: {
      title: 'Summary'
    },
    orderHealth: {
      title: 'Order Health',
      totalOrders: 'Total Orders',
      revenue: 'Revenue',
      avgOrderValue: 'Avg Order Value',
      onTimeRate: 'On-Time Rate',
      avgFulfillmentDays: 'Avg Fulfillment (Days)',
      total: 'Total'
    },
    ordersByMonth: {
      title: 'Orders by Month'
    },
    inventoryValue: {
      title: 'Inventory Value by Category'
    },
    inventoryShortages: {
      title: 'Inventory Shortages',
      noShortages: 'No inventory shortages - all orders can be fulfilled!',
      noData: 'No inventory data for selected filters',
      orderId: 'Order ID',
      sku: 'SKU',
      itemName: 'Item Name',
      quantityNeeded: 'Quantity Needed',
      quantityAvailable: 'Quantity Available',
      shortage: 'Shortage',
      daysDelayed: 'Days Delayed',
      priority: 'Priority',
      unitsShort: 'units short',
      days: 'days'
    },
    topProducts: {
      title: 'Top Products by Revenue',
      sku: 'SKU',
      product: 'Product',
      category: 'Category',
      warehouse: 'Warehouse',
      stockStatus: 'Stock Status',
      revenue: 'Revenue',
      unitsOrdered: 'Units Ordered',
      firstOrder: 'First Order',
      inStock: 'In Stock',
      lowStock: 'Low Stock'
    }
  },

  // Inventory
  inventory: {
    title: 'Inventory',
    description: 'Track and manage all inventory items',
    stockLevels: 'Stock Levels',
    skus: 'SKUs',
    searchPlaceholder: 'Search by item name...',
    clearSearch: 'Clear search',
    totalItems: 'Total Items',
    totalValue: 'Total Value',
    lowStockItems: 'Low Stock Items',
    warehouses: 'Warehouses',
    table: {
      sku: 'SKU',
      itemName: 'Item Name',
      name: 'Name',
      category: 'Category',
      warehouse: 'Warehouse',
      quantity: 'Quantity',
      quantityOnHand: 'Quantity on Hand',
      reorderPoint: 'Reorder Point',
      unitCost: 'Unit Cost',
      unitPrice: 'Unit Price',
      totalValue: 'Total Value',
      location: 'Location',
      status: 'Status'
    }
  },

  // Orders
  orders: {
    title: 'Orders',
    description: 'View and manage customer orders',
    allOrders: 'All Orders',
    submittedOrders: {
      title: 'Submitted Orders',
      empty: 'No restocking orders have been submitted yet.',
      orderNumber: 'Order Number',
      items: 'Items',
      total: 'Total',
      submitted: 'Submitted',
      leadTime: 'Lead Time',
      expectedDelivery: 'Expected Delivery',
      status: 'Status',
      loadError: 'Failed to load submitted orders',
      statusSubmitted: 'Submitted'
    },
    totalOrders: 'Total Orders',
    totalRevenue: 'Total Revenue',
    avgOrderValue: 'Avg Order Value',
    onTimeDelivery: 'On-Time Delivery',
    itemsCount: '{count} items',
    quantity: 'Qty',
    table: {
      orderNumber: 'Order Number',
      orderId: 'Order ID',
      orderDate: 'Order Date',
      date: 'Date',
      customer: 'Customer',
      category: 'Category',
      warehouse: 'Warehouse',
      items: 'Items',
      value: 'Value',
      totalValue: 'Total Value',
      status: 'Status',
      expectedDelivery: 'Expected Delivery',
      actualDelivery: 'Actual Delivery'
    }
  },

  // Restocking
  restocking: {
    title: 'Restocking',
    description: 'Choose a budget and review recommended purchases for items with forecast shortfalls',
    budget: {
      title: 'Restocking Budget',
      selected: 'Selected budget',
      max: 'Maximum useful budget',
      input: 'Budget amount',
      presets: {
        quarter: '25%',
        half: '50%',
        threeQuarters: '75%',
        max: 'Max'
      },
      utilization: '{percent}% of budget used'
    },
    recommendations: 'Recommended Purchases',
    table: {
      sku: 'SKU',
      name: 'Item',
      trend: 'Trend',
      quantity: 'Quantity',
      unitCost: 'Unit Cost',
      lineTotal: 'Line Total',
      leadTime: 'Lead Time'
    },
    days: '{count} days',
    summary: {
      totalCost: 'Total Cost',
      remainingBudget: 'Remaining Budget',
      estimatedDelivery: 'Estimated Delivery'
    },
    empty: 'This budget does not cover any recommended purchases. Increase the budget to see items.',
    noGaps: 'No restocking is needed at the moment.',
    placeOrder: 'Place Order',
    placing: 'Placing order…',
    updatingHint: 'Updating recommendations…',
    noItemsHint: 'No items to order',
    orderPlaced: 'Order {orderNumber} was placed successfully.',
    viewOrders: 'View in Orders',
    loadError: 'Failed to load restocking recommendations',
    orderError: 'Failed to place order',
    ai: {
      title: 'AI Recommendations',
      note: 'Generated by {model} from current stock and order history. Review before ordering.',
      usesBudget: 'Uses the selected budget: {amount}',
      budgetChanged: 'This plan was generated for {amount}. Generate again to use the current budget.',
      invalidBudgetResponse: 'The server rejected the selected budget.',
      generate: 'Generate',
      analyzing: 'Analyzing…',
      error: 'Failed to generate AI recommendations',
      empty: 'No restocking needed right now.',
      total: 'Total',
      placeOrder: 'Place Order',
      loadingStatus: 'Generating plan…',
      readyStatus: 'Plan ready: {count} items, total {amount}',
      placing: 'Placing order…',
      orderPlaced: 'Order {orderNumber} was placed successfully.',
      orderError: 'Failed to place order',
      noValue: '—',
      table: {
        sku: 'SKU',
        name: 'Item',
        onHand: 'On hand',
        reorderPoint: 'Reorder pt',
        daysOfCover: 'Days of cover',
        quantity: 'Qty',
        lineTotal: 'Line total',
        priority: 'Priority',
        reason: 'Reason'
      },
      priority: {
        high: 'High',
        medium: 'Medium',
        low: 'Low'
      }
    }
  },

  // Finance/Spending
  finance: {
    title: 'Finance Dashboard',
    description: 'Track revenue, costs, and financial performance',
    totalRevenue: 'Total Revenue',
    totalCosts: 'Total Costs',
    netProfit: 'Net Profit',
    avgOrderValue: 'Avg Order Value',
    fromOrders: 'From {count} orders',
    costBreakdown: 'Procurement + Operational + Labor + Overhead',
    margin: 'margin',
    perOrderRevenue: 'Per order revenue',
    revenueVsCosts: {
      title: 'Monthly Revenue vs Costs',
      revenue: 'Revenue',
      costs: 'Total Costs'
    },
    monthlyCostFlow: {
      title: 'Monthly Cost Flow',
      procurement: 'Procurement',
      operational: 'Operational',
      labor: 'Labor',
      overhead: 'Overhead'
    },
    categorySpending: {
      title: 'Spending by Category',
      ofTotal: 'of total'
    },
    transactions: {
      title: 'Recent Transactions',
      id: 'ID',
      description: 'Description',
      vendor: 'Vendor',
      date: 'Date',
      amount: 'Amount'
    }
  },

  // Demand Forecast
  demand: {
    title: 'Demand Forecast',
    description: 'Analyze demand trends and forecasts',
    increasingDemand: 'Increasing Demand',
    stableDemand: 'Stable Demand',
    decreasingDemand: 'Decreasing Demand',
    itemsCount: '{count} items',
    more: 'more...',
    demandForecasts: 'Demand Forecasts',
    table: {
      sku: 'SKU',
      itemName: 'Item Name',
      currentDemand: 'Current Demand',
      forecastedDemand: 'Forecasted Demand',
      change: 'Change',
      trend: 'Trend',
      period: 'Period'
    }
  },

  // Filters
  filters: {
    timePeriod: 'Time Period',
    location: 'Location',
    category: 'Category',
    orderStatus: 'Order Status',
    all: 'All',
    allMonths: 'All Months'
  },

  // Statuses
  status: {
    delivered: 'Delivered',
    shipped: 'Shipped',
    processing: 'Processing',
    backordered: 'Backordered',
    inStock: 'In Stock',
    lowStock: 'Low Stock',
    adequate: 'Adequate'
  },

  // Trends
  trends: {
    increasing: 'increasing',
    stable: 'stable',
    decreasing: 'decreasing'
  },

  // Priority
  priority: {
    high: 'High',
    medium: 'Medium',
    low: 'Low'
  },

  // Categories
  categories: {
    circuitBoards: 'Circuit Boards',
    sensors: 'Sensors',
    actuators: 'Actuators',
    controllers: 'Controllers',
    powerSupplies: 'Power Supplies'
  },

  // Spending Categories
  spendingCategories: {
    rawMaterials: 'Raw Materials',
    components: 'Components',
    equipment: 'Equipment',
    consumables: 'Consumables'
  },

  // Warehouses
  warehouses: {
    sanFrancisco: 'San Francisco',
    london: 'London',
    tokyo: 'Tokyo'
  },

  // Months
  months: {
    jan: 'Jan',
    feb: 'Feb',
    mar: 'Mar',
    apr: 'Apr',
    may: 'May',
    jun: 'Jun',
    jul: 'Jul',
    aug: 'Aug',
    sep: 'Sep',
    oct: 'Oct',
    nov: 'Nov',
    dec: 'Dec',
    january: 'January',
    february: 'February',
    march: 'March',
    april: 'April',
    june: 'June',
    july: 'July',
    august: 'August',
    september: 'September',
    october: 'October',
    november: 'November',
    december: 'December'
  },

  // Profile Menu
  profile: {
    profileDetails: 'Profile Details',
    myTasks: 'My Tasks',
    logout: 'Logout'
  },

  // Profile Details Modal
  profileDetails: {
    title: 'Profile Details',
    email: 'Email',
    department: 'Department',
    location: 'Location',
    phone: 'Phone',
    joinDate: 'Join Date',
    employeeId: 'Employee ID',
    close: 'Close'
  },

  // Tasks Modal
  tasks: {
    title: 'My Tasks',
    taskTitle: 'Task Title',
    taskTitlePlaceholder: 'Enter task title...',
    priority: 'Priority',
    dueDate: 'Due Date',
    addTask: 'Add Task',
    noTasks: 'No tasks yet. Add your first task above!'
  },

  // Purchase Order Modal
  purchaseOrder: {
    createTitle: 'Create Purchase Order',
    viewTitle: 'Purchase Order',
    shortage: 'Shortage',
    poNumber: 'PO Number',
    status: 'Status',
    supplier: 'Supplier',
    quantity: 'Quantity',
    unitCost: 'Unit Cost',
    total: 'Total',
    expectedDelivery: 'Expected Delivery',
    createdDate: 'Created',
    notes: 'Notes',
    submit: 'Create Purchase Order',
    saving: 'Saving...',
    loadFailed: 'Failed to load purchase order',
    createFailed: 'Failed to create purchase order',
    errSupplier: 'Supplier name is required (max 200 characters)',
    errQuantity: 'Quantity must be a whole number of at least 1',
    errUnitCost: 'Unit cost must be greater than 0',
    errDate: 'Expected delivery date is required',
    errNotes: 'Notes must be 2000 characters or fewer'
  },

  // Language
  language: {
    english: 'English',
    japanese: 'Japanese',
    selectLanguage: 'Select Language'
  },

  // Common
  common: {
    loading: 'Loading...',
    error: 'Error',
    noData: 'No data available',
    viewDetails: 'View Details',
    close: 'Close',
    save: 'Save',
    cancel: 'Cancel',
    search: 'Search',
    filter: 'Filter',
    export: 'Export',
    items: 'items'
  }
}
