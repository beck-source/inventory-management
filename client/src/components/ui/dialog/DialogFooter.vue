<script setup>
import { cn } from "@/lib/utils";
import { DialogClose } from "reka-ui";
import { Button } from '@/components/ui/button';

const props = defineProps({
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
  showCloseButton: { type: Boolean, required: false, default: false },
});
</script>

<template>
  <div
    data-slot="dialog-footer"
    :class="
      cn('flex flex-col-reverse gap-2 sm:flex-row sm:justify-end', props.class)
    "
  >
    <slot />
    <DialogClose v-if="showCloseButton" as-child>
      <Button variant="outline"> Close </Button>
    </DialogClose>
  </div>
</template>
