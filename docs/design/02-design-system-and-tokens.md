# Design System, Obsidian Dark Glassmorphism & Token Specification

> **Document ID:** `BP-UX-002`  
> **Status:** Approved / Production  
> **Target Track:** Best Multimodal UX ($5,000) • Google Cloud All Things Agentic Hackathon (2026)

---

## 1. Visual Aesthetic & Philosophy

Benchpress is designed for elite software engineers, systems architects, and FinOps leaders who live in dark IDEs and high-density terminal dashboards. The visual system embodies **Obsidian Dark Glassmorphism**—a deep, low-luminance canvas accented by translucent glass panels, subtle backdrop blurs ($12-24\,\text{px}$), ultra-thin border strokes ($1\,\text{px}$ at $10\%$ opacity), and vibrant neon functional highlights.

---

## 2. Comprehensive Token Palette (Tailwind & CSS Variables)

```css
/* File: src/styles/tokens.css */
:root {
  /* Surface & Background Hierarchy */
  --bg-obsidian-deep: #0A0D14;       /* Primary canvas background */
  --bg-obsidian-surface: #121722;    /* Card and table surfaces */
  --bg-obsidian-overlay: rgba(18, 23, 34, 0.75); /* Glass panels with blur */
  --border-subtle: rgba(255, 255, 255, 0.08);    /* Glass borders */
  --border-active: rgba(0, 240, 255, 0.35);      /* Focused active element */

  /* Functional Status Accents */
  --accent-cyan: #00F0FF;            /* Active agent reasoning loops & WebRTC voice */
  --accent-cyan-glow: rgba(0, 240, 255, 0.25);
  
  --status-pass-emerald: #10B981;    /* Verified Pass@1, CPR cost savings */
  --status-pass-glow: rgba(16, 185, 129, 0.20);
  
  --status-warn-amber: #F59E0B;      /* Trajectory bloat, self-healing retries */
  --status-warn-glow: rgba(245, 158, 11, 0.20);
  
  --status-fail-crimson: #EF4444;    /* Assertion failure, circuit-breaker tripped */
  --status-fail-glow: rgba(239, 68, 68, 0.25);

  /* Typography Colors */
  --text-primary: #F9FAFB;           /* 98% Bright White */
  --text-secondary: #9CA3AF;         /* Muted slate text */
  --text-tertiary: #4B5563;          /* Disabled / metadata text */
  --text-code-cyan: #38BDF8;         /* AST syntax & JSON keys */
}
```

### Tailwind CSS Configuration (`tailwind.config.js`)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        obsidian: {
          deep: '#0A0D14',
          surface: '#121722',
          card: 'rgba(18, 23, 34, 0.85)',
          border: 'rgba(255, 255, 255, 0.08)',
        },
        cyan: {
          neon: '#00F0FF',
          muted: '#0284C7',
        },
        emerald: {
          growth: '#10B981',
        },
        amber: {
          alert: '#F59E0B',
        },
        crimson: {
          fail: '#EF4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glass-cyan': '0 0 25px -5px rgba(0, 240, 255, 0.3)',
        'glass-emerald': '0 0 25px -5px rgba(16, 185, 129, 0.25)',
        'glass-crimson': '0 0 25px -5px rgba(239, 68, 68, 0.3)',
      },
      backdropBlur: {
        xs: '4px',
        glass: '16px',
      }
    },
  },
  plugins: [],
};
```

---

## 3. Typography & Iconography Hierarchy

| Hierarchy Level | Font Family | Size / Weight | Letter Spacing | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Display Heading (H1)** | `Outfit` / `Inter` | $32\text{px}$ / SemiBold (600) | $-0.025\text{em}$ | Dashboard Hero Titles, Benchmark Summaries |
| **Section Heading (H2)** | `Outfit` / `Inter` | $20\text{px}$ / Medium (500) | $-0.015\text{em}$ | Panel Headers, Metric Group Titles |
| **Body Text** | `Inter` | $14\text{px}$ / Regular (400) | $0.0\text{em}$ | Explanatory text, descriptions, table rows |
| **Telemetry & Code** | `JetBrains Mono` | $12\text{px} - 13\text{px}$ / Medium | $+0.02\text{em}$ | Stack traces, diffs, CPR values, JSON schemas |

**Iconography:** Standardized on `lucide-react` with a stroke width of $1.75\,\text{px}$ and uniform size tokens (`h-4 w-4` for table metadata, `h-5 w-5` for primary navigation).

---

## 4. Micro-Animations & Motion Design (Framer Motion)

Benchpress utilizes fluid physics-based spring animations to convey state changes and live telemetry flows:

```typescript
// Framer Motion Spring Presets
export const glassSpring = {
  type: "spring",
  stiffness: 300,
  damping: 30,
};

export const pulseGlowAnimation = {
  initial: { opacity: 0.6, scale: 0.98 },
  animate: {
    opacity: [0.6, 1, 0.6],
    scale: [0.98, 1.01, 0.98],
    transition: {
      duration: 2.2,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
};
```

### Motion Design Rules:
1. **Active Reasoning State:** Pulsing Electric Cyan halo (`--accent-cyan-glow`) around the active trajectory node during model inference.
2. **Audio Waveform Visualizer:** 32-bar dynamic frequency visualizer driven in real-time by the incoming WebRTC audio PCM stream.
3. **Draggable Pareto Transition:** Smooth cubic bezier curve recalculation when manipulating slider weights (`transition: all 400ms cubic-bezier(0.16, 1, 0.3, 1)`).

---

## 5. Sound Design & Haptic Feedback Specifications

To enhance the multimodal experience without cluttering the audio environment, Benchpress includes optional subtle audio feedback cues synthesized via Web Audio API:

| Event Trigger | Audio Frequency / Waveform | Volume | Perceptual Meaning |
| :--- | :--- | :--- | :--- |
| **Task Verified (Pass@1)** | $880\,\text{Hz} \rightarrow 1760\,\text{Hz}$ Sine Chime (Duration: $120\text{ms}$) | $-18\,\text{dB}$ | Success, test passed, cost logged. |
| **Circuit-Breaker Tripped** | $220\,\text{Hz} \rightarrow 110\,\text{Hz}$ Sawtooth Drop (Duration: $200\text{ms}$) | $-14\,\text{dB}$ | Budget warning, runaway loop halted. |
| **Voice Agent Connected** | Soft dual-tone $520\,\text{Hz} / 650\,\text{Hz}$ harmonic chime | $-20\,\text{dB}$ | WebRTC audio stream established. |
| **Screenshot Ingested** | Tactile camera shutter click sound | $-22\,\text{dB}$ | Vision OCR parsing initiated. |
