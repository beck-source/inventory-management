<script setup>
import { cn } from "@/lib/utils";

const props = defineProps({
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
});
</script>

<template>
  <thead data-slot="table-header" :class="cn('border-y border-[var(--line)] bg-[var(--surface-bg)]', props.class)">
    <slot />
  </thead>
</template>
