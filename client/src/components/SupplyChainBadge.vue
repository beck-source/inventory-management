<template>
  <div class="sc-badge-wrap">
    <span class="sc-badge" :class="`grade-${score.grade.toLowerCase()}`">
      ESG: {{ score.grade }}
    </span>
    <div class="sc-tooltip" role="tooltip">
      <div class="tt-header">EU Supply Chain Due Diligence (CSDDD)</div>
      <div class="tt-row">
        <span class="tt-label">Overall Grade</span>
        <span class="tt-value grade-text" :class="`grade-${score.grade.toLowerCase()}`">{{ score.grade }}</span>
      </div>
      <div class="tt-divider"></div>
      <div class="tt-row">
        <span class="tt-label">Human Rights</span>
        <span class="tt-value">{{ score.humanRights }}/100</span>
      </div>
      <div class="tt-row">
        <span class="tt-label">Environmental</span>
        <span class="tt-value">{{ score.environmental }}/100</span>
      </div>
      <div class="tt-row">
        <span class="tt-label">Labour Standards</span>
        <span class="tt-value">{{ score.labour }}/100</span>
      </div>
      <div class="tt-row">
        <span class="tt-label">Conflict Minerals</span>
        <span class="tt-value certified">{{ score.conflictMinerals }}</span>
      </div>
      <div class="tt-divider"></div>
      <div class="tt-row">
        <span class="tt-label">Last Audit</span>
        <span class="tt-value">{{ score.lastAudit }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

function charSum(str) {
  let sum = 0
  for (let i = 0; i < str.length; i++) {
    sum += str.charCodeAt(i)
  }
  return sum
}

function deriveScore(sku, category) {
  const base = charSum((sku || '') + (category || ''))

  // Deterministic scores using different moduli
  const humanRights = 50 + (base % 47)
  const environmental = 45 + ((base * 7) % 52)
  const labour = 48 + ((base * 13) % 49)
  const overall = Math.round((humanRights + environmental + labour) / 3)

  let grade
  if (overall >= 85) grade = 'A'
  else if (overall >= 72) grade = 'B'
  else if (overall >= 60) grade = 'C'
  else if (overall >= 48) grade = 'D'
  else grade = 'F'

  const auditQuarters = ['2025-Q1', '2025-Q2', '2025-Q3', '2025-Q4']
  const auditIndex = base % auditQuarters.length
  const conflictOptions = ['Certified', 'Certified', 'Pending Review', 'Certified']
  const conflictIndex = (base * 3) % conflictOptions.length

  return {
    grade,
    humanRights,
    environmental,
    labour,
    conflictMinerals: conflictOptions[conflictIndex],
    lastAudit: auditQuarters[auditIndex]
  }
}

export default {
  name: 'SupplyChainBadge',
  props: {
    sku: {
      type: String,
      default: ''
    },
    category: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const score = computed(() => deriveScore(props.sku, props.category))
    return { score }
  }
}
</script>

<style scoped>
.sc-badge-wrap {
  position: relative;
  display: inline-block;
}

.sc-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  font-size: 0.688rem;
  font-weight: 700;
  cursor: default;
  letter-spacing: 0.03em;
  white-space: nowrap;
  transition: opacity 0.15s;
}

.sc-badge-wrap:hover .sc-badge {
  opacity: 0.85;
}

/* Grade colors */
.grade-a {
  background: #d1fae5;
  color: #065f46;
}

.grade-b {
  background: #dbeafe;
  color: #1e40af;
}

.grade-c {
  background: #fef3c7;
  color: #92400e;
}

.grade-d {
  background: #fed7aa;
  color: #7c2d12;
}

.grade-f {
  background: #fecaca;
  color: #991b1b;
}

/* Tooltip */
.sc-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 8px;
  padding: 0.75rem;
  min-width: 200px;
  white-space: nowrap;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  z-index: 100;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease, transform 0.15s ease;
  transform-origin: bottom center;
}

.sc-badge-wrap:hover .sc-tooltip {
  opacity: 1;
  pointer-events: auto;
  transform: translateX(-50%) translateY(-2px);
}

.tt-header {
  font-size: 0.625rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.5rem;
}

.tt-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding: 0.2rem 0;
}

.tt-label {
  font-size: 0.75rem;
  color: #94a3b8;
}

.tt-value {
  font-size: 0.75rem;
  color: #e2e8f0;
  font-weight: 600;
}

.tt-value.certified {
  color: #6ee7b7;
}

.grade-text.grade-a { color: #6ee7b7; }
.grade-text.grade-b { color: #93c5fd; }
.grade-text.grade-c { color: #fcd34d; }
.grade-text.grade-d { color: #fb923c; }
.grade-text.grade-f { color: #f87171; }

.tt-divider {
  height: 1px;
  background: #1e293b;
  margin: 0.375rem 0;
}

/* Arrow pointing down */
.sc-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: #0f172a;
}
</style>
