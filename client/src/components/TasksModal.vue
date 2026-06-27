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
  inset: 0;
  background: var(--uui-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--uui-z-modal);
}

.modal-container {
  background: var(--uui-surface-main);
  border-radius: var(--uui-radius-12);
  box-shadow: var(--uui-shadow-400);
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
  padding: var(--uui-space-18) var(--uui-space-24);
  border-bottom: 1px solid var(--uui-divider);
}

.modal-title {
  font-size: var(--uui-h3-size);
  font-weight: var(--uui-fw-semibold);
  color: var(--uui-text-primary);
  margin: 0;
}

.close-button {
  width: var(--uui-size-36);
  height: var(--uui-size-36);
  background: none;
  border: none;
  color: var(--uui-icon);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--uui-radius-6);
  transition: all 0.12s ease;
}

.close-button:hover {
  background: var(--uui-night-100);
  color: var(--uui-icon-active);
}

.modal-body {
  padding: var(--uui-space-24);
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: var(--uui-space-18) var(--uui-space-24);
  border-top: 1px solid var(--uui-divider);
  display: flex;
  justify-content: flex-end;
  gap: var(--uui-space-12);
}

.btn-secondary {
  height: var(--uui-size-36);
  padding: 0 var(--uui-space-18);
  background: var(--uui-night-100);
  color: var(--uui-text-primary);
  border: 1px solid var(--uui-border);
  border-radius: var(--uui-radius-6);
  font-family: var(--uui-font);
  font-weight: var(--uui-fw-semibold);
  font-size: var(--uui-text-s-size);
  cursor: pointer;
  transition: all 0.12s ease;
}

.btn-secondary:hover {
  background: var(--uui-night-200);
  border-color: var(--uui-border-strong);
}

/* Task Form */
.task-form {
  background: var(--uui-surface-lowest);
  border-radius: var(--uui-radius-12);
  padding: var(--uui-space-18);
  margin-bottom: var(--uui-space-18);
}

.form-row {
  display: flex;
  gap: var(--uui-space-12);
  margin-bottom: var(--uui-space-12);
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--uui-space-6);
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
  font-size: var(--uui-text-s-size);
  font-weight: var(--uui-fw-semibold);
  color: var(--uui-text-secondary);
}

.task-input,
.task-select {
  height: var(--uui-size-36);
  padding: 0 var(--uui-space-12);
  border: 1px solid var(--uui-control-border);
  border-radius: var(--uui-radius-6);
  font-family: var(--uui-font);
  font-size: var(--uui-text-s-size);
  color: var(--uui-control-text);
  background: var(--uui-control-bg);
  transition: border-color 0.12s, box-shadow 0.12s;
}

.task-input:focus,
.task-select:focus {
  outline: none;
  border-color: var(--uui-focus);
  box-shadow: var(--uui-shadow-focus);
}

.task-select {
  cursor: pointer;
}

.task-add-btn {
  height: var(--uui-size-36);
  padding: 0 var(--uui-space-18);
  background: var(--uui-primary);
  color: var(--uui-white);
  border: none;
  border-radius: var(--uui-radius-6);
  font-family: var(--uui-font);
  font-weight: var(--uui-fw-semibold);
  font-size: var(--uui-text-s-size);
  cursor: pointer;
  transition: background 0.12s ease;
  white-space: nowrap;
}

.task-add-btn:hover:not(:disabled) {
  background: var(--uui-primary-hover);
}

.task-add-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.tasks-divider {
  height: 1px;
  background: var(--uui-divider);
  margin: var(--uui-space-24) 0;
}

.no-tasks {
  text-align: center;
  padding: var(--uui-space-48);
  color: var(--uui-text-secondary);
  font-size: var(--uui-text-m-size);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--uui-space-12);
}

.task-item {
  background: var(--uui-surface-main);
  border: 1px solid var(--uui-border);
  border-left: 4px solid var(--uui-border);
  border-radius: var(--uui-radius-12);
  padding: var(--uui-space-12) var(--uui-space-18);
  transition: box-shadow 0.12s ease, border-color 0.12s ease;
}

.task-item:hover {
  border-color: var(--uui-border-strong);
  box-shadow: var(--uui-shadow-100);
}

.task-item.priority-high {
  border-left-color: var(--uui-fire-60);
}

.task-item.priority-medium {
  border-left-color: var(--uui-amber-60);
}

.task-item.priority-low {
  border-left-color: var(--uui-blue-60);
}

.task-item.completed {
  opacity: 0.6;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--uui-space-12);
  gap: var(--uui-space-12);
}

.task-check-title {
  display: flex;
  align-items: center;
  gap: var(--uui-space-12);
  flex: 1;
}

.task-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--uui-primary);
  flex-shrink: 0;
}

.task-title {
  flex: 1;
  cursor: pointer;
  user-select: none;
  color: var(--uui-text-primary);
  font-size: var(--uui-text-m-size);
  font-weight: var(--uui-fw-semibold);
  line-height: 1.4;
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--uui-text-tertiary);
}

.task-delete-btn {
  width: var(--uui-size-30);
  height: var(--uui-size-30);
  background: var(--uui-error-subtle);
  color: var(--uui-error);
  border: none;
  border-radius: var(--uui-radius-6);
  cursor: pointer;
  transition: all 0.12s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  flex-shrink: 0;
  font-size: 1.1rem;
}

.task-delete-btn:hover {
  background: var(--uui-error);
  color: var(--uui-white);
}

.task-footer {
  display: flex;
  align-items: center;
  gap: var(--uui-space-12);
}

.priority-badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 var(--uui-space-6);
  border-radius: var(--uui-radius-3);
  font-size: var(--uui-text-xs-size);
  font-weight: var(--uui-fw-semibold);
  text-transform: uppercase;
  letter-spacing: var(--uui-overline-tracking);
}

.priority-badge.high {
  background: var(--uui-error-subtle);
  color: var(--uui-fire-70);
}

.priority-badge.medium {
  background: var(--uui-warning-subtle);
  color: var(--uui-amber-70);
}

.priority-badge.low {
  background: var(--uui-info-subtle);
  color: var(--uui-cyan-70);
}

.task-due-date {
  display: flex;
  align-items: center;
  gap: var(--uui-space-6);
  font-size: var(--uui-text-xs-size);
  color: var(--uui-text-secondary);
}

.task-due-date svg {
  color: var(--uui-text-tertiary);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 var(--uui-space-6);
  border-radius: var(--uui-radius-3);
  font-size: var(--uui-text-xs-size);
  font-weight: var(--uui-fw-semibold);
  margin-left: auto;
}

.status-badge.overdue {
  background: var(--uui-error-subtle);
  color: var(--uui-fire-70);
}

.status-badge.urgent {
  background: var(--uui-warning-subtle);
  color: var(--uui-amber-70);
}

.status-badge.upcoming {
  background: var(--uui-info-subtle);
  color: var(--uui-cyan-70);
}

.status-badge.completed {
  background: var(--uui-success-subtle);
  color: var(--uui-green-70);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.15s ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.15s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.96);
}
</style>
