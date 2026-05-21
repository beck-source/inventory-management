import { ref, watch, nextTick, onUnmounted } from "vue";

/**
 * Modal accessibility composable.
 *
 * Wires up the four things every dialog needs and that every modal in this app was missing:
 *   1. Escape closes the dialog.
 *   2. Tab is trapped inside the dialog while it's open.
 *   3. Focus moves into the dialog on open and is restored to the previously-focused element on close.
 *   4. ARIA: the consumer should bind { ref: containerRef, ...ariaProps } on the modal container
 *      and pass a `titleId` to label the dialog by `aria-labelledby`.
 *
 * Usage:
 *   const { containerRef, ariaProps, titleId } = useModal(
 *     () => props.isOpen,
 *     () => emit('close')
 *   )
 *   // <div ref="containerRef" v-bind="ariaProps">
 *   //   <h3 :id="titleId">…</h3>
 *
 * Why this composable exists: all six modal components shipped without Escape, focus-trap, focus-restore,
 * or role="dialog". Audit-action-plan.md item #2 calls it out as Tier-1.
 */
export function useModal(isOpenGetter, closeHandler) {
  const containerRef = ref(null);
  const titleId = `modal-title-${Math.random().toString(36).slice(2, 10)}`;

  // Element to restore focus to when the dialog closes. Captured at open-time so we restore
  // to the *original* trigger even if the user moved focus around inside the dialog.
  let previousActive = null;

  const ariaProps = {
    role: "dialog",
    "aria-modal": "true",
    "aria-labelledby": titleId,
    tabindex: "-1",
  };

  const focusableSelector = [
    "a[href]",
    "button:not([disabled])",
    "textarea:not([disabled])",
    'input:not([disabled]):not([type="hidden"])',
    "select:not([disabled])",
    '[tabindex]:not([tabindex="-1"])',
  ].join(",");

  const getFocusables = () => {
    if (!containerRef.value) return [];
    return Array.from(
      containerRef.value.querySelectorAll(focusableSelector),
    ).filter((el) => !el.hasAttribute("aria-hidden"));
  };

  const onKeydown = (e) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      closeHandler();
      return;
    }
    if (e.key !== "Tab") return;

    // Focus trap: wrap Tab between first and last focusable inside the container.
    const focusables = getFocusables();
    if (focusables.length === 0) {
      e.preventDefault();
      containerRef.value?.focus();
      return;
    }
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    const active = document.activeElement;

    if (e.shiftKey && active === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && active === last) {
      e.preventDefault();
      first.focus();
    }
  };

  const activate = async () => {
    previousActive =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    document.addEventListener("keydown", onKeydown, true);
    await nextTick();
    // Move focus inside the dialog. Prefer the first focusable; otherwise focus the container itself.
    const focusables = getFocusables();
    if (focusables.length > 0) {
      focusables[0].focus();
    } else if (containerRef.value) {
      containerRef.value.focus();
    }
  };

  const deactivate = () => {
    document.removeEventListener("keydown", onKeydown, true);
    // Restore focus to whoever opened the dialog. Wrapped in a try/catch because the
    // previous element may have been removed from the DOM while the modal was open.
    try {
      previousActive?.focus();
    } catch {
      /* element gone — nothing to restore to */
    }
    previousActive = null;
  };

  watch(
    isOpenGetter,
    (open) => {
      if (open) activate();
      else deactivate();
    },
    { immediate: true },
  );

  // Defence: if the consumer unmounts while open (route change, parent v-if), make sure we
  // don't leak the keydown listener.
  onUnmounted(() => {
    document.removeEventListener("keydown", onKeydown, true);
  });

  return { containerRef, ariaProps, titleId };
}
