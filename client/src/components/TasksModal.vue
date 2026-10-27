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
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(15, 23, 42, 0.5); /* shared overlay color */
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-md);
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.tasks-modal-container {
  max-width: 900px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-heading);
  margin: 0;
}

.close-button {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-control);
  transition: background-color 0.15s ease, color 0.15s ease;
}

.close-button:hover {
  background: var(--color-hover);
  color: var(--color-heading);
}

.close-button:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.modal-body {
  padding: var(--space-6);
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-4);
}

.btn-secondary {
  height: var(--control-height);
  padding: 0 var(--space-5);
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-control);
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-secondary:hover {
  background: var(--color-hover);
}

.btn-secondary:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

/* Task Form */
.task-form {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-5);
  margin-bottom: var(--space-6);
}

.form-row {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1;
}

.form-group.flex-1 {
  flex: 1;
}

.form-group-btn {
  display: flex;
  align-items: flex-end;
}

label {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

.task-input,
.task-select {
  height: var(--control-height);
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-control);
  font-size: var(--text-base);
  color: var(--color-text);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  font-family: inherit;
}

.task-input:focus-visible,
.task-select:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
}

.task-select {
  cursor: pointer;
  background: var(--color-surface);
}

/* Primary button: solid accent replaces the old purple gradient */
.task-add-btn {
  height: var(--control-height);
  padding: 0 var(--space-6);
  background: var(--color-accent);
  color: var(--color-surface);
  border: none;
  border-radius: var(--radius-control);
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  cursor: pointer;
  transition: opacity 0.15s ease, box-shadow 0.15s ease;
  white-space: nowrap;
}

.task-add-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.task-add-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
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
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.task-item {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-4);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.task-item:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-sm);
}

/* 4px accent stripe encodes priority; matches --space-1 */
.task-item.priority-high {
  border-left: var(--space-1) solid var(--color-danger);
}

.task-item.priority-medium {
  border-left: var(--space-1) solid var(--color-warning);
}

.task-item.priority-low {
  border-left: var(--space-1) solid var(--color-info);
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
}

.task-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--color-accent);
  flex-shrink: 0;
}

.task-title {
  flex: 1;
  cursor: pointer;
  user-select: none;
  color: var(--color-heading);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  line-height: 1.4;
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--color-text-muted);
}

.task-delete-btn {
  width: 28px;
  height: 28px;
  background: var(--color-danger-tint);
  color: var(--color-danger-text);
  border: none;
  border-radius: var(--radius-control);
  font-size: var(--text-lg);
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  flex-shrink: 0;
}

.task-delete-btn:hover {
  background: var(--color-danger);
  color: var(--color-surface);
}

.task-delete-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.task-footer {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.priority-badge {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-control);
  letter-spacing: 0.025em;
}

.priority-badge.high {
  background: var(--color-danger-tint);
  color: var(--color-danger-text);
}

.priority-badge.medium {
  background: var(--color-warning-tint);
  color: var(--color-warning-text);
}

.priority-badge.low {
  background: var(--color-info-tint);
  color: var(--color-info-text);
}

.task-due-date {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.task-due-date svg {
  color: var(--color-text-muted);
}

.status-badge {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-control);
  margin-left: auto;
}

.status-badge.overdue {
  background: var(--color-danger-tint);
  color: var(--color-danger-text);
}

.status-badge.urgent {
  background: var(--color-warning-tint);
  color: var(--color-warning-text);
}

.status-badge.upcoming {
  background: var(--color-info-tint);
  color: var(--color-info-text);
}

.status-badge.completed {
  background: var(--color-success-tint);
  color: var(--color-success-text);
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}
</style>
