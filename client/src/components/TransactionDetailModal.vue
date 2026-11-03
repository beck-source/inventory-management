<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
        v-if="isOpen && transaction"
        class="modal-overlay"
        @click="close"
        @keydown="onKeydown"
      >
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 :id="titleId" class="modal-title">
              {{ t("finance.transactionDetail.title") }}
            </h3>
            <button
              class="close-button"
              type="button"
              :aria-label="t('common.close')"
              @click="close"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M15 5L5 15M5 5L15 15"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </div>

          <dl class="modal-body">
            <div class="detail-row">
              <dt>{{ t("finance.transactions.id") }}</dt>
              <dd>{{ String(transaction.id).padStart(3, "0") }}</dd>
            </div>
            <div class="detail-row">
              <dt>{{ t("finance.transactions.description") }}</dt>
              <dd>{{ transaction.description }}</dd>
            </div>
            <div class="detail-row">
              <dt>{{ t("finance.transactions.vendor") }}</dt>
              <dd>{{ transaction.vendor }}</dd>
            </div>
            <div class="detail-row">
              <dt>{{ t("finance.transactions.date") }}</dt>
              <dd>{{ formattedDate }}</dd>
            </div>
            <div class="detail-row">
              <dt>{{ t("finance.transactions.amount") }}</dt>
              <dd class="amount">{{ formattedAmount }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from "vue";
import { useI18n } from "../composables/useI18n";
import { useModalA11y } from "../composables/useModalA11y";
import { formatCurrency } from "../utils/currency";

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  transaction: { type: Object, default: null },
});

const emit = defineEmits(["close"]);

const { t, currentCurrency, currentLocale } = useI18n();

const close = () => emit("close");
const { dialogRef, titleId, onKeydown } = useModalA11y(close);

const formattedAmount = computed(() =>
  props.transaction
    ? formatCurrency(props.transaction.amount, currentCurrency.value)
    : "",
);

const formattedDate = computed(() => {
  const date = new Date(props.transaction?.date);
  if (isNaN(date.getTime())) return props.transaction?.date || "-";
  return date.toLocaleDateString(
    currentLocale.value === "ja" ? "ja-JP" : "en-US",
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    },
  );
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: var(--surface);
  border-radius: 12px;
  box-shadow: 0 20px 50px var(--shadow-b);
  max-width: 480px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-strong);
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: var(--surface-sunken);
  color: var(--text-strong);
}

.modal-body {
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
}

.detail-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

dt {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

dd {
  color: var(--text-strong);
  font-size: 0.938rem;
  text-align: right;
  overflow-wrap: anywhere;
}

dd.amount {
  font-weight: 700;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
