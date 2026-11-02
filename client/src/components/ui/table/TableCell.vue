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
  <td
    data-slot="table-cell"
    :class="
      cn(
        'h-11 border-t border-[var(--surface-muted)] p-3 align-middle text-[13px] text-[var(--ink-secondary)] [&:has([role=checkbox])]:pr-0 *:[[role=checkbox]]:translate-y-0.5',
        props.class,
      )
    "
  >
    <slot />
  </td>
</template>
