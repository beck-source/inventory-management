import { ref, computed } from "vue";

const STORAGE_KEY = "app-theme";

const getInitialTheme = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") {
      return saved;
    }
  } catch (e) {
    // localStorage unavailable; fall through to system preference
  }
  try {
    if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
  } catch (e) {
    // matchMedia unavailable
  }
  return "light";
};

const applyTheme = (value) => {
  document.documentElement.setAttribute("data-theme", value);
};

const currentTheme = ref(getInitialTheme());

// Apply synchronously at module load so there is no flash of the wrong theme
applyTheme(currentTheme.value);

export function useTheme() {
  const setTheme = (value) => {
    if (value !== "light" && value !== "dark") return;
    currentTheme.value = value;
    applyTheme(value);
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch (e) {
      // ignore persistence failures
    }
  };

  const toggleTheme = () => {
    setTheme(currentTheme.value === "dark" ? "light" : "dark");
  };

  return {
    theme: computed(() => currentTheme.value),
    setTheme,
    toggleTheme,
  };
}
