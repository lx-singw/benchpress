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
        "purple-sentinel": "#8B5CF6",
        "rose-voice": "#F43F5E",
        "sky-cicd": "#38BDF8",
        obsidian: {
          950: "#06080D",
          900: "#0A0D14",
          850: "#0E131E",
          800: "#121722",
          750: "#161D2B",
          700: "#1A2234",
          600: "#242F47",
        },
      },
      boxShadow: {
        "glass-cyan": "0 0 25px -3px rgba(0, 240, 255, 0.35)",
        "glass-emerald": "0 0 25px -3px rgba(16, 185, 129, 0.35)",
        "glass-amber": "0 0 25px -3px rgba(245, 158, 11, 0.35)",
        "glass-crimson": "0 0 25px -3px rgba(239, 68, 68, 0.35)",
        "glass-purple": "0 0 25px -3px rgba(139, 92, 246, 0.35)",
        "glass-rose": "0 0 25px -3px rgba(244, 63, 94, 0.35)",
        "glass-sky": "0 0 25px -3px rgba(56, 189, 248, 0.35)",
        "glass-surface": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "sans-serif"],
      },
      animation: {
        "pulse-fast": "pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "ping-slow": "ping 2s cubic-bezier(0, 0, 0.2, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
