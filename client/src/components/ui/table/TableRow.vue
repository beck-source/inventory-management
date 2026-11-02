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
  <tr
    data-slot="table-row"
    :class="
      cn(
        'data-[state=selected]:bg-muted transition-colors in-[tbody]:hover:bg-[var(--surface-muted)]',
        props.class,
      )
    "
  >
    <slot />
  </tr>
</template>
