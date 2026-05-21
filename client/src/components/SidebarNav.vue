<template>
  <aside
    :class="[
      'sticky top-0 h-screen bg-sia-navy text-white flex flex-col transition-[width] duration-200 ease-out flex-shrink-0',
      collapsed ? 'w-16' : 'w-64'
    ]"
  >
    <!-- Brand -->
    <div class="h-16 flex items-center gap-3 px-4 border-b border-white/10">
      <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-sia-sky to-sia-blush flex-shrink-0 flex items-center justify-center shadow-inner">
        <span class="text-sia-navy font-extrabold text-sm tracking-tight">S</span>
      </div>
      <div v-if="!collapsed" class="overflow-hidden">
        <div class="font-bold tracking-tight text-[15px] leading-tight whitespace-nowrap">{{ t('nav.companyName') }}</div>
        <div class="text-[11px] text-white/50 leading-tight whitespace-nowrap">{{ t('nav.subtitle') }}</div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto">
      <router-link
        v-for="item in items"
        :key="item.path"
        :to="item.path"
        :title="collapsed ? item.label : ''"
        class="group relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13.5px] font-medium text-white/65 hover:text-white hover:bg-white/5 transition-colors"
        :class="{ 'justify-center': collapsed }"
        active-class="!text-white !bg-white/10"
      >
        <span
          v-show="isActive(item.path)"
          class="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-r bg-sia-blue"
        />
        <component :is="item.icon" :size="19" class="flex-shrink-0" :stroke-width="1.75" />
        <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Footer / toggle -->
    <div class="border-t border-white/10 p-2">
      <button
        class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-white/55 hover:text-white hover:bg-white/5 transition"
        @click="$emit('toggle')"
      >
        <component :is="collapsed ? ChevronRight : ChevronLeft" :size="18" :stroke-width="2" />
        <span v-if="!collapsed" class="text-xs font-medium">Collapse</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  LayoutDashboard, Package, ShoppingCart, RotateCw,
  TrendingUp, Wallet, FileBarChart, ChevronLeft, ChevronRight
} from 'lucide-vue-next'
import { useI18n } from '../composables/useI18n'

defineProps({ collapsed: Boolean })
defineEmits(['toggle'])

const route = useRoute()
const { t } = useI18n()

const items = computed(() => [
  { path: '/',           label: t('nav.overview'),       icon: LayoutDashboard },
  { path: '/inventory',  label: t('nav.inventory'),      icon: Package },
  { path: '/orders',     label: t('nav.orders'),         icon: ShoppingCart },
  { path: '/restocking', label: 'Restocking',            icon: RotateCw },
  { path: '/demand',     label: t('nav.demandForecast'), icon: TrendingUp },
  { path: '/spending',   label: t('nav.finance'),        icon: Wallet },
  { path: '/reports',    label: 'Reports',               icon: FileBarChart },
])

const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path === path || route.path.startsWith(path + '/')
}

const ChevronLeftIcon = ChevronLeft
const ChevronRightIcon = ChevronRight
</script>
