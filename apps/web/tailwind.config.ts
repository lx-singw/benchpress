import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0A0D14",
        surface: "#121722",
        "surface-light": "#1A2234",
        "surface-border": "rgba(255, 255, 255, 0.08)",
        "cyan-electric": "#00F0FF",
        "emerald-pass": "#10B981",
        "amber-bloat": "#F59E0B",
        "crimson-fail": "#EF4444",
      },
      boxShadow: {
        "glass-cyan": "0 0 25px -5px rgba(0, 240, 255, 0.3)",
        "glass-emerald": "0 0 25px -5px rgba(16, 185, 129, 0.3)",
        "glass-amber": "0 0 25px -5px rgba(245, 158, 11, 0.3)",
        "glass-crimson": "0 0 25px -5px rgba(239, 68, 68, 0.3)",
        "glass-surface": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
