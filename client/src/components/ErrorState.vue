<template>
  <div v-if="loading" class="loading" role="status" aria-live="polite">
    {{ t("common.loading") }}
  </div>
  <div v-else-if="message" class="error error-state" role="alert">
    <span class="error-message">{{ message }}</span>
    <button
      v-if="retryable"
      class="retry-button"
      type="button"
      @click="$emit('retry')"
    >
      {{ t("common.retry") }}
    </button>
  </div>
</template>

<script setup>
import { computed, getCurrentInstance } from "vue";
import { useI18n } from "../composables/useI18n";

defineProps({
  message: { type: String, default: "" },
  loading: { type: Boolean, default: false },
});

defineEmits(["retry"]);

const { t } = useI18n();

const instance = getCurrentInstance();
const retryable = computed(() => !!instance?.vnode.props?.onRetry);
</script>

<style scoped>
.error-state {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.retry-button {
  padding: 0.4rem 1rem;
  background: white;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #991b1b;
  font-size: 0.813rem;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  flex-shrink: 0;
}

.retry-button:hover {
  background: #fee2e2;
}

.retry-button:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>
