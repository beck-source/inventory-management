/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
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
        },
      },
      fontFamily: {
        sans: ['Sora', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
