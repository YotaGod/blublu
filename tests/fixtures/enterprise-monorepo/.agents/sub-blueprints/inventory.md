# Domain Blueprint: InventoryService
**Level 2 — Domain Architecture**
**Last Updated**: 2026-11-27 | **Status**: [Inferred]

## Domain Responsibility
Stock tracking, reservation management, and warehouse synchronization.

## Modules

| Module | Path | Responsibility | Status |
| :--- | :--- | :--- | :--- |
| `InventoryServer` | `apps/inventory-service/src/index.js` | HTTP server bootstrap | [Inferred] |
| `StockController` | `apps/inventory-service/src/controllers/stock.controller.js` | REST endpoint handlers | [Inferred] |
| `ReservationService` | `apps/inventory-service/src/services/reservation.service.js` | Stock reservation logic | [Inferred] |

## Internal Dependencies
- `SharedDb` (packages/shared-db) — Prisma ORM client

## Data Flow
OrderService → StockController → ReservationService → SharedDb
