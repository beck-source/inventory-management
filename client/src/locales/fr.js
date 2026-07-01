export default {
  // Navigation
  nav: {
    overview: 'Vue d\'ensemble',
    inventory: 'Inventaire',
    orders: 'Commandes',
    finance: 'Finance',
    demandForecast: 'Prévisions de demande',
    restocking: 'Réapprovisionnement',
    reports: 'Rapports',
    companyName: 'Catalyst Components',
    subtitle: 'Système de gestion des stocks'
  },

  // Dashboard
  dashboard: {
    title: 'Vue d\'ensemble',
    kpi: {
      title: 'Indicateurs clés de performance',
      inventoryTurnover: 'Taux de rotation des stocks',
      ordersFulfilled: 'Commandes exécutées',
      orderFillRate: 'Taux de satisfaction',
      revenue: 'Chiffre d\'affaires (Commandes)',
      revenueYTD: 'CA (Commandes) depuis le début de l\'année',
      revenueMTD: 'CA (Commandes) depuis le début du mois',
      avgProcessingTime: 'Délai moyen de traitement (jours)',
      goal: 'Objectif'
    },
    summary: {
      title: 'Résumé'
    },
    orderHealth: {
      title: 'Santé des commandes',
      totalOrders: 'Total des commandes',
      revenue: 'Chiffre d\'affaires',
      avgOrderValue: 'Valeur moyenne des commandes',
      onTimeRate: 'Taux de livraison à temps',
      avgFulfillmentDays: 'Délai moyen d\'exécution (jours)',
      total: 'Total'
    },
    ordersByMonth: {
      title: 'Commandes par mois'
    },
    inventoryValue: {
      title: 'Valeur des stocks par catégorie'
    },
    inventoryShortages: {
      title: 'Ruptures de stock',
      noShortages: 'Aucune rupture de stock — toutes les commandes peuvent être honorées !',
      noData: 'Aucune donnée d\'inventaire pour les filtres sélectionnés',
      orderId: 'N° de commande',
      sku: 'SKU',
      itemName: 'Nom de l\'article',
      quantityNeeded: 'Quantité requise',
      quantityAvailable: 'Quantité disponible',
      shortage: 'Manque',
      daysDelayed: 'Jours de retard',
      priority: 'Priorité',
      unitsShort: 'unités manquantes',
      days: 'jours'
    },
    topProducts: {
      title: 'Meilleurs produits par chiffre d\'affaires',
      sku: 'SKU',
      product: 'Produit',
      category: 'Catégorie',
      warehouse: 'Entrepôt',
      stockStatus: 'État des stocks',
      revenue: 'Chiffre d\'affaires',
      unitsOrdered: 'Unités commandées',
      firstOrder: 'Première commande',
      inStock: 'En stock',
      lowStock: 'Stock faible'
    }
  },

  // Inventory
  inventory: {
    title: 'Inventaire',
    description: 'Suivi et gestion de tous les articles en stock',
    stockLevels: 'Niveaux de stock',
    skus: 'SKU',
    searchPlaceholder: 'Rechercher par nom d\'article...',
    clearSearch: 'Effacer la recherche',
    totalItems: 'Total des articles',
    totalValue: 'Valeur totale',
    lowStockItems: 'Articles en stock faible',
    warehouses: 'Entrepôts',
    table: {
      sku: 'SKU',
      itemName: 'Nom de l\'article',
      name: 'Nom',
      category: 'Catégorie',
      warehouse: 'Entrepôt',
      quantity: 'Quantité',
      quantityOnHand: 'Stock disponible',
      reorderPoint: 'Point de réapprovisionnement',
      unitCost: 'Coût unitaire',
      unitPrice: 'Prix unitaire',
      totalValue: 'Valeur totale',
      location: 'Emplacement',
      status: 'Statut'
    }
  },

  // Orders
  orders: {
    title: 'Commandes',
    description: 'Consulter et gérer les commandes clients',
    allOrders: 'Toutes les commandes',
    totalOrders: 'Total des commandes',
    totalRevenue: 'Chiffre d\'affaires total',
    avgOrderValue: 'Valeur moyenne des commandes',
    onTimeDelivery: 'Livraison à temps',
    itemsCount: '{count} articles',
    quantity: 'Qté',
    restockingOrders: 'Commandes de réapprovisionnement',
    noRestockingOrders: 'Aucune commande de réapprovisionnement envoyée.',
    submittedAt: 'Envoyée le',
    table: {
      orderNumber: 'N° de commande',
      orderId: 'ID commande',
      orderDate: 'Date de commande',
      date: 'Date',
      customer: 'Client',
      category: 'Catégorie',
      warehouse: 'Entrepôt',
      items: 'Articles',
      value: 'Valeur',
      totalValue: 'Valeur totale',
      status: 'Statut',
      expectedDelivery: 'Livraison prévue',
      actualDelivery: 'Livraison effective'
    }
  },

  // Restocking Planner
  restocking: {
    title: 'Plan de réapprovisionnement',
    description: 'Recommande les articles à réapprovisionner selon les prévisions de demande et le budget disponible',
    budgetLabel: 'Budget disponible',
    recommendedItems: 'Articles recommandés',
    totalCost: 'Coût total',
    remainingBudget: 'Budget restant',
    placeOrder: 'Passer la commande',
    orderPlaced: 'Commande de réapprovisionnement envoyée avec succès',
    noRecommendations: 'Aucun article ne peut être recommandé avec le budget actuel',
    confirmOrder: 'Confirmer et envoyer cette commande de réapprovisionnement ?',
    submitting: 'Envoi en cours...',
    belowReorder: 'Sous le point de réappro.',
    table: {
      sku: 'SKU',
      itemName: 'Nom de l\'article',
      trend: 'Tendance',
      unitCost: 'Coût unitaire',
      quantityToOrder: 'Qté à commander',
      totalCost: 'Coût total',
      belowReorder: 'Sous le seuil'
    }
  },

  // Finance/Spending
  finance: {
    title: 'Tableau de bord financier',
    description: 'Suivi des revenus, des coûts et de la performance financière',
    totalRevenue: 'Chiffre d\'affaires total',
    totalCosts: 'Coûts totaux',
    netProfit: 'Bénéfice net',
    avgOrderValue: 'Valeur moyenne des commandes',
    fromOrders: 'Sur {count} commandes',
    costBreakdown: 'Achats + Exploitation + Main d\'œuvre + Frais généraux',
    margin: 'marge',
    perOrderRevenue: 'CA par commande',
    revenueVsCosts: {
      title: 'Revenus mensuels vs Coûts',
      revenue: 'Revenus',
      costs: 'Coûts totaux'
    },
    monthlyCostFlow: {
      title: 'Flux de coûts mensuels',
      procurement: 'Achats',
      operational: 'Exploitation',
      labor: 'Main d\'œuvre',
      overhead: 'Frais généraux'
    },
    categorySpending: {
      title: 'Dépenses par catégorie',
      ofTotal: 'du total'
    },
    transactions: {
      title: 'Transactions récentes',
      id: 'ID',
      description: 'Description',
      vendor: 'Fournisseur',
      date: 'Date',
      amount: 'Montant'
    }
  },

  // Demand Forecast
  demand: {
    title: 'Prévisions de demande',
    description: 'Analyser les tendances de la demande et anticiper les besoins futurs',
    increasingDemand: 'Demande en hausse',
    stableDemand: 'Demande stable',
    decreasingDemand: 'Demande en baisse',
    itemsCount: '{count} articles',
    more: 'autres...',
    demandForecasts: 'Prévisions de demande',
    table: {
      sku: 'SKU',
      itemName: 'Nom de l\'article',
      currentDemand: 'Demande actuelle',
      forecastedDemand: 'Demande prévisionnelle',
      change: 'Variation',
      trend: 'Tendance',
      period: 'Période'
    }
  },

  // Filters
  filters: {
    timePeriod: 'Période',
    location: 'Lieu',
    category: 'Catégorie',
    orderStatus: 'Statut de la commande',
    all: 'Tous',
    allMonths: 'Tous les mois'
  },

  // Statuses
  status: {
    delivered: 'Livré',
    shipped: 'Expédié',
    processing: 'En cours',
    backordered: 'En rupture',
    pending: 'En attente',
    inStock: 'En stock',
    lowStock: 'Stock faible',
    adequate: 'Suffisant'
  },

  // Trends
  trends: {
    increasing: 'hausse',
    stable: 'stable',
    decreasing: 'baisse'
  },

  // Priority
  priority: {
    high: 'Haute',
    medium: 'Moyenne',
    low: 'Basse'
  },

  // Categories
  categories: {
    circuitBoards: 'Circuits imprimés',
    sensors: 'Capteurs',
    actuators: 'Actionneurs',
    controllers: 'Contrôleurs',
    powerSupplies: 'Alimentations'
  },

  // Spending Categories
  spendingCategories: {
    rawMaterials: 'Matières premières',
    components: 'Composants',
    equipment: 'Équipement',
    consumables: 'Consommables'
  },

  // Warehouses
  warehouses: {
    sanFrancisco: 'San Francisco',
    london: 'Londres',
    tokyo: 'Tokyo'
  },

  // Months
  months: {
    jan: 'Jan',
    feb: 'Fév',
    mar: 'Mar',
    apr: 'Avr',
    may: 'Mai',
    jun: 'Juin',
    jul: 'Juil',
    aug: 'Août',
    sep: 'Sep',
    oct: 'Oct',
    nov: 'Nov',
    dec: 'Déc',
    january: 'Janvier',
    february: 'Février',
    march: 'Mars',
    april: 'Avril',
    june: 'Juin',
    july: 'Juillet',
    august: 'Août',
    september: 'Septembre',
    october: 'Octobre',
    november: 'Novembre',
    december: 'Décembre'
  },

  // Profile Menu
  profile: {
    profileDetails: 'Détails du profil',
    myTasks: 'Mes tâches',
    logout: 'Déconnexion'
  },

  // Profile Details Modal
  profileDetails: {
    title: 'Détails du profil',
    email: 'E-mail',
    department: 'Département',
    location: 'Lieu',
    phone: 'Téléphone',
    joinDate: 'Date d\'entrée',
    employeeId: 'ID employé',
    close: 'Fermer'
  },

  // Tasks Modal
  tasks: {
    title: 'Mes tâches',
    taskTitle: 'Titre de la tâche',
    taskTitlePlaceholder: 'Saisir le titre de la tâche...',
    priority: 'Priorité',
    dueDate: 'Échéance',
    addTask: 'Ajouter une tâche',
    noTasks: 'Aucune tâche. Ajoutez votre première tâche ci-dessus !'
  },

  // Language
  language: {
    english: 'Anglais',
    japanese: 'Japonais',
    french: 'Français',
    selectLanguage: 'Choisir la langue'
  },

  // Reports
  reports: {
    title: 'Rapports de performance',
    description: 'Consultez les indicateurs trimestriels et les tendances mensuelles',
    quarterlyPerformance: 'Performance trimestrielle',
    monthlyRevenueTrend: 'Tendance mensuelle des revenus',
    monthOverMonth: 'Analyse mois par mois',
    quarter: 'Trimestre',
    totalOrders: 'Total des commandes',
    totalRevenue: 'Revenu total',
    avgOrderValue: 'Valeur moy. des commandes',
    fulfillmentRate: "Taux d'exécution",
    month: 'Mois',
    orders: 'Commandes',
    revenue: 'Revenu',
    change: 'Variation',
    growthRate: 'Taux de croissance',
    totalRevenueYTD: "Revenu total (depuis début d'année)",
    avgMonthlyRevenue: 'Revenu mensuel moyen',
    totalOrdersYTD: "Total commandes (depuis début d'année)",
    bestQuarter: 'Meilleur trimestre',
    loadError: 'Échec du chargement des rapports'
  },

  // Common
  common: {
    loading: 'Chargement...',
    error: 'Erreur',
    noData: 'Aucune donnée disponible',
    viewDetails: 'Voir les détails',
    close: 'Fermer',
    save: 'Enregistrer',
    cancel: 'Annuler',
    search: 'Rechercher',
    filter: 'Filtrer',
    export: 'Exporter',
    items: 'articles'
  }
}
