import { ref } from 'vue'

const isOpen = ref(false)
const actionDescription = ref('')
const pendingAction = ref(null)

export function useWorksCouncil() {
  const requireApproval = (description, onOverride) => {
    actionDescription.value = description
    pendingAction.value = onOverride
    isOpen.value = true
  }

  const handleOverride = () => {
    if (pendingAction.value) pendingAction.value()
    isOpen.value = false
    pendingAction.value = null
  }

  const handleClose = () => {
    isOpen.value = false
    pendingAction.value = null
  }

  return { isOpen, actionDescription, requireApproval, handleOverride, handleClose }
}
