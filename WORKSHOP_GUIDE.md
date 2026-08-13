# Anthropic Partner Basecamp Workshop Guide

## Overview
This document explains everything we're doing in the Claude Code workshop. It's written in plain language so you can understand what's happening and why.

---

## What We're Building
We're working on a **Factory Inventory Management System** — a web application that helps factories track:
- Inventory levels across warehouses
- Customer orders and their status
- Demand forecasts
- Revenue and spending
- Backlog (orders waiting to be fulfilled)

The app has two parts:
1. **Frontend** (what you see) - A dashboard in your browser showing charts, tables, and metrics
2. **Backend** (the invisible part) - A server that stores data and sends it to the frontend when requested

---

## Steps Completed

### ✅ Step 1: Fork & Clone Repository (10 pts)
**What we did:**
- Forked the original inventory app from Anthropic's GitHub to your personal GitHub account
- Cloned (downloaded) it to your computer at `/Users/moukie/Claude/inventory-management`
- Created a working branch called `new_features` where we can safely make changes

**Why:** This gives you a personal copy of the code that you can modify without affecting anyone else's work.

---

### ✅ Step 2: Launch Claude Code (10 pts)
**What we did:**
- Opened Claude Code (the AI coding assistant you're using now)
- Selected the Haiku model for faster responses

**Why:** Claude Code helps us write, understand, and modify code throughout the workshop.

---

### ✅ Step 3: Run Inventory Management Locally (15 pts)
**What we did:**

1. **Installed Node.js** - Downloaded the JavaScript runtime your computer needed
2. **Installed Frontend Dependencies** - Ran `npm install` in the `client/` folder to get all the Vue 3 and Vite libraries the dashboard needs
3. **Installed Backend Dependencies** - Ran `uv sync` in the `server/` folder to get all the Python/FastAPI libraries the data server needs
4. **Started the Backend Server** - Launched the Python FastAPI server on port 8001 (this serves the data/API)
5. **Started the Frontend Server** - Launched the Vue 3 dev server on port 3000 (this serves the visual dashboard)
6. **Opened the App** - Navigated to `http://localhost:3000` in your browser to see the working dashboard

**Why:** Now you have a fully running app on your computer that you can modify and test.

**What's Running Now:**
- Frontend dashboard: `http://localhost:3000` - The visual inventory management interface
- Backend API: `http://localhost:8001` - The data server (API docs available at `http://localhost:8001/docs`)

---

---

### ✅ Step 4: Edit CLAUDE.md File (5 pts)
**What we did:**
- Reviewed the project's CLAUDE.md file (instructions for Claude)
- Added a "Code Style" section with the rule: "Always document non-obvious logic changes with comments"

**Why:** This file helps Claude understand project conventions and best practices.

---

### ✅ Step 5: Understand the Codebase (20 pts)
**What we did:**
1. Explored the codebase to understand architecture
2. Read key files: backend main.py, frontend api.js, view components
3. Generated a professional HTML architecture page explaining:
   - Frontend (Vue 3) ↔ Backend (FastAPI) ↔ Mock Data flow
   - Tech stack with all technologies used
   - API endpoints and how data flows
   - Dashboard pages and features
   - Filter system and data structures
4. Opened the page in browser at `http://localhost:8080/ARCHITECTURE.html`

**Why:** Understanding the system architecture is crucial before building new features. It helps us follow existing patterns and conventions.

---

### ✅ Step 6: Build Budget-Based Restocking Feature (25 pts)
**What we built:**
A complete budget-based restocking tool that allows users to:
1. Set a budget ($0-$50,000 USD) using an interactive slider
2. Get AI-recommended inventory items based on demand forecasts (sorted by highest demand gap)
3. Adjust recommended quantities in real-time with budget validation
4. Submit restocking orders that integrate with the Orders system
5. See submitted orders with "Submitted" status and 7-day delivery lead time

**Implementation Summary:**

**Backend (Python FastAPI):**
- ✅ New endpoint: `GET /api/restocking/recommendations?budget=X` - Returns items prioritized by demand gap, fills budget greedily
- ✅ New endpoint: `POST /api/restocking/orders` - Creates new orders with "Submitted" status and 7-day delivery
- ✅ New Pydantic models: RestockingItem, RestockingOrderItem, RestockingOrderRequest
- ✅ Budget validation: Prevents orders exceeding budget

**Frontend (Vue 3):**
- ✅ New component: `client/src/views/Restocking.vue` (15.9 KB) with:
  - Interactive budget slider ($0-$50,000, $100 steps)
  - Real-time stats cards (Total Budget, Item Count, Estimated Cost, Budget Remaining)
  - Recommended items table with adjustable quantities
  - Quantity validation and real-time cost calculation
  - Place Order button with budget constraint validation
  - Success/error messages
- ✅ New translations: English and Japanese i18n keys for all UI text
- ✅ Router integration: Route added to `/restocking` in main.js
- ✅ Navigation: "Restocking" tab added between "Demand Forecast" and "Reports"

**API Integration:**
- ✅ `api.getRestockingRecommendations(budget)` - Fetch recommendations
- ✅ `api.submitRestockingOrder(orderData)` - Submit order for placement

**Key Algorithms:**
- **Recommendation**: Match demand forecasts with inventory, calculate demand gaps (forecasted - current), sort descending, fill budget greedily
- **Budget Tracking**: Real-time total cost calculation, prevent overspend, show remaining budget
- **Order Creation**: Generate "RST-2025-XXXX" order numbers, set 7-day delivery lead time

**Testing Verified:**
✅ Backend endpoint returns recommendations sorted by demand gap  
✅ Budget slider triggers API calls and updates stats  
✅ Items count displays correctly  
✅ UI loads and renders without errors  
✅ Translations working for both English and Japanese  

---

## Summary: What We've Accomplished

**Steps Completed:**
- Step 1: Fork & Clone Repository (10 pts) ✅
- Step 2: Launch Claude Code (10 pts) ✅
- Step 3: Run Inventory Management Locally (15 pts) ✅
- Step 4: Edit CLAUDE.md File (5 pts) ✅
- Step 5: Understand the Codebase (20 pts) ✅
- Step 6: Build Budget-Based Restocking Feature (25 pts) ✅

**Total: 85 points earned** 🎉

**Technologies & Patterns Used:**
- Vue 3 Composition API with reactivity (ref, computed, watch)
- FastAPI with Pydantic validation
- Budget-constrained recommendation algorithm
- International i18n support
- RESTful API design
- Git workflow with feature branches

**Next Steps:**
Workshop is progressing well! Ready for Step 7 or iteration on existing features.

**Note:** This guide will be updated as we complete each step!
