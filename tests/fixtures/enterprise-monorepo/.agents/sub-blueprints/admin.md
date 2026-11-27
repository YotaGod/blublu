# Domain Blueprint: AdminDashboard
**Level 2 — Domain Architecture**
**Last Updated**: 2026-11-27 | **Status**: [Inferred]

## Domain Responsibility
Internal operations UI for order management, user administration, and inventory oversight.

## Modules

| Module | Path | Responsibility | Status |
| :--- | :--- | :--- | :--- |
| `AdminApp` | `apps/admin-dashboard/src/index.js` | Next.js app entrypoint | [Inferred] |
| `OrdersPage` | `apps/admin-dashboard/src/pages/orders.jsx` | Order management view | [Inferred] |
| `UsersPage` | `apps/admin-dashboard/src/pages/users.jsx` | User admin view | [Inferred] |

## Internal Dependencies
- `APIGateway` (apps/api-gateway) — all data via gateway

## Data Flow
Admin Browser → AdminApp → APIGateway → Downstream Services
