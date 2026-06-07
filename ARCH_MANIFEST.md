# ARCH_MANIFEST.md
> **Project**: SmartSummaryPro | **Status**: Active | **Last Updated**: 2026-06-07

---
## 1. The Core Axioms
**"When the body grows, the soul must follow."**
This project follows the **GEB-Flow Architecture**.
1. **Lagged Synchronization**: Code changes trigger reverse updates to headers and meta-files.
2. **Fractal Structure**: Every directory needs `_DIR_META.md`; every file needs a Header.

---
## 2. Global Architecture (Top-Level Only)
- **/core (Kernel)**: The bedrock (Config, Quota). No business logic allowed.
- **/modules (Business Domain)**: DDD-based business logic containers (Worker).
- **/interfaces (Gateways)**: UI, Dialogs. Input/Output washing only.
- **/infrastructure (Adapters)**: API, DB Metadata. Implements core abstractions.

---
## 3. Recursive Maintenance
**This is the Source of Truth.**
> **Warning**: Do not break the chain. Local changes update local metas; Structural changes update the Manifest.
