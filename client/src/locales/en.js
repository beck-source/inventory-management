export default {
  // Navigation
  nav: {
    overview: "Overview",
    inventory: "Inventory",
    orders: "Orders",
    finance: "Finance",
    demandForecast: "Demand Forecast",
    restocking: "Restocking",
    reports: "Reports",
    companyName: "Catalyst Components",
    subtitle: "Inventory Management System",
  },

  // Dashboard
  dashboard: {
    title: "Overview",
    kpi: {
      title: "Key Performance Indicators",
      inventoryTurnover: "Inventory Turnover Rate",
      ordersFulfilled: "Orders Fulfilled",
      orderFillRate: "Order Fill Rate",
      revenue: "Revenue (Orders)",
      revenueYTD: "Revenue (Orders) YTD",
      revenueMTD: "Revenue (Orders) MTD",
      avgProcessingTime: "Avg Processing Time (Days)",
      goal: "Goal",
    },
    summary: {
      title: "Summary",
    },
    orderHealth: {
      title: "Order Health",
      totalOrders: "Total Orders",
      revenue: "Revenue",
      avgOrderValue: "Avg Order Value",
      onTimeRate: "On-Time Rate",
      avgFulfillmentDays: "Avg Fulfillment (Days)",
      total: "Total",
    },
    ordersByMonth: {
      title: "Orders by Month",
    },
    inventoryValue: {
      title: "Inventory Value by Category",
    },
    inventoryShortages: {
      actions: "Actions",
      createPo: "Create PO",
      viewPo: "View PO",
      viewDetails: "View details for order {id}",
      title: "Inventory Shortages",
      noShortages: "No inventory shortages - all orders can be fulfilled!",
      noData: "No inventory data for selected filters",
      orderId: "Order ID",
      sku: "SKU",
      itemName: "Item Name",
      quantityNeeded: "Quantity Needed",
      quantityAvailable: "Quantity Available",
      shortage: "Shortage",
      daysDelayed: "Days Delayed",
      priority: "Priority",
      unitsShort: "units short",
      days: "days",
    },
    topProducts: {
      title: "Top Products by Revenue",
      sku: "SKU",
      product: "Product",
      category: "Category",
      warehouse: "Warehouse",
      stockStatus: "Stock Status",
      revenue: "Revenue",
      unitsOrdered: "Units Ordered",
      firstOrder: "First Order",
      inStock: "In Stock",
      lowStock: "Low Stock",
    },
  },

  // Inventory
  inventory: {
    title: "Inventory",
    description: "Track and manage all inventory items",
    stockLevels: "Stock Levels",
    skus: "SKUs",
    searchPlaceholder: "Search by item name...",
    clearSearch: "Clear search",
    exportCsv: "Export CSV",
    totalItems: "Total Items",
    totalValue: "Total Value",
    lowStockItems: "Low Stock Items",
    warehouses: "Warehouses",
    table: {
      sku: "SKU",
      itemName: "Item Name",
      name: "Name",
      category: "Category",
      warehouse: "Warehouse",
      quantity: "Quantity",
      quantityOnHand: "Quantity on Hand",
      reorderPoint: "Reorder Point",
      unitCost: "Unit Cost",
      unitPrice: "Unit Price",
      totalValue: "Total Value",
      location: "Location",
      status: "Status",
    },
  },

  // Orders
  orders: {
    title: "Orders",
    description: "View and manage customer orders",
    allOrders: "All Orders",
    totalOrders: "Total Orders",
    totalRevenue: "Total Revenue",
    avgOrderValue: "Avg Order Value",
    onTimeDelivery: "On-Time Delivery",
    itemsCount: "{count} items",
    quantity: "Qty",
    table: {
      orderNumber: "Order Number",
      orderId: "Order ID",
      orderDate: "Order Date",
      date: "Date",
      customer: "Customer",
      category: "Category",
      warehouse: "Warehouse",
      items: "Items",
      value: "Value",
      totalValue: "Total Value",
      status: "Status",
      expectedDelivery: "Expected Delivery",
      actualDelivery: "Actual Delivery",
      submittedDate: "Submitted",
      leadTime: "Lead Time (days)",
    },
    submitted: {
      title: "Submitted Orders",
      empty: "No restock orders have been submitted yet",
      loadFailed: "Failed to load submitted orders",
    },
  },

  // Restocking
  restocking: {
    title: "Restocking",
    description:
      "Set a budget and order the items with the largest forecast shortfall",
    budget: "Budget",
    recommendations: "Recommended Items",
    empty: "No items can be recommended for this budget",
    loadFailed: "Failed to load recommendations",
    orderFailed: "Failed to place order",
    table: {
      select: "Select",
      sku: "SKU",
      name: "Item",
      category: "Category",
      trend: "Trend",
      stock: "In Stock",
      forecast: "Forecast",
      shortfall: "Shortfall",
      quantity: "Order Qty",
      unitCost: "Unit Cost",
      lineCost: "Line Cost",
      leadTime: "Lead Time (days)",
    },
    summary: {
      selectedTotal: "Selected Total",
      budget: "Budget",
      remaining: "Remaining Budget",
      leadTime: "Order Lead Time",
      days: "{count} days",
      overBudget:
        "Selected total exceeds the budget. Reduce quantities or deselect items.",
      nothingSelected: "Select at least one item to place an order.",
      invalidQty:
        "Order quantity must be a whole number between 1 and the shortfall for each selected item.",
    },
    placeOrder: "Place Order",
    placing: "Placing order...",
    confirmation: "Order {number} submitted. Expected delivery: {date}.",
    viewOrders: "View in Orders",
  },

  // Reports
  reports: {
    title: "Performance Reports",
    description: "View quarterly performance metrics and monthly trends",
    loading: "Loading reports...",
    loadFailed: "Failed to load reports",
    quarterly: {
      title: "Quarterly Performance",
      quarter: "Quarter",
      totalOrders: "Total Orders",
      totalRevenue: "Total Revenue",
      avgOrderValue: "Avg Order Value",
      fulfillmentRate: "Fulfillment Rate",
    },
    trend: {
      title: "Monthly Revenue Trend",
      barLabel: "{month}: {value}",
    },
    mom: {
      title: "Month-over-Month Analysis",
      month: "Month",
      orders: "Orders",
      revenue: "Revenue",
      change: "Change",
      growthRate: "Growth Rate",
    },
    summary: {
      totalRevenueYtd: "Total Revenue (YTD)",
      avgMonthlyRevenue: "Avg Monthly Revenue",
      totalOrdersYtd: "Total Orders (YTD)",
      bestQuarter: "Best Performing Quarter",
    },
    notAvailable: "N/A",
  },

  // Finance/Spending
  finance: {
    title: "Finance Dashboard",
    description: "Track revenue, costs, and financial performance",
    totalRevenue: "Total Revenue",
    totalCosts: "Total Costs",
    netProfit: "Net Profit",
    avgOrderValue: "Avg Order Value",
    fromOrders: "From {count} orders",
    costBreakdown: "Procurement + Operational + Labor + Overhead",
    margin: "margin",
    perOrderRevenue: "Per order revenue",
    revenueVsCosts: {
      title: "Monthly Revenue vs Costs",
      revenue: "Revenue",
      costs: "Total Costs",
    },
    monthlyCostFlow: {
      title: "Monthly Cost Flow",
      procurement: "Procurement",
      operational: "Operational",
      labor: "Labor",
      overhead: "Overhead",
    },
    categorySpending: {
      title: "Spending by Category",
      ofTotal: "of total",
    },
    transactionDetail: {
      title: "Transaction Details",
    },
    transactions: {
      title: "Recent Transactions",
      id: "ID",
      description: "Description",
      vendor: "Vendor",
      date: "Date",
      amount: "Amount",
    },
  },

  // Demand Forecast
  demand: {
    title: "Demand Forecast",
    description: "Analyze demand trends and forecasts",
    increasingDemand: "Increasing Demand",
    stableDemand: "Stable Demand",
    decreasingDemand: "Decreasing Demand",
    itemsCount: "{count} items",
    more: "more...",
    demandForecasts: "Demand Forecasts",
    table: {
      sku: "SKU",
      itemName: "Item Name",
      currentDemand: "Current Demand",
      forecastedDemand: "Forecasted Demand",
      change: "Change",
      trend: "Trend",
      period: "Period",
    },
  },

  // Filters
  filters: {
    timePeriod: "Time Period",
    location: "Location",
    category: "Category",
    orderStatus: "Order Status",
    all: "All",
    allMonths: "All Months",
    reset: "Reset all filters",
  },

  // Statuses
  status: {
    delivered: "Delivered",
    shipped: "Shipped",
    processing: "Processing",
    backordered: "Backordered",
    inStock: "In Stock",
    lowStock: "Low Stock",
    adequate: "Adequate",
    submitted: "Submitted",
  },

  // Trends
  trends: {
    increasing: "increasing",
    stable: "stable",
    decreasing: "decreasing",
  },

  // Backlog
  backlog: {
    title: "Backlog Management",
    description: "Track and resolve inventory shortages",
    loading: "Loading backlog...",
    loadFailed: "Failed to load backlog",
    highPriority: "High Priority",
    mediumPriority: "Medium Priority",
    lowPriority: "Low Priority",
    totalItems: "Total Backlog Items",
    itemsHeading: "Backlog Items",
    empty: "No backlog items - all orders can be fulfilled.",
    table: {
      orderId: "Order ID",
      sku: "SKU",
      itemName: "Item Name",
      quantityNeeded: "Quantity Needed",
      quantityAvailable: "Quantity Available",
      shortage: "Shortage",
      daysDelayed: "Days Delayed",
      priority: "Priority",
    },
    unitsShort: "{n} units short",
    days: "{n} days",
  },

  // Priority
  priority: {
    high: "High",
    medium: "Medium",
    low: "Low",
  },

  // Categories
  categories: {
    circuitBoards: "Circuit Boards",
    sensors: "Sensors",
    actuators: "Actuators",
    controllers: "Controllers",
    powerSupplies: "Power Supplies",
  },

  // Spending Categories
  spendingCategories: {
    rawMaterials: "Raw Materials",
    components: "Components",
    equipment: "Equipment",
    consumables: "Consumables",
  },

  // Warehouses
  warehouses: {
    sanFrancisco: "San Francisco",
    london: "London",
    tokyo: "Tokyo",
  },

  // Months
  months: {
    jan: "Jan",
    feb: "Feb",
    mar: "Mar",
    apr: "Apr",
    may: "May",
    jun: "Jun",
    jul: "Jul",
    aug: "Aug",
    sep: "Sep",
    oct: "Oct",
    nov: "Nov",
    dec: "Dec",
    january: "January",
    february: "February",
    march: "March",
    april: "April",
    june: "June",
    july: "July",
    august: "August",
    september: "September",
    october: "October",
    november: "November",
    december: "December",
  },

  // Profile Menu
  profile: {
    profileDetails: "Profile Details",
    myTasks: "My Tasks",
    logout: "Logout",
  },

  // Profile Details Modal
  profileDetails: {
    title: "Profile Details",
    email: "Email",
    department: "Department",
    location: "Location",
    phone: "Phone",
    joinDate: "Join Date",
    employeeId: "Employee ID",
    close: "Close",
  },

  // Tasks Modal
  tasks: {
    title: "My Tasks",
    taskTitle: "Task Title",
    taskTitlePlaceholder: "Enter task title...",
    priority: "Priority",
    dueDate: "Due Date",
    addTask: "Add Task",
    noTasks: "No tasks yet. Add your first task above!",
    deleteTask: "Delete task: {title}",
  },

  // Purchase Order Modal
  purchaseOrder: {
    createTitle: "Create Purchase Order",
    detailsTitle: "Purchase Order Details",
    sku: "SKU",
    supplierName: "Supplier Name",
    quantity: "Quantity",
    unitCost: "Unit Cost",
    expectedDeliveryDate: "Expected Delivery Date",
    notes: "Notes",
    cancel: "Cancel",
    close: "Close",
    create: "Create Purchase Order",
    creating: "Creating...",
    notFound: "No purchase order found.",
    loadFailed: "Failed to load purchase order",
    createFailed: "Failed to create purchase order",
    errorSummary: "Please correct the highlighted fields.",
    poNumber: "PO Number",
    status: "Status",
    supplier: "Supplier",
    totalCost: "Total Cost",
    expectedDelivery: "Expected Delivery",
    created: "Created",
    units: "{count} units",
    none: "None",
    na: "N/A",
    validation: {
      supplierRequired: "Supplier name is required.",
      quantityInvalid: "Quantity must be a whole number of at least 1.",
      unitCostInvalid: "Unit cost must be a number greater than 0.",
      dateRequired: "A valid expected delivery date is required.",
    },
  },

  // Language
  language: {
    english: "English",
    japanese: "Japanese",
    selectLanguage: "Select Language",
  },

  // Common
  common: {
    loading: "Loading...",
    loadFailed: "Failed to load data",
    retry: "Retry",
    error: "Error",
    noData: "No data available",
    viewDetails: "View Details",
    close: "Close",
    save: "Save",
    cancel: "Cancel",
    search: "Search",
    filter: "Filter",
    export: "Export",
    items: "items",
  },

  // Theme
  theme: {
    switchToLight: "Switch to light mode",
    switchToDark: "Switch to dark mode",
  },
};
