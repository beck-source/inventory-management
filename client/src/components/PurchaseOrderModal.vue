<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen && backlogItem"
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
        class="modal-overlay"
        @click="close"
        @keydown="onKeydown"
      >
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 :id="titleId" class="modal-title">
              {{
                mode === "create"
                  ? t("purchaseOrder.createTitle")
                  : t("purchaseOrder.detailsTitle")
              }}
            </h3>
            <button
              class="close-button"
              type="button"
              :aria-label="t('common.close')"
              @click="close"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M15 5L5 15M5 5L15 15"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-header">
              <h4 class="item-name">
                {{ translateProductName(backlogItem.item_name) }}
              </h4>
              <div class="item-sku">
                {{ t("purchaseOrder.sku") }}: {{ backlogItem.item_sku }}
              </div>
            </div>

            <div
              v-if="loading"
              class="state-message"
              role="status"
              aria-live="polite"
            >
              {{ t("common.loading") }}
            </div>
            <div v-else-if="loadError" class="state-message error" role="alert">
              {{ loadError }}
            </div>

            <!-- Create mode -->
            <form
              v-else-if="mode === 'create'"
              id="po-form"
              class="po-form"
              novalidate
              @submit.prevent="submit"
            >
              <div v-if="submitError" class="state-message error" role="alert">
                <div>{{ submitError }}</div>
                <ul v-if="summaryErrors.length" class="error-list">
                  <li v-for="msg in summaryErrors" :key="msg">{{ msg }}</li>
                </ul>
              </div>
              <div class="form-field">
                <label for="po-supplier">{{
                  t("purchaseOrder.supplierName")
                }}</label>
                <input
                  id="po-supplier"
                  v-model.trim="form.supplier_name"
                  type="text"
                  required
                  :aria-invalid="!!fieldErrors.supplier_name"
                  :aria-describedby="
                    fieldErrors.supplier_name ? 'po-supplier-error' : undefined
                  "
                />
                <div
                  v-if="fieldErrors.supplier_name"
                  id="po-supplier-error"
                  class="field-error"
                  role="alert"
                >
                  {{ fieldErrors.supplier_name }}
                </div>
              </div>
              <div class="form-row">
                <div class="form-field">
                  <label for="po-quantity">{{
                    t("purchaseOrder.quantity")
                  }}</label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    min="1"
                    step="1"
                    required
                    :aria-invalid="!!fieldErrors.quantity"
                    :aria-describedby="
                      fieldErrors.quantity ? 'po-quantity-error' : undefined
                    "
                  />
                  <div
                    v-if="fieldErrors.quantity"
                    id="po-quantity-error"
                    class="field-error"
                    role="alert"
                  >
                    {{ fieldErrors.quantity }}
                  </div>
                </div>
                <div class="form-field">
                  <label for="po-cost">{{ t("purchaseOrder.unitCost") }}</label>
                  <input
                    id="po-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    :aria-invalid="!!fieldErrors.unit_cost"
                    :aria-describedby="
                      fieldErrors.unit_cost ? 'po-cost-error' : undefined
                    "
                  />
                  <div
                    v-if="fieldErrors.unit_cost"
                    id="po-cost-error"
                    class="field-error"
                    role="alert"
                  >
                    {{ fieldErrors.unit_cost }}
                  </div>
                </div>
              </div>
              <div class="form-field">
                <label for="po-date">{{
                  t("purchaseOrder.expectedDeliveryDate")
                }}</label>
                <input
                  id="po-date"
                  v-model="form.expected_delivery_date"
                  type="date"
                  required
                  :aria-invalid="!!fieldErrors.expected_delivery_date"
                  :aria-describedby="
                    fieldErrors.expected_delivery_date
                      ? 'po-date-error'
                      : undefined
                  "
                />
                <div
                  v-if="fieldErrors.expected_delivery_date"
                  id="po-date-error"
                  class="field-error"
                  role="alert"
                >
                  {{ fieldErrors.expected_delivery_date }}
                </div>
              </div>
              <div class="form-field">
                <label for="po-notes">{{ t("purchaseOrder.notes") }}</label>
                <textarea
                  id="po-notes"
                  v-model="form.notes"
                  rows="3"
                  :aria-invalid="!!fieldErrors.notes"
                  :aria-describedby="
                    fieldErrors.notes ? 'po-notes-error' : undefined
                  "
                ></textarea>
                <div
                  v-if="fieldErrors.notes"
                  id="po-notes-error"
                  class="field-error"
                  role="alert"
                >
                  {{ fieldErrors.notes }}
                </div>
              </div>
            </form>

            <!-- View mode -->
            <div v-else-if="purchaseOrder" class="info-grid">
              <div v-for="row in viewRows" :key="row.key" class="info-item">
                <div class="info-label">{{ row.label }}</div>
                <div class="info-value">{{ row.value }}</div>
              </div>
            </div>
            <div v-else class="state-message">
              {{ t("purchaseOrder.notFound") }}
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="close">
              {{
                mode === "create"
                  ? t("purchaseOrder.cancel")
                  : t("purchaseOrder.close")
              }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              type="submit"
              form="po-form"
              :disabled="submitting"
            >
              {{
                submitting
                  ? t("purchaseOrder.creating")
                  : t("purchaseOrder.create")
              }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from "vue";
import { api } from "../api";
import { useI18n } from "../composables/useI18n";
import { useModalA11y } from "../composables/useModalA11y";

const { t, currentLocale, translateProductName } = useI18n();

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: {
    type: String,
    default: "create",
    validator: (v) => ["create", "view"].includes(v),
  },
});

const emit = defineEmits(["close", "po-created"]);

const { dialogRef, titleId, onKeydown } = useModalA11y(() => emit("close"));

const loading = ref(false);
const loadError = ref(null);
const submitting = ref(false);
const submitError = ref(null);
const purchaseOrder = ref(null);
const fieldErrors = reactive({});
const summaryErrors = ref([]);

const FIELDS = [
  "supplier_name",
  "quantity",
  "unit_cost",
  "expected_delivery_date",
  "notes",
];

const form = reactive({
  supplier_name: "",
  quantity: 1,
  unit_cost: 0,
  expected_delivery_date: "",
  notes: "",
});

const clearErrors = () => {
  FIELDS.forEach((f) => delete fieldErrors[f]);
  summaryErrors.value = [];
  submitError.value = null;
};

const validate = () => {
  const errors = {};
  if (!form.supplier_name)
    errors.supplier_name = t("purchaseOrder.validation.supplierRequired");
  if (!Number.isInteger(form.quantity) || form.quantity < 1)
    errors.quantity = t("purchaseOrder.validation.quantityInvalid");
  if (
    typeof form.unit_cost !== "number" ||
    !Number.isFinite(form.unit_cost) ||
    form.unit_cost <= 0
  ) {
    errors.unit_cost = t("purchaseOrder.validation.unitCostInvalid");
  }
  if (
    !form.expected_delivery_date ||
    isNaN(new Date(form.expected_delivery_date).getTime())
  ) {
    errors.expected_delivery_date = t("purchaseOrder.validation.dateRequired");
  }
  return errors;
};

// FastAPI returns {detail: string} or {detail: [{loc, msg}]}
const applyServerError = (err) => {
  const detail = err?.response?.data?.detail;
  submitError.value = t("purchaseOrder.createFailed");
  if (typeof detail === "string") {
    summaryErrors.value = [detail];
  } else if (Array.isArray(detail)) {
    const general = [];
    detail.forEach((item) => {
      const msg = item?.msg || (typeof item === "string" ? item : null);
      if (!msg) return;
      const field = Array.isArray(item.loc)
        ? item.loc.find((l) => FIELDS.includes(l))
        : null;
      if (field && !fieldErrors[field]) fieldErrors[field] = msg;
      else if (!field) general.push(msg);
    });
    summaryErrors.value = general;
    if (Object.keys(fieldErrors).length)
      submitError.value = t("purchaseOrder.errorSummary");
  }
};

const resetForm = () => {
  const item = props.backlogItem;
  const shortage = item
    ? (item.quantity_needed || 0) - (item.quantity_available || 0)
    : 0;
  form.supplier_name = "";
  form.quantity = Math.max(shortage, 1);
  form.unit_cost = 0;
  form.expected_delivery_date = "";
  form.notes = "";
  clearErrors();
};

const loadPO = async () => {
  loading.value = true;
  loadError.value = null;
  purchaseOrder.value = null;
  try {
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(
      props.backlogItem.id,
    );
  } catch (err) {
    loadError.value = t("purchaseOrder.loadFailed");
    console.error("Failed to load purchase order:", err);
  } finally {
    loading.value = false;
  }
};

watch(
  () => [props.isOpen, props.backlogItem?.id, props.mode],
  () => {
    if (!props.isOpen || !props.backlogItem) return;
    loadError.value = null;
    if (props.mode === "view") {
      loadPO();
    } else {
      loading.value = false;
      resetForm();
    }
  },
  { immediate: true },
);

const submit = async () => {
  clearErrors();
  const errors = validate();
  if (Object.keys(errors).length) {
    Object.assign(fieldErrors, errors);
    submitError.value = t("purchaseOrder.errorSummary");
    return;
  }
  submitting.value = true;
  try {
    const po = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name,
      quantity: form.quantity,
      unit_cost: form.unit_cost,
      expected_delivery_date: form.expected_delivery_date,
      notes: form.notes,
    });
    emit("po-created", po);
  } catch (err) {
    applyServerError(err);
    console.error("Failed to create purchase order:", err);
  } finally {
    submitting.value = false;
  }
};

const close = () => emit("close");

const formatDate = (value) => {
  if (!value) return t("purchaseOrder.na");
  const date = new Date(value);
  if (isNaN(date.getTime())) return t("purchaseOrder.na");
  return date.toLocaleDateString(
    currentLocale.value === "ja" ? "ja-JP" : "en-US",
    { year: "numeric", month: "long", day: "numeric" },
  );
};

const viewRows = computed(() => {
  const po = purchaseOrder.value;
  if (!po) return [];
  const total = (Number(po.quantity) || 0) * (Number(po.unit_cost) || 0);
  return [
    { key: "id", label: t("purchaseOrder.poNumber"), value: po.id },
    {
      key: "status",
      label: t("purchaseOrder.status"),
      value: po.status || t("purchaseOrder.na"),
    },
    {
      key: "supplier",
      label: t("purchaseOrder.supplier"),
      value: po.supplier_name,
    },
    {
      key: "quantity",
      label: t("purchaseOrder.quantity"),
      value: t("purchaseOrder.units", { count: po.quantity }),
    },
    {
      key: "unit_cost",
      label: t("purchaseOrder.unitCost"),
      value: `$${Number(po.unit_cost || 0).toFixed(2)}`,
    },
    {
      key: "total",
      label: t("purchaseOrder.totalCost"),
      value: `$${total.toFixed(2)}`,
    },
    {
      key: "delivery",
      label: t("purchaseOrder.expectedDelivery"),
      value: formatDate(po.expected_delivery_date),
    },
    {
      key: "created",
      label: t("purchaseOrder.created"),
      value: formatDate(po.created_date),
    },
    {
      key: "notes",
      label: t("purchaseOrder.notes"),
      value: po.notes || t("purchaseOrder.none"),
    },
  ];
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 600px;
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
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.item-header {
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.item-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.375rem 0;
}

.item-sku {
  font-size: 0.875rem;
  color: #64748b;
  font-family: "Monaco", "Courier New", monospace;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.form-field input,
.form-field textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
}

.form-field input:focus,
.form-field textarea:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
  border-color: #64748b;
}

.form-field input[aria-invalid="true"],
.form-field textarea[aria-invalid="true"] {
  border-color: #dc2626;
}

.field-error {
  font-size: 0.813rem;
  color: #991b1b;
}

.error-list {
  margin: 0.5rem 0 0;
  padding-left: 1.25rem;
  text-align: left;
}

.modal-container :focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.state-message {
  padding: 1rem;
  color: #64748b;
  text-align: center;
  font-size: 0.938rem;
}

.state-message.error {
  color: #991b1b;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary,
.btn-primary {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  background: #0f172a;
  border: 1px solid #0f172a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
