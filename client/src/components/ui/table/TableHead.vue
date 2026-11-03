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
  <th
    data-slot="table-head"
    :class="
      cn(
        'px-3 py-2 text-left align-middle text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-muted)] [&:has([role=checkbox])]:pr-0 *:[[role=checkbox]]:translate-y-0.5',
        props.class,
      )
    "
  >
    <slot />
  </th>
</template>
