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
  <div data-slot="table-container" class="relative w-full overflow-auto">
    <table
      data-slot="table"
      :class="cn(
        // border-collapse: preflight normally sets this; without it the browser's
        // default 2px border-spacing shows as gaps between header cells
        'w-full caption-bottom text-sm border-collapse',
        props.class,
      )"
    >
      <slot />
    </table>
  </div>
</template>
