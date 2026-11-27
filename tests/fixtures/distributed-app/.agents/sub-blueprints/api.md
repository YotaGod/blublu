# Domain Blueprint: API

> Parent Index: `../codebase-map.md`
> Maintained by **Codsblu (blublu)**.

---

## 1. Domain Overview

- **Domain Identifier**: `api`
- **Root Directory**: `apps/api`
- **Primary Responsibility**: RESTful HTTP service handlers and API infrastructure.
- **Domain Dependencies**: None

---

## 2. Domain Entry Points & Exported Contracts

| Interface / Entry Point | File Path | Type | Consumers / Contract |
| :--- | :--- | :--- | :--- |
| Server Listener | `apps/api/server.js` | HTTP Server | Consumed by Web domain and external HTTP clients |

---

## 3. Domain Module Registry

| Sub-Module | Path | Responsibility | Internal Dependencies | Status |
| :--- | :--- | :--- | :--- | :--- |
| `Server` | `apps/api/server.js` | Bootstraps Express routes and responds to /api/health | None | [Verified] |

---

## 4. Domain Data Flows

### Flow 1: Healthcheck probe
1. Monitoring service pings `/api/health`.
2. Express handler returns 200 OK.

---

## 5. Domain Database Mapping

*N/A — In-memory service.*

---

## 6. Domain Business Invariants

- **Invariant 1**: Port 3000 default listener.

---

## 7. Domain Mapping Health

- **Last Updated**: 2026-11-27 09:20 UTC
- **Health Status**: Healthy
- **Verification Ratio**: 100%
