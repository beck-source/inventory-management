export default {
  // Navigation
  nav: {
    overview: 'Command Center',
    inventory: 'Cargo Hold',
    orders: 'Trade Routes',
    finance: 'Credits Ledger',
    demandForecast: 'Intel Report',
    reports: 'Mission Logs',
    restocking: 'Supply Run',
    companyName: 'Catalyst Components',
    subtitle: 'Galactic Inventory System'
  },

  // Dashboard
  dashboard: {
    title: 'Command Center',
    kpi: {
      title: 'Galactic Intelligence Metrics',
      inventoryTurnover: 'Cargo Rotation Rate',
      ordersFulfilled: 'Missions Completed',
      orderFillRate: 'Mission Success Rate',
      revenue: 'Credits Earned (Trades)',
      revenueYTD: 'Credits Earned (Trades) YTD',
      revenueMTD: 'Credits Earned (Trades) MTD',
      avgProcessingTime: 'Avg Hyperjump Time (Cycles)',
      goal: 'Imperial Quota'
    },
    summary: {
      title: 'Holographic Briefing'
    },
    orderHealth: {
      title: 'Trade Route Health',
      totalOrders: 'Total Trade Runs',
      revenue: 'Credits',
      avgOrderValue: 'Avg Trade Value',
      onTimeRate: 'On-Time Rate',
      avgFulfillmentDays: 'Avg Delivery Cycles',
      total: 'Total'
    },
    ordersByMonth: {
      title: 'Trade Routes by Cycle'
    },
    inventoryValue: {
      title: 'Cargo Value by Class'
    },
    inventoryShortages: {
      title: 'Cargo Shortages',
      noShortages: 'No cargo shortages - all trade routes can be fulfilled!',
      noData: 'No cargo data for selected sectors',
      orderId: 'Mission ID',
      sku: 'Cargo Code',
      itemName: 'Cargo Name',
      quantityNeeded: 'Quantity Required',
      quantityAvailable: 'Quantity in Hold',
      shortage: 'Shortage',
      daysDelayed: 'Cycles Delayed',
      priority: 'Alert Level',
      unitsShort: 'units short',
      days: 'cycles'
    },
    topProducts: {
      title: 'Top Cargo by Credits',
      sku: 'Cargo Code',
      product: 'Cargo',
      category: 'Class',
      warehouse: 'Station',
      stockStatus: 'Hold Status',
      revenue: 'Credits',
      unitsOrdered: 'Units Traded',
      firstOrder: 'First Trade',
      inStock: 'Available',
      lowStock: 'Running Low'
    }
  },

  // Inventory
  inventory: {
    title: 'Cargo Hold',
    description: 'Track and manage all cargo in your hold',
    stockLevels: 'Hold Levels',
    skus: 'Cargo Codes',
    searchPlaceholder: 'Scan cargo hold...',
    clearSearch: 'Clear scan',
    totalItems: 'Total Cargo',
    totalValue: 'Total Credits',
    lowStockItems: 'Low Hold Items',
    warehouses: 'Stations',
    table: {
      sku: 'Cargo Code',
      itemName: 'Cargo Name',
      name: 'Name',
      category: 'Class',
      warehouse: 'Station',
      quantity: 'Quantity',
      quantityOnHand: 'Quantity on Hand',
      reorderPoint: 'Resupply Point',
      unitCost: 'Unit Cost',
      unitPrice: 'Unit Price',
      totalValue: 'Total Credits',
      location: 'Sector',
      status: 'Status'
    }
  },

  // Orders
  orders: {
    title: 'Trade Routes',
    description: 'View and manage all trade missions',
    allOrders: 'All Trade Routes',
    totalOrders: 'Total Trade Routes',
    totalRevenue: 'Total Credits',
    avgOrderValue: 'Avg Trade Value',
    onTimeDelivery: 'On-Time Delivery',
    itemsCount: '{count} items',
    quantity: 'Qty',
    table: {
      orderNumber: 'Mission Number',
      orderId: 'Mission ID',
      orderDate: 'Mission Date',
      date: 'Date',
      customer: 'Client',
      category: 'Class',
      warehouse: 'Station',
      items: 'Cargo',
      value: 'Credits',
      totalValue: 'Total Credits',
      status: 'Status',
      expectedDelivery: 'Estimated Arrival',
      actualDelivery: 'Actual Arrival'
    }
  },

  // Finance/Spending
  finance: {
    title: 'Credits Ledger',
    description: 'Track revenue, costs, and galactic financial performance',
    totalRevenue: 'Total Credits',
    totalCosts: 'Total Expenditures',
    netProfit: 'Net Credits',
    avgOrderValue: 'Avg Trade Value',
    fromOrders: 'From {count} trade runs',
    costBreakdown: 'Procurement + Operational + Labor + Overhead',
    margin: 'margin',
    perOrderRevenue: 'Per trade revenue',
    revenueVsCosts: {
      title: 'Monthly Credits vs Expenditures',
      revenue: 'Credits',
      costs: 'Total Expenditures'
    },
    monthlyCostFlow: {
      title: 'Monthly Expenditure Flow',
      procurement: 'Procurement',
      operational: 'Operational',
      labor: 'Labor',
      overhead: 'Overhead'
    },
    categorySpending: {
      title: 'Spending by Class',
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
    title: 'Intel Report',
    description: 'Analyze demand trends across the galaxy',
    increasingDemand: 'Rising Demand',
    stableDemand: 'Balanced Demand',
    decreasingDemand: 'Fading Demand',
    itemsCount: '{count} items',
    more: 'more...',
    demandForecasts: 'Demand Intelligence',
    table: {
      sku: 'Cargo Code',
      itemName: 'Cargo Name',
      currentDemand: 'Current Demand',
      forecastedDemand: 'Forecasted Demand',
      change: 'Change',
      trend: 'Trend',
      period: 'Period'
    }
  },

  // Filters
  filters: {
    timePeriod: 'Time Cycle',
    location: 'Sector',
    category: 'Class',
    orderStatus: 'Mission Status',
    all: 'All',
    allMonths: 'All Cycles'
  },

  // Statuses
  status: {
    delivered: 'Kessel Run Complete',
    shipped: 'Jumped to Hyperspace',
    processing: 'Aboard the Falcon',
    backordered: 'Stuck on Tatooine',
    inStock: 'In Hold',
    lowStock: 'Running Low',
    adequate: 'Well Stocked'
  },

  // Trends
  trends: {
    increasing: 'rising',
    stable: 'in the Force balance',
    decreasing: 'fading'
  },

  // Priority
  priority: {
    high: 'Code Red Alert',
    medium: 'Standard Alert',
    low: 'No Disturbance'
  },

  // Categories
  categories: {
    circuitBoards: 'Droid Logic Boards',
    sensors: 'Sensor Arrays',
    actuators: 'Servo Units',
    controllers: 'Navigation Controllers',
    powerSupplies: 'Power Cells'
  },

  // Spending Categories
  spendingCategories: {
    rawMaterials: 'Raw Ore',
    components: 'Components',
    equipment: 'Equipment',
    consumables: 'Rations'
  },

  // Warehouses
  warehouses: {
    sanFrancisco: 'Coruscant Hub',
    london: 'Bespin Station',
    tokyo: 'Tatooine Depot'
  },

  // Months
  months: {
    jan: 'First Cycle',
    feb: 'Second Cycle',
    mar: 'Third Cycle',
    apr: 'Fourth Cycle',
    may: 'Fifth Cycle',
    jun: 'Sixth Cycle',
    jul: 'Seventh Cycle',
    aug: 'Eighth Cycle',
    sep: 'Ninth Cycle',
    oct: 'Tenth Cycle',
    nov: 'Eleventh Cycle',
    dec: 'Twelfth Cycle',
    january: 'Month of the First Cycle',
    february: 'Month of the Second Cycle',
    march: 'Month of the Third Cycle',
    april: 'Month of the Fourth Cycle',
    june: 'Month of the Sixth Cycle',
    july: 'Month of the Seventh Cycle',
    august: 'Month of the Eighth Cycle',
    september: 'Month of the Ninth Cycle',
    october: 'Month of the Tenth Cycle',
    november: 'Month of the Eleventh Cycle',
    december: 'Month of the Twelfth Cycle'
  },

  // Profile Menu
  profile: {
    profileDetails: 'Mission Dossier',
    myTasks: 'My Missions',
    logout: 'Leave the Cantina'
  },

  // Profile Details Modal
  profileDetails: {
    title: 'Mission Dossier',
    email: 'Holo Address',
    department: 'Division',
    location: 'Station',
    phone: 'Comm Channel',
    joinDate: 'Enlistment Date',
    employeeId: 'Trooper ID',
    close: 'These aren\'t the droids you\'re looking for'
  },

  // Tasks Modal
  tasks: {
    title: 'My Missions',
    taskTitle: 'Mission Title',
    taskTitlePlaceholder: 'Enter mission title...',
    priority: 'Alert Level',
    dueDate: 'Mission Deadline',
    addTask: 'Add Mission',
    noTasks: 'No missions yet. Plan your first mission above!'
  },

  // Language
  language: {
    english: 'Galactic Basic',
    japanese: 'Japanese',
    selectLanguage: 'Select Language',
    starwars: 'Galactic Basic',
    minecraft: 'Enchantment Language'
  },

  // Common
  common: {
    loading: 'Calculating jump to hyperspace...',
    error: 'The Force has been disturbed',
    noData: 'Nothing in the holonet, there is',
    viewDetails: 'Open Holofile',
    close: 'These aren\'t the droids you\'re looking for',
    save: 'Transmit to Fleet',
    cancel: 'Abort Mission',
    search: 'Scan holonet',
    filter: 'Narrow Sector',
    export: 'Transmit Data',
    items: 'items'
  },

  // Reports
  reports: {
    title: 'Mission Logs',
    description: 'Quarterly and cycle performance analytics',
    quarterlyTitle: 'Quarterly Mission Performance',
    monthlyTitle: 'Monthly Credits Trend',
    momTitle: 'Cycle-over-Cycle Analysis',
    quarter: 'Quarter',
    totalOrders: 'Total Trade Routes',
    totalRevenue: 'Total Credits',
    delivered: 'Delivered',
    avgOrderValue: 'Avg Trade Value',
    fulfillmentRate: 'Mission Success Rate',
    month: 'Cycle',
    orderCount: 'Trade Count',
    revenue: 'Credits',
    deliveredCount: 'Delivered Count',
    change: 'Change',
    growthRate: 'Growth Rate',
    ytdRevenue: 'Total Credits (YTD)',
    ytdOrders: 'Total Trades (YTD)',
    avgFulfillment: 'Avg Mission Success Rate',
    avgMonthlyRevenue: 'Avg Monthly Credits',
    ytdDelivered: 'Delivered Trades (YTD)',
    bestQuarter: 'Best Performing Quarter'
  },

  // Backlog
  backlog: {
    title: 'Supply Run',
    description: 'Track and resolve cargo shortages',
    highPriority: 'Code Red Alert',
    mediumPriority: 'Standard Alert',
    lowPriority: 'No Disturbance',
    totalItems: 'Total Backlog Items',
    items: 'Backlog Items',
    noItems: 'No backlog - all trade routes can be fulfilled!',
    orderId: 'Mission ID',
    sku: 'Cargo Code',
    itemName: 'Cargo Name',
    quantityNeeded: 'Quantity Required',
    quantityAvailable: 'Quantity in Hold',
    shortage: 'Shortage',
    daysDelayed: 'Cycles Delayed',
    priority: 'Alert Level',
    unitsShort: 'units short',
    days: 'cycles'
  }
}
