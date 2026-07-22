<template>
  <Teleport to="body">
    <!-- Page blur overlay -->
    <div v-if="showBanner" class="gdpr-overlay"></div>

    <!-- Cookie banner -->
    <div v-if="showBanner" class="gdpr-banner" role="dialog" aria-modal="true" aria-label="Cookie consent">
      <div class="gdpr-banner-inner">
        <p class="gdpr-text">
          We use cookies to analyze usage and improve your experience. This site processes data
          as a Data Controller under GDPR Art. 6(1)(a).
        </p>
        <div class="gdpr-actions">
          <button class="btn-accept" @click="acceptAll">Accept All</button>
          <button class="btn-manage" @click="showPreferences = true">Manage Preferences</button>
          <button class="btn-reject" @click="rejectAll">Reject All</button>
        </div>
      </div>
    </div>

    <!-- Preferences modal -->
    <Transition name="modal">
      <div v-if="showPreferences" class="pref-overlay" @click.self="showPreferences = false">
        <div class="pref-modal" role="dialog" aria-modal="true" aria-label="Cookie preferences">
          <div class="pref-header">
            <h2 class="pref-title">Cookie Preferences</h2>
            <button class="pref-close" @click="showPreferences = false" aria-label="Close">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M14 4L4 14M4 4L14 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="pref-body">
            <!-- Strictly Necessary -->
            <div class="pref-row">
              <div class="pref-info">
                <div class="pref-name">
                  Strictly Necessary
                  <svg class="lock-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
                  </svg>
                </div>
                <div class="pref-desc">Required for the application to function. Cannot be disabled.</div>
              </div>
              <div class="toggle-wrap">
                <div class="toggle-track on disabled">
                  <div class="toggle-thumb"></div>
                </div>
              </div>
            </div>

            <!-- Analytics -->
            <div class="pref-row">
              <div class="pref-info">
                <div class="pref-name">Analytics</div>
                <div class="pref-desc">Help us understand how you use this dashboard.</div>
              </div>
              <div class="toggle-wrap" @click="prefs.analytics = !prefs.analytics">
                <div class="toggle-track" :class="{ on: prefs.analytics }">
                  <div class="toggle-thumb"></div>
                </div>
              </div>
            </div>

            <!-- Marketing -->
            <div class="pref-row">
              <div class="pref-info">
                <div class="pref-name">Marketing</div>
                <div class="pref-desc">Used to show relevant content.</div>
              </div>
              <div class="toggle-wrap" @click="prefs.marketing = !prefs.marketing">
                <div class="toggle-track" :class="{ on: prefs.marketing }">
                  <div class="toggle-thumb"></div>
                </div>
              </div>
            </div>

            <!-- Personalization -->
            <div class="pref-row">
              <div class="pref-info">
                <div class="pref-name">Personalization</div>
                <div class="pref-desc">Remember your preferences.</div>
              </div>
              <div class="toggle-wrap" @click="prefs.personalization = !prefs.personalization">
                <div class="toggle-track" :class="{ on: prefs.personalization }">
                  <div class="toggle-thumb"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="pref-footer">
            <button class="btn-save" @click="savePreferences">Save Preferences</button>
            <button class="btn-reject-link" @click="rejectAll">Reject All</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'

const STORAGE_KEY = 'gdpr_consent'

export default {
  name: 'GdprCookieBanner',
  setup() {
    const showBanner = ref(false)
    const showPreferences = ref(false)

    const prefs = reactive({
      analytics: true,
      marketing: false,
      personalization: true
    })

    const saveConsent = (analytics, marketing, personalization) => {
      const consent = {
        necessary: true,
        analytics,
        marketing,
        personalization,
        timestamp: new Date().toISOString()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(consent))
      showBanner.value = false
      showPreferences.value = false
    }

    const acceptAll = () => saveConsent(true, true, true)
    const rejectAll = () => saveConsent(false, false, false)
    const savePreferences = () => saveConsent(prefs.analytics, prefs.marketing, prefs.personalization)

    onMounted(() => {
      const existing = localStorage.getItem(STORAGE_KEY)
      if (!existing) {
        showBanner.value = true
      }
    })

    return { showBanner, showPreferences, prefs, acceptAll, rejectAll, savePreferences }
  }
}
</script>

<style scoped>
.gdpr-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(3px);
  z-index: 9998;
  pointer-events: none;
}

.gdpr-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #0f172a;
  border-top: 1px solid #1e293b;
  z-index: 9999;
  padding: 1.25rem 2rem;
}

.gdpr-banner-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.gdpr-text {
  flex: 1;
  font-size: 0.875rem;
  color: #cbd5e1;
  line-height: 1.5;
  min-width: 280px;
}

.gdpr-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.btn-accept {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
}

.btn-accept:hover {
  background: #1d4ed8;
}

.btn-manage {
  background: transparent;
  color: #cbd5e1;
  border: 1px solid #475569;
  padding: 0.5rem 1.125rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  font-family: inherit;
}

.btn-manage:hover {
  border-color: #94a3b8;
  color: white;
}

.btn-reject {
  background: transparent;
  color: #94a3b8;
  border: none;
  padding: 0.5rem 0.75rem;
  font-size: 0.813rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.15s;
  font-family: inherit;
}

.btn-reject:hover {
  color: #cbd5e1;
}

/* Preferences modal */
.pref-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.pref-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 520px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.pref-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.pref-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.pref-close {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
}

.pref-close:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.pref-body {
  padding: 0.5rem 0;
}

.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  gap: 1rem;
}

.pref-row:last-child {
  border-bottom: none;
}

.pref-info {
  flex: 1;
}

.pref-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.25rem;
}

.lock-icon {
  color: #94a3b8;
  flex-shrink: 0;
}

.pref-desc {
  font-size: 0.813rem;
  color: #64748b;
  line-height: 1.4;
}

.toggle-wrap {
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-wrap.disabled {
  cursor: not-allowed;
}

/* iOS-style toggle switch */
.toggle-track {
  width: 44px;
  height: 26px;
  border-radius: 13px;
  background: #d1d5db;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-track.on {
  background: #2563eb;
}

.toggle-track.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  transition: transform 0.2s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}

.toggle-track.on .toggle-thumb {
  transform: translateX(18px);
}

.pref-footer {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.btn-save {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
}

.btn-save:hover {
  background: #1d4ed8;
}

.btn-reject-link {
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 0.875rem;
  cursor: pointer;
  padding: 0.5rem;
  font-family: inherit;
  transition: color 0.15s;
}

.btn-reject-link:hover {
  color: #0f172a;
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .pref-modal,
.modal-leave-active .pref-modal {
  transition: transform 0.2s ease;
}

.modal-enter-from .pref-modal,
.modal-leave-to .pref-modal {
  transform: scale(0.96) translateY(8px);
}
</style>
