# Benchpress: 3-Minute Demo Video Walkthrough Script

> **Track Target:** The Taskmaster (Grand Prize & Track Winner) • Google Cloud All Things Agentic Hackathon  
> **Format:** 3 Minutes 30 Seconds Screencast with Voiceover  
> **Target Date:** August 29–30, 2026  

---

## 🎬 Video Production Breakdown

| Timecode | Segment Name | Visual On-Screen | Voiceover Script |
|---|---|---|---|
| **0:00 - 0:40** | **The Token Price Lie** | Split screen: Provider price list showing `$0.075/1M` vs. terminal showing failed test assertions. | *"Engineering teams are adopting AI coding agents faster than ever, but picking the right model is a multi-million-dollar guessing game. Provider catalogs tell you token prices, but they don't tell you the real Cost Per Resolution. If a cheap model fails half the time, you burn tokens, retry indefinitely, and waste developer hours. What if your infrastructure could autonomously evaluate model changes, verify code with real tests, and make provable, risk-free routing decisions?"* |
| **0:40 - 1:30** | **The Autonomous Taskmaster Loop** | Terminal / Architecture Diagram showing ChangeEvent ingestion ➔ Gemini Orchestrator ➔ Cloud Tasks. | *"Enter Benchpress: the autonomous Taskmaster on Google Cloud. When Google or Anthropic drops a new model or updates reasoning knobs, Benchpress triggers an autonomous loop. First, our Gemini 3.5+ Evaluation Orchestrator fingerprints the workload and queries the catalog using structured tools. It designs a bounded, 4-task discriminating experiment and submits it to a deterministic Plan-Policy gate. Once approved, it dispatches parallel, idempotent jobs through Google Cloud Tasks."* |
| **1:30 - 2:15** | **Sandboxed Ground-Truth Execution** | Live Cloud Run worker logs showing ephemeral sandbox creation, tool turns (`view_file`, `edit_hunk`), and Pytest exit code 0. | *"On Cloud Run Gen2, workers provision isolated ephemeral worktrees. The model executes real coding tools—inspecting files and patching code hunks with strict path containment. Then, a deterministic Pytest oracle executes outside the model's reach to verify 100% test pass rates. Our failure-inclusive aggregator accounts for every cent spent across passing and failing runs, computing true Cost Per Resolution and calculating 95% Wilson Score intervals."* |
| **2:15 - 3:00** | **The Switch Decision Card & Provenance** | Browser navigating to `/decisions/exp_01J6G7R8Q9ABCDEFGHJKMNPQ20`. Pointing out Switch Decision Card, Evidence Summary, Why Not Cheapest, Replay Timeline, and 1-Click JSON Receipt. | *"Here is the live result on our web console. The hero Switch Decision Card delivers an authoritative, truth-badged verdict: SWITCH. Candidate configuration—Gemini 2.5 Pro with 2048 thinking budget—achieved a 100% resolution rate and cut Cost Per Resolution by 50%, from $0.0108 down to $0.0054 per resolved bug. Look at the 'Why Not Cheapest?' panel: it proves why Gemini Flash was eliminated—it failed 2 of 4 task assertions. The Replay Timeline shows every state transition from ingestion to publication with cryptographic SHA-256 digests."* |
| **3:00 - 3:30** | **Enterprise Governance & Conclusion** | Quick shot of Terraform manifests, BigQuery dataset, and 1-Click verified JSON receipt download. | *"Before promoting, Benchpress executed a contained canary on TASK-001. When canary guardrails passed, an atomic Compare-and-Swap promoted the active policy. If quality had regressed, it would have safely stayed on baseline. Benchpress is 100% production-ready on Google Cloud Run, Cloud Tasks, and Firestore. Stop guessing your AI agent economics. Let Benchpress automate your model governance with cryptographic certainty."* |

---

## 🎙️ Recording Checklist

1. **Resolution**: 1080p (1920x1080) at 60fps.
2. **Audio**: Clean voiceover, 48kHz, no background noise.
3. **Browser**: Chrome in Dark Mode, Zoom 100% on `/decisions/exp_01J6G7R8Q9ABCDEFGHJKMNPQ20`.
4. **Terminal**: Clean font (JetBrains Mono / Fira Code), demonstrating `scripts/verify_monorepo.sh` passing.
