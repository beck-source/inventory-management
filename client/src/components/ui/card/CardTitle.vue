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
  <h3
    data-slot="card-title"
    :class="cn('text-sm leading-normal font-normal text-[var(--ink-primary)]', props.class)"
  >
    <slot />
  </h3>
</template>
