<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>{{ mode === 'view' ? 'View Purchase Order' : 'Create Purchase Order' }}</h2>
        <button class="modal-close" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body">
        <p class="coming-soon">Purchase order management coming soon.</p>
        <div v-if="backlogItem" class="backlog-info">
          <p><strong>Item:</strong> {{ backlogItem.item_name || backlogItem.sku }}</p>
          <p><strong>Shortage:</strong> {{ backlogItem.shortage_quantity }} units</p>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" @click="$emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen:      { type: Boolean, default: false },
    backlogItem: { type: Object,  default: null },
    mode:        { type: String,  default: 'create' }
  },
  emits: ['close', 'po-created']
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.4);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal {
  background: var(--surface-bg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  width: 480px;
  max-width: 90vw;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
}
.modal-header h2 { font-size: var(--text-lg); font-weight: 600; color: var(--text-primary); }
.modal-close { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--text-secondary); line-height: 1; }
.modal-body { padding: 1.25rem; }
.coming-soon { color: var(--text-secondary); font-size: var(--text-sm); margin-bottom: .75rem; }
.backlog-info { background: var(--accent-subtle); border-radius: var(--radius-sm); padding: .75rem 1rem; font-size: var(--text-sm); display: flex; flex-direction: column; gap: .25rem; }
.modal-footer { padding: .75rem 1.25rem; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end; }
</style>
