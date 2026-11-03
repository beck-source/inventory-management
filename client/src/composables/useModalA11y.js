import { ref, watch, onBeforeUnmount } from "vue";

let uid = 0;

const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

export function useModalA11y(onClose) {
  const dialogRef = ref(null);
  const titleId = `modal-title-${++uid}`;
  let previousFocus = null;

  const getFocusable = () =>
    Array.from(dialogRef.value?.querySelectorAll(FOCUSABLE) ?? []).filter(
      (el) => el.offsetParent !== null || el === document.activeElement,
    );

  const restoreFocus = () => {
    if (previousFocus && document.contains(previousFocus))
      previousFocus.focus();
    previousFocus = null;
  };

  watch(
    dialogRef,
    (el) => {
      if (el) {
        previousFocus = document.activeElement;
        const target =
          el.querySelector("[autofocus]") || getFocusable()[0] || el;
        target.focus();
      } else {
        restoreFocus();
      }
    },
    { flush: "post" },
  );

  const onKeydown = (event) => {
    if (event.key === "Escape") {
      event.stopPropagation();
      onClose();
      return;
    }
    if (event.key !== "Tab") return;
    const items = getFocusable();
    if (!items.length) {
      event.preventDefault();
      dialogRef.value?.focus();
      return;
    }
    const first = items[0];
    const last = items[items.length - 1];
    const active = document.activeElement;
    if (event.shiftKey && (active === first || active === dialogRef.value)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  };

  onBeforeUnmount(() => {
    if (dialogRef.value) restoreFocus();
  });

  return { dialogRef, titleId, onKeydown };
}
