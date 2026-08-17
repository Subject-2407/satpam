/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        satpam: {
          ink: "#172033",
          muted: "#65758B",
          line: "#D8E0EA",
          panel: "#F8FAFC",
          blue: "#2563EB",
          cyan: "#0891B2",
          amber: "#B45309",
          red: "#B91C1C",
          green: "#047857"
        }
      }
    }
  },
  plugins: [],
};
