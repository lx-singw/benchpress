# Official Hackathon Final Submission Checklist & Release Guide

> **Project Name:** Benchpress 🏋️‍♂️  
> **Tagline:** The Independent Economic & Trajectory Intelligence Platform for AI Agents & Model Routing  
> **Competition:** Google Cloud All Things Agentic Hackathon (2026)  
> **Target Prizes:**
> 1. **Grand Prize & Venture-Grade Platform**
> 2. **Best Architectural Design** ($5,000 USD + $1,000 GCP Credits)
> 3. **Best Multimodal UX** ($5,000 USD + $1,000 GCP Credits)
> 4. **Primary Track:** The Taskmaster (Event-driven asynchronous fleets, Cloud Tasks & BigQuery telemetry)
> 5. **Secondary Track:** The Fortified Enterprise Fleet (Enterprise security, VPC-SC, and CMEK governance)

---

## 📋 1. Devpost Submission Field Verification

| Devpost Field | Submission Value / Asset | Verified Status |
| :--- | :--- | :--- |
| **Project Title** | `Benchpress` | ✅ Verified |
| **Tagline** | `The Independent Economic & Trajectory Intelligence Platform for AI Agents & Model Routing` | ✅ Verified |
| **Repository URL** | `https://github.com/lx-singw/benchpress` | ✅ Public & Verified |
| **Video Demo URL** | 3-minute YouTube/Vimeo walkthrough following `docs/hackathon/02-demo-video-script.md` | ✅ Cue Sheet Ready |
| **Primary Track** | `The Taskmaster` (Event-driven asynchronous agent fleets) | ✅ Confirmed |
| **Target Bonuses** | `Best Architectural Design` & `Best Multimodal UX` | ✅ Confirmed |

---

## 🎬 2. Video Recording Cue Sheet (3 Minutes)

- **[0:00 - 0:30] Hook & Problem Statement:** The $85\%$ AI inference cost crisis in multi-turn coding agents; why Pass@1 alone is financially deceptive.
- **[0:30 - 1:15] Architecture & gVisor Sandbox Fleet:** Cloud Tasks async queue, 13-State Deterministic FSM, gVisor `runsc` containment, and Protobuf streaming to BigQuery.
- **[1:15 - 2:00] Tri-Modal Multimodal UX:** Sub-200ms Gemini Live WebRTC duplex voice debugging, OCR screenshot error dropzone, and Obsidian Dark Glassmorphism Pareto frontier.
- **[2:00 - 2:40] Autonomous Self-Governance & Healing:** AST Tool-Healer dynamic wrapper injection, Markov Turn-5 token velocity sentinel, and CI/CD crash-to-PR auto-remediation daemon.
- **[2:40 - 3:00] Enterprise Governance & Conclusion:** 1-Click VPC-SC/CMEK appliance, anti-contamination canary injector, and trajectory fine-tuning distillation.

---

## 🧪 3. Quality Gate & Test Suite Audit

```bash
# Execute full monorepo quality and test gate
bash scripts/verify_monorepo.sh
```

- **Monorepo Build:** 4/4 packages built cleanly (`web`, `@benchpress/sdk`, `@benchpress/telemetry`, `@benchpress/distillation`).
- **Next.js 15 Routes:** 12/12 static and dynamic routes compiled without errors.
- **Pytest Suite:** 45+ tests passing with 100% green coverage across Worker, SDK, Enterprise, Autonomous, E2E, and Chaos suites.
- **Security Audit:** Zero committed credentials or private API keys; DLP PII masking and cryptographic provenance signing active.
