/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  // Class strategy lets `useTheme` toggle dark mode by adding/removing the
  // `dark` class on <html>, ignoring the OS preference except as the initial fallback.
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sia: {
          navy:     '#0A1633',
          midnight: '#000028',
          blue:     '#00B6F0',
          sky:      '#DEECFC',
          blush:    '#FFEAF0',
          slate:    '#475569',
          mist:     '#F5F7FB',
          line:     '#E2E8F0',
          // Dark-mode surfaces — extend the palette so dark variants stay on-brand.
          ink:      '#0B1220',   // app background in dark mode
          panel:    '#111A2E',   // card surface in dark mode
          border:   '#1E2A4A',   // divider/border in dark mode
        },
      },
      fontFamily: {
        sans: ['Sora', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
