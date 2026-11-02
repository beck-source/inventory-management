<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ t('tasks.title') }}</h3>
            <Button variant="ghost" size="sm" @click="close">
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </Button>
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
                  <select id="task-priority" v-model="newTask.priority" class="task-select">
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
                  <Button variant="primary" @click="handleAddTask" :disabled="!newTask.title.trim() || !newTask.dueDate">
                    {{ t('tasks.addTask') }}
                  </Button>
                </div>
              </div>
            </div>

            <div class="tasks-divider"></div>

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
                  <Button variant="danger" size="sm" @click="$emit('delete-task', task.id)">×</Button>
                </div>

                <div class="task-footer">
                  <Badge :variant="task.priority === 'high' ? 'danger' : task.priority === 'medium' ? 'warn' : 'accent'">
                    {{ translatePriority(task.priority) }}
                  </Badge>
                  <div class="task-due-date">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                      <rect x="2" y="3" width="10" height="9" rx="1" stroke="currentColor" stroke-width="1.2"/>
                      <path d="M4.5 1.5V4.5M9.5 1.5V4.5M2 6H12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                    </svg>
                    {{ formatDueDate(task.dueDate) }}
                  </div>
                  <Badge :variant="getStatusVariant(task.dueDate, task.status)" class="status-badge">
                    {{ getStatusText(task.dueDate, task.status) }}
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <Button variant="ghost" @click="close">{{ t('profileDetails.close') }}</Button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import Button from './ui/Button.vue'
import Badge from './ui/Badge.vue'

export default {
  name: 'TasksModal',
  components: { Button, Badge },
  props: {
    isOpen: { type: Boolean, required: true },
    tasks: { type: Array, default: () => [] }
  },
  emits: ['close', 'add-task', 'delete-task', 'toggle-task'],
  setup(props, { emit }) {
    const { t, currentLocale } = useI18n()
    const newTask = ref({ title: '', priority: 'medium', dueDate: '' })

    const sortedTasks = computed(() => [...props.tasks])

    const close = () => emit('close')

    const handleAddTask = () => {
      if (newTask.value.title.trim() && newTask.value.dueDate) {
        emit('add-task', {
          title: newTask.value.title.trim(),
          priority: newTask.value.priority,
          dueDate: newTask.value.dueDate
        })
        newTask.value = { title: '', priority: 'medium', dueDate: '' }
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

    const getStatusVariant = (dueDate, status) => {
      if (status === 'completed') return 'success'
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const due = new Date(dueDate)
      due.setHours(0, 0, 0, 0)
      const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24))
      if (diffDays < 0) return 'danger'
      if (diffDays <= 1) return 'warn'
      return 'neutral'
    }

    const getStatusText = (dueDate, status) => {
      const isJapanese = currentLocale.value === 'ja'
      if (status === 'completed') return isJapanese ? '完了' : 'Completed'
      const variant = getStatusVariant(dueDate, status)
      if (variant === 'danger') return isJapanese ? '期限超過' : 'Overdue'
      if (variant === 'warn') return isJapanese ? 'もうすぐ期限' : 'Due Soon'
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
      getStatusVariant,
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
  background: rgba(15, 23, 42, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: var(--surface-card);
  border-radius: var(--r-lg);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  width: 90%;
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--line);
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink-primary);
  margin: 0;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 24px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Task Form */
.task-form {
  background: var(--surface-muted);
  border-radius: var(--r-md);
  padding: 24px;
  margin-bottom: 24px;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.form-group.flex-1 { flex: 1; }

.form-group-btn {
  display: flex;
  align-items: flex-end;
}

label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.task-input,
.task-select {
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  font-size: 13px;
  font-family: inherit;
  color: var(--ink-primary);
  background: var(--surface-card);
  transition: border-color 0.15s;
}

.task-input:focus,
.task-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.task-select {
  cursor: pointer;
}

.tasks-divider {
  height: 1px;
  background: var(--line);
  margin: 24px 0;
}

.no-tasks {
  text-align: center;
  padding: 48px;
  color: var(--ink-muted);
  font-size: 14px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.task-item {
  background: var(--surface-card);
  border-bottom: 1px solid var(--line);
  padding: 16px 0;
}

.task-item:last-child {
  border-bottom: none;
}

.task-item.priority-high { border-left: 3px solid var(--danger); padding-left: 12px; }
.task-item.priority-medium { border-left: 3px solid var(--warn); padding-left: 12px; }
.task-item.priority-low { border-left: 3px solid var(--accent); padding-left: 12px; }

.task-item.completed {
  opacity: 0.6;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 16px;
}

.task-check-title {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.task-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent);
  flex-shrink: 0;
}

.task-title {
  flex: 1;
  cursor: pointer;
  user-select: none;
  color: var(--ink-primary);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--ink-muted);
}

.task-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-due-date {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ink-muted);
}

.status-badge {
  margin-left: auto;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
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
