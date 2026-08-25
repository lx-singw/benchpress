# ADR-008: Just-In-Time (JIT) Micro-Token Brokering, Confidential Cloud Run & eBPF Egress Defense

> **Status:** Accepted / Enterprise Standard  
> **Date:** 2026-08-22  
> **Deciders:** Principal Autonomous Systems Architect, CISO & Enterprise Security Lead  
> **Consulted:** DevOps Lead, Google Cloud Security Specialists  

---

## 1. Context & Problem Statement

Autonomous agent benchmarks execute arbitrary third-party code and multi-turn shell commands on Google Cloud infrastructure. This creates severe enterprise security risks:
1. **Static Credential Exfiltration:** If static GCP service account keys or long-lived API tokens are mounted inside container environments, a compromised or prompt-injected agent could read `/var/secrets` or inspect environment variables and exfiltrate cloud credentials.
2. **Memory Snooping & Co-Tenant Exposure:** In multi-tenant environments, memory dumps or side-channel exploits could expose sensitive source code or proprietary embeddings in RAM.
3. **Covert Outbound Network Egress:** A malicious benchmark repository could establish reverse TCP shells or DNS tunnels to exfiltrate proprietary code.

Benchpress evaluated establishing a **Zero-Trust Kernel & Hardware Defense Architecture** combining **JIT Ephemeral Credential Brokering**, **Confidential Cloud Run (AMD SEV-SNP)**, and **Linux eBPF Kernel Probes**.

---

## 2. Decision Drivers

- **Zero Static Credentials in Sandboxes:** No persistent API keys or service account tokens inside the container filesystem or environment.
- **Hardware-Level Memory Encryption:** Encrypt memory in-use to protect against hypervisor memory inspection.
- **Kernel-Level Socket Egress Blocking:** Intercept all network socket connection attempts at the Linux kernel boundary (`sys_enter_connect`).
- **Sub-10ms Credential Minting Overhead:** Token generation must not add measurable latency to model inference loops.

---

## 3. Considered Options

* **Option 1: JIT Micro-Token Broker + Confidential Cloud Run + eBPF Probes (Selected)**
  - Credential Broker uses Google Cloud IAM Security Token Service (STS) to mint short-lived ($60\text{s}$ TTL) OAuth2 micro-tokens scoped strictly to the target Vertex AI or BigQuery resource per turn.
  - Sandboxes run on Confidential Cloud Run with AMD SEV-SNP hardware memory encryption.
  - Custom eBPF C probes hook `sys_enter_connect` to terminate any rogue socket connection attempts instantly.
* **Option 2: Secret Manager Environment Variable Injection**
  - Injects long-lived API keys into container environment. Vulnerable to `printenv` inspection by agents.
* **Option 3: Standard VPC Firewall Rules Only**
  - Network-layer filtering without kernel-level socket interception or memory encryption.

---

## 4. Architectural Implementation & eBPF Kernel Probe

```mermaid
flowchart TD
    subgraph HostHardware["Confidential Cloud Run (AMD SEV-SNP Encrypted Memory)"]
        
        subgraph KernelSpace["Linux Kernel Layer (eBPF Monitored)"]
            eBPFProbe["eBPF Socket Filter: tracepoint/syscalls/sys_enter_connect"]
            SentryKernel["gVisor Sentry User-Space Kernel"]
        end

        subgraph ContainerSandbox["Sandbox Worker Namespace"]
            AgentWorker["Agent Execution Worker"]
            JITClient["JIT Micro-Token Client"]
        end

        subgraph CredentialBroker["GCP IAM Security Token Service (STS)"]
            STSBroker["JIT Credential Broker Daemon<br/>(Mints 60-Second Down-Scoped OAuth2 Tokens)"]
        end
    end

    AgentWorker -->|1. Request Micro-Token for Turn N| JITClient
    JITClient -->|2. Exchange STS Token (TTL=60s)| STSBroker
    STSBroker -->>JITClient|3. Return Ephemeral OAuth2 Token|
    JITClient -->|4. Invoke Vertex AI API| AgentWorker

    AgentWorker -.->|5. Rogue Process Attempts Socket Connect| eBPFProbe
    eBPFProbe -->|6. Intercept Syscall: Destination IP != Private Google CIDR| DropSocket["Block Egress (EPERM) & Emit SIGKILL"]
```

### eBPF Kernel Egress Filter Specification (C-style Probe)
```c
// File: benchpress/security/ebpf/egress_filter.bpf.c
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#define GOOGLE_PRIVATE_ACCESS_NET 0xC7249908 // 199.36.153.8
#define GOOGLE_PRIVATE_ACCESS_MASK 0xFFFFFFFC // /30 mask

SEC("tracepoint/syscalls/sys_enter_connect")
int handle_sys_connect(struct trace_event_raw_sys_enter *ctx) {
    struct sockaddr_in *addr = (struct sockaddr_in *)ctx->args[1];
    u32 dest_ip = addr->sin_addr.s_addr;

    // Allow only Private Google Access CIDR ranges (*.googleapis.com)
    if ((dest_ip & GOOGLE_PRIVATE_ACCESS_MASK) != GOOGLE_PRIVATE_ACCESS_NET) {
        bpf_printk("SECURITY ALERT: Blocked unauthorized egress attempt to IP: %pI4\n", &dest_ip);
        // Force process termination
        bpf_send_signal(9); // SIGKILL
        return -1; // EPERM
    }
    return 0; // ALLOW
}
char LICENSE[] SEC("license") = "GPL";
```

---

## 5. Confidential Cloud Run Configuration (Terraform HCL)

```hcl
# File: terraform/confidential_worker.tf
resource "google_cloud_run_v2_service" "confidential_sandbox_worker" {
  name     = "benchpress-confidential-worker"
  location = var.region

  template {
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    
    # Enforce AMD SEV-SNP Hardware Memory Encryption
    confidential_compute = true

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/benchpress-artifacts/sandbox-worker:latest"
      
      resources {
        limits = {
          cpu    = "4000m"
          memory = "8192Mi"
        }
      }
    }
  }
}
```

---

## 6. Decision Outcome

**Chosen Option: Option 1 (JIT Credential Broker + Confidential Cloud Run + eBPF Egress Probes).**

### Rationale:
1. **Zero Standing Privileges:** Eliminates $100\%$ of static secrets from worker containers. Tokens expire in 60 seconds, rendering memory dumps useless.
2. **Hardware Encryption:** AMD SEV-SNP ensures cryptographic isolation of RAM, preventing hypervisor and co-tenant memory inspection.
3. **Sub-Millisecond Kernel Blocking:** eBPF probe intercepts unauthorized network egress inside the kernel before TCP handshakes can initiate.
