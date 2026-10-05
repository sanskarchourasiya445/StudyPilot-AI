/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          blue: "#2563eb",
          "blue-hover": "#1d4ed8",
          green: "#16a34a",
          amber: "#d97706",
          red: "#dc2626",
          teal: "#0d9488",
          purple: "#9333ea",
        },
      },
      fontFamily: {
        sans: ["Inter", "Plus Jakarta Sans", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}
