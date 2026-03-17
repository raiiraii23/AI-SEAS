/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        engaged:    "#22c55e",
        neutral:    "#64748b",
        confused:   "#f59e0b",
        disengaged: "#ef4444",
      },
    },
  },
  plugins: [],
};
