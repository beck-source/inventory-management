<template>
  <div class="budget-slider">
    <div class="slider-header">
      <label>{{ label }}</label>
      <div class="slider-value">{{ formattedValue }}</div>
    </div>
    <input
      type="range"
      :min="min"
      :max="max"
      :step="step"
      :value="modelValue"
      @input="updateValue"
      class="slider-input"
    />
    <div class="slider-labels">
      <span>{{ formatCurrency(min) }}</span>
      <span>{{ formatCurrency(max) }}</span>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'BudgetSlider',
  props: {
    modelValue: {
      type: Number,
      required: true
    },
    min: {
      type: Number,
      default: 0
    },
    max: {
      type: Number,
      default: 100000
    },
    step: {
      type: Number,
      default: 1000
    },
    label: {
      type: String,
      default: 'Budget'
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const { currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const formatCurrency = (value) => {
      return `${currencySymbol.value}${value.toLocaleString()}`
    }

    const formattedValue = computed(() => {
      return formatCurrency(props.modelValue)
    })

    const updateValue = (event) => {
      emit('update:modelValue', Number(event.target.value))
    }

    return {
      formattedValue,
      formatCurrency,
      updateValue
    }
  }
}
</script>

<style scoped>
.budget-slider {
  padding: 1rem;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.slider-header label {
  font-weight: 600;
  color: #0f172a;
  font-size: 0.938rem;
}

.slider-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.025em;
}

.slider-input {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(to right, #3b82f6, #93c5fd);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider-input::-webkit-slider-thumb:hover {
  background: #1d4ed8;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.slider-input::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider-input::-moz-range-thumb:hover {
  background: #1d4ed8;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}
</style>
