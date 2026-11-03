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
  background: var(--red-bg);
  border: 1px solid var(--red-soft);
  color: var(--red-text);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-size: 0.938rem;
}

.retry-button {
  padding: 0.4rem 1rem;
  background: var(--surface);
  border: 1px solid var(--red-soft);
  border-radius: 6px;
  color: var(--red-text);
  font-size: 0.813rem;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  flex-shrink: 0;
}

.retry-button:hover {
  background: var(--red-soft);
}

.retry-button:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}
</style>
