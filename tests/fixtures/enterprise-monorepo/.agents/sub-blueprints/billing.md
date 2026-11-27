# Domain Blueprint: BillingService
**Level 2 — Domain Architecture**
**Last Updated**: 2026-11-27 | **Status**: [Inferred]

## Domain Responsibility
Stripe payment processing, invoice generation, and payment record management.

## Modules

| Module | Path | Responsibility | Status |
| :--- | :--- | :--- | :--- |
| `BillingServer` | `apps/billing-service/src/index.js` | HTTP server bootstrap | [Verified] |
| `PaymentController` | `apps/billing-service/src/controllers/payment.controller.js` | Payment endpoint handlers | [Inferred] |
| `StripeClient` | `apps/billing-service/src/services/stripe.client.js` | Stripe API integration | [Inferred] |

## Internal Dependencies
- `SharedAuth` (packages/shared-auth) — request authentication
- `SharedDb` (packages/shared-db) — invoice storage
- `NotificationService` (apps/notification-service) — payment confirmation emails

## Data Flow
OrderService → PaymentController → StripeClient → Stripe API
