<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="close">
        <div class="modal-container tasks-modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ t('tasks.title') }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Add Task Form -->
            <div class="task-form">
              <div class="form-row">
                <div class="form-group flex-1">
                  <label for="task-title">{{ t('tasks.taskTitle') }}</label>
                  <input
                    id="task-title"
                    v-model="newTask.title"
                    type="text"
                    :placeholder="t('tasks.taskTitlePlaceholder')"
                    class="task-input"
                    @keyup.enter="handleAddTask"
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="task-priority">{{ t('tasks.priority') }}</label>
                  <select
                    id="task-priority"
                    v-model="newTask.priority"
                    class="task-select"
                  >
                    <option value="high">{{ t('priority.high') }}</option>
                    <option value="medium">{{ t('priority.medium') }}</option>
                    <option value="low">{{ t('priority.low') }}</option>
                  </select>
                </div>

                <div class="form-group">
                  <label for="task-due-date">{{ t('tasks.dueDate') }}</label>
                  <input
                    id="task-due-date"
                    v-model="newTask.dueDate"
                    type="date"
                    class="task-input"
                  />
                </div>

                <div class="form-group-btn">
                  <button @click="handleAddTask" class="task-add-btn" :disabled="!newTask.title.trim() || !newTask.dueDate">
                    {{ t('tasks.addTask') }}
                  </button>
                </div>
              </div>
            </div>

            <div class="tasks-divider"></div>

            <!-- Tasks List -->
            <div v-if="sortedTasks.length === 0" class="no-tasks">
              {{ t('tasks.noTasks') }}
            </div>

            <div v-else class="tasks-list">
              <div
                v-for="task in sortedTasks"
                :key="task.id"
                class="task-item"
                :class="[`priority-${task.priority}`, { completed: task.status === 'completed' }]"
              >
                <div class="task-header">
                  <div class="task-check-title">
                    <input
                      type="checkbox"
                      :checked="task.status === 'completed'"
                      @change="$emit('toggle-task', task.id)"
                      class="task-checkbox"
                    />
                    <span class="task-title" @click="$emit('toggle-task', task.id)">{{ task.title }}</span>
                  </div>
                  <button @click="$emit('delete-task', task.id)" class="task-delete-btn" title="Delete task">
                    ×
                  </button>
                </div>

                <div class="task-footer">
                  <span class="priority-badge" :class="task.priority">
                    {{ translatePriority(task.priority) }}
                  </span>
                  <div class="task-due-date">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                      <rect x="2" y="3" width="10" height="9" rx="1" stroke="currentColor" stroke-width="1.2"/>
                      <path d="M4.5 1.5V4.5M9.5 1.5V4.5M2 6H12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                    </svg>
                    {{ formatDueDate(task.dueDate) }}
                  </div>
                  <span class="status-badge" :class="getStatusClass(task.dueDate, task.status)">
                    {{ getStatusText(task.dueDate, task.status) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">{{ t('profileDetails.close') }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'TasksModal',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    },
    tasks: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close', 'add-task', 'delete-task', 'toggle-task'],
  setup(props, { emit }) {
    const { t, currentLocale } = useI18n()
    const newTask = ref({
      title: '',
      priority: 'medium',
      dueDate: ''
    })

    const sortedTasks = computed(() => {
      // Don't sort - just return tasks in their current order (newest first)
      return [...props.tasks]
    })

    const close = () => {
      emit('close')
    }

    const handleAddTask = () => {
      if (newTask.value.title.trim() && newTask.value.dueDate) {
        emit('add-task', {
          title: newTask.value.title.trim(),
          priority: newTask.value.priority,
          dueDate: newTask.value.dueDate
        })
        newTask.value = {
          title: '',
          priority: 'medium',
          dueDate: ''
        }
      }
    }

    const formatDueDate = (dateString) => {
      const date = new Date(dateString)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const dueDate = new Date(date)
      dueDate.setHours(0, 0, 0, 0)

      const diffTime = dueDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      const isJapanese = currentLocale.value === 'ja'

      if (diffDays === 0) return isJapanese ? '今日' : 'today'
      if (diffDays === 1) return isJapanese ? '明日' : 'tomorrow'
      if (diffDays === -1) return isJapanese ? '昨日' : 'yesterday'
      if (diffDays < 0) return isJapanese ? `${Math.abs(diffDays)}日前` : `${Math.abs(diffDays)} days ago`
      if (diffDays < 7) return isJapanese ? `${diffDays}日後` : `in ${diffDays} days`

      const locale = isJapanese ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
      })
    }

    const getStatusClass = (dueDate, status) => {
      if (status === 'completed') return 'completed'

      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const due = new Date(dueDate)
      due.setHours(0, 0, 0, 0)

      const diffTime = due - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) return 'overdue'
      if (diffDays <= 1) return 'urgent'
      return 'upcoming'
    }

    const getStatusText = (dueDate, status) => {
      const isJapanese = currentLocale.value === 'ja'

      if (status === 'completed') return isJapanese ? '完了' : 'Completed'

      const statusClass = getStatusClass(dueDate, status)
      if (statusClass === 'overdue') return isJapanese ? '期限超過' : 'Overdue'
      if (statusClass === 'urgent') return isJapanese ? 'もうすぐ期限' : 'Due Soon'
      return isJapanese ? '予定' : 'Upcoming'
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    return {
      t,
      newTask,
      sortedTasks,
      close,
      handleAddTask,
      formatDueDate,
      getStatusClass,
      getStatusText,
      translatePriority
    }
  }
}
</script>

<style scoped>
/* Overlay: position, top/left and z-index (1000) are unchanged so the modal stays
   above the sidebar (100) and topbar (90). Padding is the viewport gutter, which
   keeps the panel off the screen edges at 390px. */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
}

/* Panel. 900px is the wide tasks variant (the old 90% width is replaced by the
   overlay gutter). overflow: hidden clips the children to the rounded corners. */
.modal-container {
  width: min(700px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  /* Deeper than --shadow-md on purpose: the panel floats over the dimmed page. */
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
}

.tasks-modal-container {
  width: min(900px, 100%);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  flex-shrink: 0;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
  margin: 0;
}

.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.close-button:hover {
  background: var(--color-subtle);
  color: var(--color-text);
}

.close-button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.modal-body {
  flex: 1;
  /* min-height: 0 lets the body shrink inside the max-height panel, so it
     scrolls and the header and footer stay in view. */
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-6);
}

.modal-footer {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-6);
  border-top: 1px solid var(--color-border);
}

/* Secondary button: bordered surface, so it reads as an action without competing with primary. */
.btn-secondary {
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-soft);
  cursor: pointer;
  transition: background-color var(--transition-fast), border-color var(--transition-fast);
}

.btn-secondary:hover {
  background: var(--color-bg);
  border-color: var(--color-border-strong);
}

.btn-secondary:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Task Form */
.task-form {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  margin-bottom: var(--space-6);
}

/* flex-wrap lets priority, due date and the Add button stack on a 390px screen. */
.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.form-row:last-child {
  margin-bottom: 0;
}

/* The 140px basis is what triggers the wrap above; min-width: 0 stops inputs from overflowing. */
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1 1 140px;
  min-width: 0;
}

.form-group.flex-1 {
  flex: 1;
}

.form-group-btn {
  display: flex;
  align-items: flex-end;
}

label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-soft);
}

.task-input,
.task-select {
  width: 100%;
  min-height: 40px;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-size: 0.9375rem;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  font-family: inherit;
}

.task-input:focus,
.task-select:focus {
  outline: none;
  border-color: var(--color-primary);
  /* Ring replaces the removed outline; 3px is the conventional focus-ring width, not a spacing value. */
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.task-select {
  cursor: pointer;
}

/* Primary button: flat brand colour, no gradient or lift animation. */
.task-add-btn {
  min-height: 40px;
  padding: var(--space-2) var(--space-5);
  background: var(--color-primary);
  color: var(--color-surface);
  border: none;
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition-fast), box-shadow var(--transition-fast);
  white-space: nowrap;
  height: fit-content;
}

/* Hover darkens via a filter because the tokens have no darker primary. */
.task-add-btn:hover:not(:disabled) {
  filter: brightness(0.92);
}

.task-add-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.task-add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tasks-divider {
  height: 1px;
  background: var(--color-border);
  margin: var(--space-6) 0;
}

.no-tasks {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-muted);
  font-size: 1rem;
  font-style: italic;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.task-item {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.task-item:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-sm);
}

/* The 4px left bar encodes priority; the amber has no token, so it stays literal. */
.task-item.priority-high {
  border-left: 4px solid var(--color-danger);
}

.task-item.priority-medium {
  border-left: 4px solid #f59e0b;
}

.task-item.priority-low {
  border-left: 4px solid var(--color-primary);
}

.task-item.completed {
  opacity: 0.6;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-3);
  gap: var(--space-4);
}

.task-check-title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
}

.task-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--color-primary);
  flex-shrink: 0;
}

.task-title {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
  cursor: pointer;
  user-select: none;
  color: var(--color-text);
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.4;
}

/* Muted slate for finished tasks; #94a3b8 is lighter than any text token, which is the point. */
.task-item.completed .task-title {
  text-decoration: line-through;
  color: #94a3b8;
}

.task-delete-btn {
  width: 28px;
  height: 28px;
  background: var(--color-danger);
  color: var(--color-surface);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  transition: filter var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  flex-shrink: 0;
}

.task-delete-btn:hover {
  filter: brightness(0.92);
}

.task-delete-btn:focus-visible {
  outline: 2px solid var(--color-danger);
  outline-offset: 2px;
}

/* wrap so the badges drop to a second line on narrow screens instead of overflowing. */
.task-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3) var(--space-4);
}

.priority-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  letter-spacing: 0.025em;
}

/* Badge text colours (#991b1b, #92400e, #1e40af, #065f46) and the light blue
   (#dbeafe) have no token, so they stay literal. */
.priority-badge.high {
  background: var(--color-danger-soft);
  color: #991b1b;
}

.priority-badge.medium {
  background: var(--color-warning-soft);
  color: #92400e;
}

.priority-badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.task-due-date {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.8125rem;
  color: var(--color-muted);
}

.task-due-date svg {
  color: #94a3b8;
}

/* margin-left: auto pushes the status to the right edge when it shares a line. */
.status-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  margin-left: auto;
}

.status-badge.overdue {
  background: var(--color-danger-soft);
  color: #991b1b;
}

.status-badge.urgent {
  background: var(--color-warning-soft);
  color: #92400e;
}

.status-badge.upcoming {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.completed {
  background: var(--color-success-soft);
  color: #065f46;
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-fast);
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--transition-fast);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
