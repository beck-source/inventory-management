<template>
  <!-- Dialog provides Escape-to-close, focus trap and scroll lock. -->
  <Dialog :open="isOpen" @update:open="(open) => { if (!open) close() }">
    <!-- p-0/gap-0 so header, body and footer own their padding; width/height match the old container (90vw x 85vh) -->
    <DialogContent class="sm:max-w-[90vw] w-[90%] max-h-[85vh] p-0 gap-0 overflow-hidden flex flex-col">
      <DialogHeader class="p-6 border-b border-border">
        <DialogTitle class="text-base font-semibold text-[var(--ink-primary)]">{{ t('tasks.title') }}</DialogTitle>
        <DialogDescription class="sr-only">{{ t('tasks.title') }}</DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-y-auto p-6">
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
              <Select v-model="newTask.priority">
                <SelectTrigger id="task-priority" class="w-full min-w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="high">{{ t('priority.high') }}</SelectItem>
                  <SelectItem value="medium">{{ t('priority.medium') }}</SelectItem>
                  <SelectItem value="low">{{ t('priority.low') }}</SelectItem>
                </SelectContent>
              </Select>
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
              <Button variant="default" @click="handleAddTask" :disabled="!newTask.title.trim() || !newTask.dueDate">
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
              <Button variant="destructive" size="sm" @click="$emit('delete-task', task.id)">×</Button>
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

      <DialogFooter class="p-6 border-t border-border">
        <Button variant="ghost" @click="close">{{ t('profileDetails.close') }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script>
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export default {
  name: 'TasksModal',
  components: {
    Button, Badge,
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue
  },
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

.task-input {
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

.task-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
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
</style>
