# Sub-Blueprint Template: `.agents/sub-blueprints/<domain>.md`

This document defines the canonical schema for domain-specific sub-blueprints in **Codsblu v1.2.0 Distributed Mode**.
When a codebase employs distributed blueprints, the root `.agents/codebase-map.md` acts as the index, while detailed module registries and domain-specific schemas live inside `.agents/sub-blueprints/`.

> **Context-Aware Loading Rule for AI Agents**:
> Agents must NEVER load all sub-blueprints into context at once.
> Only read `.agents/sub-blueprints/<domain>.md` when the user's task or modified files directly touch this specific domain.

---

```markdown
# Domain Blueprint: [Domain Name]

> Parent Index: `../codebase-map.md`
> Maintained by **Codsblu (blublu)**. Source code is the ultimate truth.

---

## 1. Domain Overview

- **Domain Identifier**: [e.g. `billing`, `api`, `auth`, `web`]
- **Root Directory**: `[e.g. apps/api or src/modules/billing]`
- **Primary Responsibility**: [Concise 1-2 sentence description of domain capabilities]
- **Domain Dependencies**: [Other registered domains this domain imports or communicates with]

---

## 2. Domain Entry Points & Exported Contracts

Public interfaces and entry points exposed by this domain to other subsystems.

| Interface / Entry Point | File Path | Type | Consumers / Contract |
| :--- | :--- | :--- | :--- |
| Public API Router | `src/modules/billing/routes.ts` | HTTP Router | External clients via Gateway |
| Billing Service Client | `src/modules/billing/index.ts` | Service Export | Consumed by `Orders` domain |

---

## 3. Domain Module Registry

Granular component registry internal to this domain.

| Sub-Module | Path | Responsibility | Internal Dependencies | Status |
| :--- | :--- | :--- | :--- | :--- |
| `InvoiceProcessor` | `src/modules/billing/invoices.ts` | PDF invoice generation and storage | `StripeClient` | [Verified] |
| `SubscriptionManager`| `src/modules/billing/subscriptions.ts` | Plan tiers and lifecycle state machine | `InvoiceProcessor` | [Verified] |
| `StripeClient` | `src/modules/billing/stripe.ts` | Stripe SDK adapter and webhook validation | None | [Verified] |

*Status tags: `[Verified]`, `[Inferred]`, `[Unverified]`, `[Stale]`*

---

## 4. Domain Data Flows

### Flow 1: [e.g. Subscription Renewal Flow]
1. Stripe sends `invoice.paid` webhook to `src/modules/billing/webhooks.ts`.
2. Webhook handler validates signature and delegates to `SubscriptionManager`.
3. `SubscriptionManager` updates subscription expiration and calls `InvoiceProcessor.recordPayment()`.
4. Domain event `Billing.SubscriptionRenewed` dispatched.

---

## 5. Domain Database Mapping

- **Tables / Entities Owned**:
  - `billing_subscriptions`: Tracks user plan tier, Stripe customer ID, renewal dates.
  - `billing_invoices`: Ledger records of individual billing transactions.

---

## 6. Domain Business Invariants

- **Invariant 1**: Invoices cannot be deleted once marked `paid` (audit law requirement).
- **Invariant 2**: Grace period for failed credit card renewals is exactly 3 days.

---

## 7. Domain Mapping Health

- **Last Updated**: [YYYY-MM-DD HH:MM UTC]
- **Health Status**: [Healthy | Drift Detected | Needs Rebuild]
- **Verification Ratio**: [XX%]
```
