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
  <div
    data-slot="card"
    :class="
      cn(
        'flex flex-col gap-4 rounded-[10px] border border-[var(--line)] bg-[var(--surface-card)] p-6 text-[var(--ink-primary)]',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
