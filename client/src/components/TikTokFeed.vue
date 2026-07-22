<template>
  <div class="feed-wrap">
    <div v-if="loading" class="feed-loading">
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
    </div>

    <div v-else-if="posts.length === 0" class="feed-empty">
      No inventory events found.
    </div>

    <div v-else class="feed-scroller">
      <div
        v-for="post in posts"
        :key="post.id"
        class="feed-card"
        :class="`type-${post.type}`"
      >
        <div class="card-accent"></div>
        <div class="card-inner">
          <!-- Header -->
          <div class="card-header">
            <div class="avatar" :style="{ background: post.avatarColor }">
              {{ post.avatar }}
            </div>
            <div class="card-meta">
              <div class="card-username">{{ post.username }}</div>
              <div class="card-time">{{ post.timeAgo }}</div>
            </div>
            <div class="event-badge" :class="post.type">{{ post.badgeLabel }}</div>
          </div>

          <!-- Body -->
          <div class="card-body">
            <div class="card-title">{{ post.title }}</div>
            <div class="card-text">{{ post.content }}</div>
            <div class="card-tags">
              <span v-for="tag in post.hashtags" :key="tag" class="hashtag">{{ tag }}</span>
            </div>
          </div>

          <!-- Footer -->
          <div class="card-footer">
            <button class="eng-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
              </svg>
              {{ post.likes.toLocaleString() }}
            </button>
            <button class="eng-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
              </svg>
              {{ post.comments }}
            </button>
            <button class="eng-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
              {{ post.shares }}
            </button>
            <span class="scroll-hint">scroll for more</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'TikTokFeed',
  setup() {
    const loading = ref(true)
    const posts = ref([])

    const TIME_AGO = ['just now', '1m ago', '3m ago', '7m ago', '14m ago', '28m ago', '42m ago', '1h ago', '2h ago']
    const rand = (max) => Math.floor(Math.random() * max)

    const WAREHOUSE_META = {
      'San Francisco': { user: '@catalyst_sf', color: '#7c3aed', initials: 'CS' },
      'London':        { user: '@catalyst_ldn', color: '#2563eb', initials: 'CL' },
      'Tokyo':         { user: '@catalyst_tky', color: '#dc2626', initials: 'CT' }
    }
    const DEFAULT_META = { user: '@catalyst_ops', color: '#059669', initials: 'CO' }

    const getMeta = (warehouse) => {
      if (!warehouse) return DEFAULT_META
      for (const [k, v] of Object.entries(WAREHOUSE_META)) {
        if (warehouse.includes(k)) return v
      }
      return DEFAULT_META
    }

    const buildPosts = (inventory, orders) => {
      const result = []
      let id = 0

      // Low stock (critical < 50, warning < 100)
      inventory
        .filter(item => item.quantity_on_hand < 100)
        .slice(0, 6)
        .forEach(item => {
          const meta = getMeta(item.warehouse)
          const isCritical = item.quantity_on_hand < 50
          result.push({
            id: id++,
            username: meta.user,
            avatar: meta.initials,
            avatarColor: meta.color,
            timeAgo: TIME_AGO[rand(TIME_AGO.length)],
            type: isCritical ? 'danger' : 'warning',
            badgeLabel: isCritical ? 'Critical' : 'Low Stock',
            title: `Low Stock: ${item.sku}`,
            content: `${item.name} is running low — only ${item.quantity_on_hand} units remaining. Immediate restocking recommended.`,
            likes: rand(800) + 100,
            comments: rand(40) + 5,
            shares: rand(15) + 1,
            hashtags: ['#inventory', '#lowstock', `#${(item.category || 'ops').toLowerCase().replace(/[\s/]+/g, '')}`]
          })
        })

      // Backordered
      orders
        .filter(o => o.status === 'backordered')
        .slice(0, 3)
        .forEach(order => {
          const meta = getMeta(order.warehouse)
          result.push({
            id: id++,
            username: meta.user,
            avatar: meta.initials,
            avatarColor: meta.color,
            timeAgo: TIME_AGO[rand(TIME_AGO.length)],
            type: 'danger',
            badgeLabel: 'Backordered',
            title: `Backorder: ${order.id}`,
            content: `Order ${order.id} is backordered. Replenishment required${order.customer ? ` for ${order.customer}` : ''}. Act fast!`,
            likes: rand(200) + 20,
            comments: rand(50) + 8,
            shares: rand(8) + 1,
            hashtags: ['#backorder', '#urgent', '#restock']
          })
        })

      // Shipped
      orders
        .filter(o => o.status === 'shipped')
        .slice(0, 4)
        .forEach(order => {
          const meta = getMeta(order.warehouse)
          result.push({
            id: id++,
            username: meta.user,
            avatar: meta.initials,
            avatarColor: meta.color,
            timeAgo: TIME_AGO[rand(TIME_AGO.length)],
            type: 'info',
            badgeLabel: 'Shipped',
            title: `Order Dispatched: ${order.id}`,
            content: `${order.id} is on its way${order.customer ? ` to ${order.customer}` : ''}${order.total_value ? ` — value $${Number(order.total_value).toLocaleString()}` : ''}. Estimated delivery in 2-3 days.`,
            likes: rand(400) + 50,
            comments: rand(20) + 2,
            shares: rand(10) + 1,
            hashtags: ['#shipped', '#fulfillment', '#ontheway']
          })
        })

      // Delivered
      orders
        .filter(o => o.status === 'delivered')
        .slice(0, 4)
        .forEach(order => {
          const meta = getMeta(order.warehouse)
          result.push({
            id: id++,
            username: meta.user,
            avatar: meta.initials,
            avatarColor: meta.color,
            timeAgo: TIME_AGO[rand(TIME_AGO.length)],
            type: 'success',
            badgeLabel: 'Delivered',
            title: `Confirmed Delivery: ${order.id}`,
            content: `Order ${order.id} delivered successfully${order.customer ? ` to ${order.customer}` : ''}. Another happy customer!`,
            likes: rand(600) + 80,
            comments: rand(30) + 3,
            shares: rand(12) + 1,
            hashtags: ['#delivered', '#success', '#customerwin']
          })
        })

      // Shuffle for variety
      result.sort(() => Math.random() - 0.5)
      return result
    }

    onMounted(async () => {
      try {
        const [inventory, orders] = await Promise.all([
          api.getInventory({}),
          api.getOrders({})
        ])
        posts.value = buildPosts(inventory, orders)
      } catch (err) {
        console.error('TikTokFeed: failed to load data', err)
        posts.value = []
      } finally {
        loading.value = false
      }
    })

    return { loading, posts }
  }
}
</script>

<style scoped>
.feed-wrap {
  width: 100%;
  height: 100%;
  background: #020617;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.feed-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  animation: dot-pulse 1.2s ease-in-out infinite;
}

.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50%       { opacity: 1;   transform: scale(1.2); }
}

.feed-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 14px;
}

/* ─── Scroll container ─────────────────────────────────── */
.feed-scroller {
  flex: 1;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  scrollbar-width: none;
}

.feed-scroller::-webkit-scrollbar { display: none; }

/* ─── Card ────────────────────────────────────────────── */
.feed-card {
  height: 100%;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  position: relative;
  display: flex;
  background: #0f172a;
  border-bottom: 1px solid #1e293b;
}

.card-accent {
  width: 4px;
  flex-shrink: 0;
  border-radius: 0;
}

.feed-card.type-danger  .card-accent { background: linear-gradient(to bottom, #ef4444, #b91c1c); }
.feed-card.type-warning .card-accent { background: linear-gradient(to bottom, #f59e0b, #d97706); }
.feed-card.type-success .card-accent { background: linear-gradient(to bottom, #34d399, #059669); }
.feed-card.type-info    .card-accent { background: linear-gradient(to bottom, #60a5fa, #2563eb); }

.card-inner {
  flex: 1;
  padding: 20px 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

/* ─── Header ──────────────────────────────────────────── */
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
  letter-spacing: 0.05em;
}

.card-meta {
  flex: 1;
  min-width: 0;
}

.card-username {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

.card-time {
  font-size: 11px;
  color: #475569;
  margin-top: 1px;
}

.event-badge {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.event-badge.danger  { background: rgba(239, 68, 68, 0.15);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.event-badge.warning { background: rgba(245,158,11, 0.15);   color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }
.event-badge.success { background: rgba(52, 211,153, 0.15);  color: #6ee7b7; border: 1px solid rgba(52,211,153,0.3); }
.event-badge.info    { background: rgba(96, 165,250, 0.15);  color: #93c5fd; border: 1px solid rgba(96,165,250,0.3); }

/* ─── Body ────────────────────────────────────────────── */
.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.3;
}

.card-text {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.6;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.hashtag {
  font-size: 11px;
  color: #60a5fa;
  font-weight: 500;
}

/* ─── Footer ──────────────────────────────────────────── */
.card-footer {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid #1e293b;
}

.eng-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  color: #475569;
  font-size: 12px;
  cursor: default;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: inherit;
  transition: color 0.15s;
}

.eng-btn:hover { color: #94a3b8; }

.scroll-hint {
  margin-left: auto;
  font-size: 10px;
  color: #334155;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
</style>
