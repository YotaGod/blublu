# Domain Blueprint: UserService
**Level 2 — Domain Architecture**
**Last Updated**: 2026-11-27 | **Status**: [Inferred]

## Domain Responsibility
User registration, authentication, profile management, and session handling.

## Modules

| Module | Path | Responsibility | Status |
| :--- | :--- | :--- | :--- |
| `UserServer` | `apps/user-service/src/index.js` | HTTP server bootstrap | [Inferred] |
| `UserController` | `apps/user-service/src/controllers/user.controller.js` | REST endpoint handlers | [Inferred] |
| `UserService` | `apps/user-service/src/services/user.service.js` | Business logic | [Inferred] |

## Internal Dependencies
- `SharedAuth` (packages/shared-auth) — password hashing, JWT signing
- `SharedDb` (packages/shared-db) — Prisma ORM client

## Data Flow
API Gateway → UserController → UserService → SharedDb
