/** @type {import('tailwindcss').Config} */
// โทนสีองค์กร: Deep Forest Green + Warm Brass + Warm Ivory (อ่านง่าย, สไตล์ราชการ/enterprise)
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        forest: {
          50: '#eef4f0', 100: '#d3e3da', 200: '#a8c7b5', 300: '#77a78c',
          400: '#4d8a68', 500: '#2f6d4e', 600: '#245740', 700: '#1e4a35',
          800: '#173727', 900: '#112a1e', 950: '#0a1a12',
        },
        brass: {
          50: '#faf6ee', 100: '#f2e8d2', 200: '#e6cf9f', 300: '#d6b36b',
          400: '#c9a227', 500: '#b08d57', 600: '#8f6f3e', 700: '#6d5330',
        },
        ivory: { 50: '#fbf9f4', 100: '#f5f1e8', 200: '#ece5d6' },
      },
      fontFamily: {
        sans: ['Inter', 'Sarabun', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(17,42,30,0.06), 0 8px 24px rgba(17,42,30,0.10)',
      },
    },
  },
  plugins: [],
}
