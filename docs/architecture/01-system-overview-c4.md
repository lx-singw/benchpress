# C4 System Architecture, Autonomous Fleets & Data Topologies

> **Document ID:** `BP-ARCH-001`  
> **Status:** Approved / Production  
> **Target Track:** Best Architectural Design ($5,000) • Google Cloud All Things Agentic Hackathon (2026)

---

## 1. Architectural Philosophy & Overview

Benchpress is architected from first principles as an **event-driven, autonomous telemetry and closed-loop trajectory intelligence platform**. The system decouples interactive client surfaces from high-throughput background sandbox execution while hosting autonomous background daemons that continuously tune model routing, heal broken tool invocations, and auto-remediate CI/CD pipeline crashes.

The architecture is structured across the four standard C4 levels (Context, Container, Component, Code), ensuring unambiguous separation of concerns, high horizontal scalability on Google Cloud Platform, and millisecond-latency developer feedback loops.

---

## 2. C4 Level 1: System Context Diagram

```mermaid
C4Context
    title System Context Diagram for Benchpress Autonomous Intelligence Platform

    Person(developer, "AI Application Engineer", "Builds multi-agent workflows, configures IDE routing, and inspects auto-remediated CI PRs.")
    Person(finops, "FinOps & Engineering Leader", "Monitors AI token expenditure, models cost-per-resolution (CPR), and tracks autonomous arbitrage.")

    Enterprise_Boundary(b0, "Benchpress Platform Boundary") {
        System(benchpress, "Benchpress Intelligence Engine", "Executes multi-turn agent benchmarks, computes Cost Per Resolution (CPR), runs closed-loop canary tuning, and serves real-time model routing.")
    }

    System_Ext(vertex, "Google Cloud Vertex AI", "Provides Gemini 2.5 Pro (Supervisor & Planner), Gemini 3.5 Flash, Gemini 3.7 Flash, and Multimodal Live APIs.")
    System_Ext(external_llm, "External Model Providers", "Anthropic Claude 3.7 Sonnet, OpenAI GPT-4o, DeepSeek-R1 API endpoints.")
    System_Ext(routers, "Model Routers & IDEs", "Cursor, Windsurf, Not Diamond, and enterprise AI gateways receiving autonomous routing webhooks.")
    System_Ext(github, "GitHub Actions CI/CD", "Sends check_run webhook failures; receives verified [BENCHPRESS-AUTO] Pull Requests.")

    Rel(developer, benchpress, "Inspects trajectories, runs voice/vision diagnostics, merges auto-PRs", "HTTPS / WebRTC")
    Rel(finops, benchpress, "Analyzes CPR leaderboards, monitors token velocity governor", "HTTPS / Web")
    Rel(routers, benchpress, "Receives autonomous closed-loop routing webhook updates", "REST / Webhooks")
    Rel(github, benchpress, "Dispatches CI crash webhooks; receives automated remediated PRs", "HTTPS / Webhooks")

    Rel(benchpress, vertex, "Dispatches multi-turn prompts, tool calls, and WebRTC live audio/vision sessions", "gRPC / TLS 1.3")
    Rel(benchpress, external_llm, "Executes benchmark trajectories against baseline frontier models", "HTTPS / REST")
```

---

## 3. C4 Level 2: Container Diagram (Enhanced with Autonomous Daemons)

```mermaid
C4Container
    title Container Architecture Diagram: Benchpress Autonomous Platform on GCP

    Person(user, "User / Developer / FinOps", "Interacts via Web Browser, IDE, or CLI")
    System_Ext(github_ci, "GitHub Actions CI/CD", "Dispatches failing test webhooks")
    System_Ext(router_client, "API Consumer (Router / IDE)", "Queries routing engine & receives policy webhooks")

    Container_Boundary(c1, "Google Cloud Platform (us-central1)") {
        
        Container(cloud_armor, "Cloud Armor & Cloud Load Balancer", "WAF, DDoS Protection, TLS Termination", "Google Cloud Armor")
        
        Container(frontend_gateway, "Public Web Hub & API Gateway", "Next.js 15 App Router & FastAPI Proxy", "Cloud Run (Serverless)")
        
        Container(ci_cd_ingress, "Autonomous CI/CD Ingress Controller", "Ingests GitHub check_run webhooks, verifies HMAC, triggers auto-remediation", "Cloud Run Service")
        
        Container(canary_scheduler, "Closed-Loop Canary Scheduler", "Dispatches 6-hour drift detection swarms across holdout suites", "Cloud Tasks Cron Queue")
        
        Container(multimodal_proxy, "WebRTC Live Audio/Vision Proxy", "Duplex audio relay, DOM sync, function call router", "Cloud Run (WebSocket / WebRTC)")
        
        Container(cloud_tasks, "Taskmaster Dispatch Queues", "Rate-limiting, backoff retries, concurrency limits", "Cloud Tasks")
        
        Container(worker_fleet, "Trajectory Sandbox Worker Fleet", "Executes multi-turn agent loops within gVisor micro-sandboxes with AST Supervisor Healer", "Cloud Run Gen2 (gVisor)")
        
        ContainerDb(redis_buffer, "Telemetry Ingestion Buffer", "Micro-batches turn telemetry metrics before warehouse flush", "Memorystore Redis 7.2")
        
        ContainerDb(bigquery, "Benchpress Analytics Warehouse", "Stores raw multi-turn traces, turn tokens, tool metrics, and CPR indices", "BigQuery (Storage Write API)")
        
        ContainerDb(firestore, "Real-time State & Leaderboard Cache", "Sub-millisecond leaderboard caching and live trajectory WebSocket push", "Firestore (Native Mode)")
        
        ContainerDb(gcs, "Artifact & Trace Repository", "Stores raw git repos, diff patches, execution logs, and audio recordings", "Cloud Storage (Standard)")
    }

    System_Ext(vertex_ai, "Vertex AI / Foundation Models", "Gemini 2.5 Pro (Supervisor), Gemini 3.5 Flash (Coder), Gemini 3.7 Flash")

    Rel(user, cloud_armor, "Accesses Leaderboard, Live Voice, and Trajectory Replayer", "HTTPS / WSS")
    Rel(github_ci, cloud_armor, "POST /api/v1/webhooks/github-ci-failure", "HTTPS / Webhook")
    Rel(router_client, cloud_armor, "POST /api/v1/routing-recommendation", "HTTPS / JSON")
    
    Rel(cloud_armor, frontend_gateway, "Routes Web/API traffic", "HTTP/2")
    Rel(cloud_armor, ci_cd_ingress, "Routes GitHub webhook payloads", "HTTP/2")
    Rel(cloud_armor, multimodal_proxy, "Routes WebRTC and WebSocket media streams", "WSS / WebRTC")

    Rel(ci_cd_ingress, cloud_tasks, "Enqueues remediation trajectory run", "gRPC")
    Rel(canary_scheduler, cloud_tasks, "Dispatches scheduled canary evaluation jobs", "gRPC")
    
    Rel(cloud_tasks, worker_fleet, "Dispatches rate-controlled tasks", "HTTP POST (Push)")
    
    Rel(worker_fleet, vertex_ai, "Invokes Gemini 2.5 Pro (Supervisor/Planner) and Gemini 3.5 Flash (Coder)", "REST / gRPC")
    Rel(worker_fleet, redis_buffer, "Pushes high-frequency turn metrics", "RESP Protocol")
    Rel(worker_fleet, firestore, "Updates live step-by-step trajectory status", "gRPC")
    Rel(worker_fleet, gcs, "Uploads raw git patches, container logs, and trace artifacts", "gRPC")

    Rel(redis_buffer, bigquery, "Flushes micro-batched telemetry records every 2 seconds", "Storage Write API")
    Rel(bigquery, frontend_gateway, "Broadcasts updated Pareto routing policy webhooks", "Webhook Dispatch")
```

---

## 4. C4 Level 3: Component Diagram (Trajectory Sandbox Worker with Supervisor AST Healer)

```mermaid
C4Component
    title Component Diagram: Trajectory Sandbox Worker Instance with Autonomous Pillars

    Container_Boundary(w1, "Cloud Run Gen2 Instance (gVisor Runtime)") {
        Component(task_receiver, "Task Ingestion Controller", "FastAPI / Pydantic", "Validates Cloud Tasks payload, verifies HMAC token, initiates run lifecycle.")
        
        Component(fsm_engine, "13-State Deterministic FSM Engine", "Python Asyncio State Machine", "Enforces transitions across 13 states including Predictive Sentinel and Closed-Loop Calibration.")
        
        Component(markov_sentinel, "Predictive Budget Sentinel", "NumPy Markov Forecaster", "Evaluates Turn 5 token velocity; down-tiers model to Flash if projected cost > 2.5x median CPR.")
        
        Component(context_mgr, "Multi-Turn Context Orchestrator", "Python Tokenizer & Pruner", "Manages sliding memory windows, token compaction, and tool output pruning.")
        
        Component(hybrid_router, "2-Tier Hybrid Reasoning Engine", "Vertex AI SDK Adapter", "Dispatches planning turns to Gemini 2.5 Pro and code generation to Gemini 3.5 Flash.")
        
        Component(tool_interceptor, "AST Tool Interceptor & Validator", "Python AST & JSON Schema", "Validates tool signatures, catches duplicate schema errors, enforces security rules.")
        
        Component(supervisor_healer, "Supervisor AST Tool-Healer", "Gemini 2.5 Pro Adapter Synthesizer", "Generates dynamic Python wrapper adapters for recurring schema failures and injects into runtime.")
        
        Component(gvisor_sandbox, "Isolated Code Execution Sandbox", "gVisor + Ephemeral VFS + Git", "Executes shell commands, file edits, and pytest test harnesses in an isolated micro-sandbox.")
        
        Component(eval_assert, "Ground Truth Assertion Engine", "Pytest / AST Harness", "Executes unit tests and calculates deterministic Pass@1 status.")
        
        Component(telemetry_emitter, "Telemetry & Metric Emitter", "Redis Pipeline & GCS Uploader", "Calculates step CPR, token bloat, and streams metrics to Redis and BigQuery.")
    }

    Rel(task_receiver, fsm_engine, "Initializes trajectory state", "Internal Call")
    Rel(fsm_engine, markov_sentinel, "Evaluates token velocity at Turn 5", "Internal Call")
    Rel(fsm_engine, context_mgr, "Retrieves pruned multi-turn context", "Internal Call")
    Rel(fsm_engine, hybrid_router, "Dispatches prompt to foundation model", "gRPC / TLS")
    Rel(hybrid_router, tool_interceptor, "Receives tool call specification", "Internal Call")
    Rel(tool_interceptor, supervisor_healer, "Triggers dynamic wrapper synthesis on duplicate schema failure", "Internal Call")
    Rel(supervisor_healer, gvisor_sandbox, "Injects synthesized wrapper function into sandbox namespace", "Python exec()")
    Rel(tool_interceptor, gvisor_sandbox, "Executes validated command/code", "IPC / Process Exec")
    Rel(gvisor_sandbox, eval_assert, "Passes final git patch for ground truth verification", "File / IPC")
    Rel(eval_assert, telemetry_emitter, "Reports final resolution status and turn cost breakdown", "Internal Call")
```

---

## 5. End-to-End Sequence Diagram: Autonomous CI/CD Crash-to-PR Auto-Remediation

```mermaid
sequenceDiagram
    autonumber
    actor GitHub as GitHub Actions CI/CD
    participant Ingress as Cloud Run CI/CD Ingress
    participant CloudTasks as Cloud Tasks Queue
    participant Worker as Cloud Run Sandbox Worker
    participant Vertex as Vertex AI (Gemini 2.5/3.5)
    participant Sandbox as gVisor Container Sandbox
    participant BigQuery as BigQuery Analytics
    participant GitHubAPI as GitHub REST API (Pull Requests)

    GitHub->>Ingress: Webhook: `check_run.completed` (status="failure", test_failure_log="...")
    Ingress->>Ingress: Validate HMAC-SHA256 signature via Secret Manager
    Ingress->>CloudTasks: Enqueue Remediation Task (Repo + Commit + Error Trace)
    CloudTasks->>Worker: Dispatch HTTP Push to private Cloud Run worker

    Worker->>Sandbox: Provision gVisor container & checkout failing git commit
    Worker->>BigQuery: Vector match error trace against historical failure patterns
    BigQuery-->>Worker: Matched Strategy: 2-Tiered Hybrid (Gemini 2.5 Pro + 3.5 Flash)

    Worker->>Vertex: Turn 1 (Planner): Formulate AST bug fix strategy
    Vertex-->>Worker: Strategy Checkpoints Emitted
    Worker->>Vertex: Turns 2-3 (Coder): Execute file edits on failing module
    Vertex-->>Worker: AST patch applied in sandbox

    Worker->>Sandbox: Run pytest ground-truth assertion harness
    Sandbox-->>Worker: Pytest Result: 18 Passed, 0 Failed (Exit Code 0)

    Worker->>GitHubAPI: POST /repos/{owner}/{repo}/pulls
    Note over Worker,GitHubAPI: Opens PR tagged [BENCHPRESS-AUTO] with patch diff + unit-test logs + CPR report ($0.024 spend)
    Worker->>BigQuery: Stream completed remediation telemetry via Storage Write API
    Worker-->>CloudTasks: HTTP 200 OK (Remediation Task Complete)
```
