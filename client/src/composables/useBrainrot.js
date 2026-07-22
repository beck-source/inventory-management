import { ref } from 'vue'

const brainrotEnabled = ref(false)

export function useBrainrot() {
  const toggle = () => {
    brainrotEnabled.value = !brainrotEnabled.value
  }

  return { brainrotEnabled, toggle }
}
