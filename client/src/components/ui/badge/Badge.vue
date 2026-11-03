<script setup>
import { reactiveOmit } from "@vueuse/core";
import { cn } from "@/lib/utils";
import { Primitive } from "reka-ui";
import { badgeVariants } from ".";

const props = defineProps({
  asChild: { type: Boolean, required: false },
  // span by default: badges sit inline in table cells and text, like the old ui/Badge.vue
  as: { type: null, required: false, default: "span" },
  variant: { type: null, required: false },
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
});

// variant only feeds badgeVariants(); omit it so it is not rendered as a DOM attribute
const delegatedProps = reactiveOmit(props, "class", "variant");
</script>

<template>
  <Primitive
    data-slot="badge"
    :class="cn(badgeVariants({ variant }), props.class)"
    v-bind="delegatedProps"
  >
    <slot />
  </Primitive>
</template>
