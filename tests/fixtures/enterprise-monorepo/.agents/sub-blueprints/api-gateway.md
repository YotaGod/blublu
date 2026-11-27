# Domain Blueprint: APIGateway
**Level 2 — Domain Architecture**
**Last Updated**: 2026-11-27 | **Status**: [Inferred]

## Domain Responsibility
Reverse proxy, authentication enforcement, rate limiting, and request routing to downstream microservices.

## Modules

| Module | Path | Responsibility | Status |
| :--- | :--- | :--- | :--- |
| `GatewayServer` | `apps/api-gateway/src/index.js` | HTTP server bootstrap, middleware chain | [Verified] |
| `AuthMiddleware` | `apps/api-gateway/src/middleware/auth.js` | JWT validation, token forwarding | [Inferred] |
| `ProxyRouter` | `apps/api-gateway/src/routes/proxy.js` | Service routing rules | [Inferred] |

## Internal Dependencies
- `SharedAuth` (packages/shared-auth) — token validation

## Data Flow
Client → GatewayServer → AuthMiddleware → ProxyRouter → Downstream Services
