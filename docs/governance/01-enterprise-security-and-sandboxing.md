# Enterprise Security, Container Isolation & gVisor Sandboxing

> **Document ID:** `BP-GOV-001`  
> **Status:** Historical target-state design — not deployed or verified
> **Target Track:** The Fortified Enterprise Fleet • Google Cloud All Things Agentic Hackathon (2026)

---

## 1. Zero-Trust Sandboxing Philosophy

Enterprise adoption of autonomous AI agent benchmarks requires executing untrusted, third-party code and multi-turn shell commands without risking:
1. **Host Kernel Compromise & Container Escapes:** Malicious benchmark tasks attempting privilege escalation or kernel exploits.
2. **Data Exfiltration & Lateral Movement:** Agents accessing internal cloud metadata endpoints (`169.254.169.254`) or VPC resources.
3. **Resource Exhaustion & Fork Bombs:** Unchecked process spawning or unbounded RAM allocation degrading node clusters.

Benchpress implements a **4-Layer Hardware & Kernel Defense Architecture** centered on Google's **gVisor (`runsc`) user-space virtualization runtime**.

```mermaid
flowchart TD
    subgraph HostNode["GCP Cloud Run Gen2 Bare-Metal Node"]
        HostKernel["Host Linux Kernel (Protected)"]
        
        subgraph gVisorSandbox["gVisor User-Space Virtualization Boundary (runsc)"]
            SentryKernel["Sentry Micro-Kernel (Intercepts all 300+ Syscalls)"]
            Gofer["Gofer VFS Interceptor (Restricted File IO)"]
            
            subgraph IsolatedExecutionEnvironment["Ephemeral Execution Namespace"]
                AgentProcess["Benchpress Agent Worker Process"]
                GitWorktree["/workspace/repo (Ephemeral tmpfs)"]
                PytestProcess["Pytest Ground-Truth Assertion Runner"]
            end
        end
        
        subgraph NetworkPerimeter["VPC Service Controls Perimeter"]
            VPCSC["VPC Service Controls"]
            PrivateGoogle["Private Google Access Only (*.googleapis.com)"]
            BlockedInternet["External Internet Egress (BLOCKED: EPERM)"]
        end
    end

    AgentProcess -->|System Call (e.g., clone, open, socket)| SentryKernel
    SentryKernel -->|Syscall Filter / Seccomp-BPF| HostKernel
    SentryKernel --> Gofer
    Gofer --> GitWorktree
    AgentProcess -.->|Network Socket Attempt| VPCSC
```

---

## 2. Kernel Isolation via gVisor (`runsc`)

Unlike standard Docker containers that share the underlying host kernel via cgroups and namespaces, Benchpress executes all code evaluation turns inside **gVisor (`runsc`)**:

- **User-Space Kernel Architecture:** gVisor provides `Sentry`, a user-space kernel written in memory-safe Go. Sentry implements the Linux system call interface directly in user space.
- **System Call Interception:** Host kernel system calls are reduced to a minimal subset (e.g., `futex`, `epoll_wait`, `read`, `write`). Dangerous syscall primitives (`ptrace`, `bpf`, `sys_chroot`, `kexec_load`) are trapped and handled entirely inside Sentry, making host kernel exploitation virtually impossible.
- **Seccomp-BPF Profile:** An immutable BPF system call filter blocks any containerized process from calling unapproved syscalls directly.

---

## 3. Linux Capability Dropping & Rootless Execution

Benchpress container execution drops all non-essential Linux capabilities by default:

```json
{
  "cap_drop": [
    "CAP_AUDIT_CONTROL",
    "CAP_AUDIT_READ",
    "CAP_AUDIT_WRITE",
    "CAP_BLOCK_SUSPEND",
    "CAP_CHOWN",
    "CAP_DAC_OVERRIDE",
    "CAP_DAC_READ_SEARCH",
    "CAP_FSETID",
    "CAP_IPC_LOCK",
    "CAP_IPC_OWNER",
    "CAP_KILL",
    "CAP_LEASE",
    "CAP_LINUX_IMMUTABLE",
    "CAP_MAC_ADMIN",
    "CAP_MAC_OVERRIDE",
    "CAP_MKNOD",
    "CAP_NET_ADMIN",
    "CAP_NET_BIND_SERVICE",
    "CAP_NET_BROADCAST",
    "CAP_NET_RAW",
    "CAP_SETGID",
    "CAP_SETFCAP",
    "CAP_SETPCAP",
    "CAP_SETUID",
    "CAP_SYS_ADMIN",
    "CAP_SYS_BOOT",
    "CAP_SYS_CHROOT",
    "CAP_SYS_MODULE",
    "CAP_SYS_NICE",
    "CAP_SYS_PACCT",
    "CAP_SYS_PTRACE",
    "CAP_SYS_RAWIO",
    "CAP_SYS_RESOURCE",
    "CAP_SYS_TIME",
    "CAP_SYS_TTY_CONFIG",
    "CAP_SYSLOG",
    "CAP_WAKE_ALARM"
  ]
}
```

---

## 4. Network Isolation & Metadata Protection

1. **Metadata Server Cloaking:**
   - The GCP metadata IP (`169.254.169.254`) is unroutable from within the sandbox namespace. Any attempt by an agent or benchmark script to fetch instance service account tokens returns an immediate connection timeout.
2. **VPC Service Controls (VPC-SC):**
   - The Cloud Run service operates strictly within a Google Cloud VPC Service Controls perimeter.
   - Outbound internet access is rejected with `EPERM`. Only cryptographically authenticated gRPC traffic to Vertex AI and BigQuery endpoints is permitted via Private Google Access.
3. **Ephemeral Worktree Life Cycle:**
   - Every task executes inside an in-memory `tmpfs` volume with a hard ceiling of $2\,\text{GB}$.
   - Upon task completion or fatal halt, the container destroys the entire worktree memory space, ensuring zero residual artifacts or cross-run contamination.
