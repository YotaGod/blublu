# Domain Blueprint: NotificationService
**Level 2 — Domain Architecture**
**Last Updated**: 2026-11-27 | **Status**: [Inferred]

## Domain Responsibility
Email, SMS, and push notification delivery via SendGrid and Twilio.

## Modules

| Module | Path | Responsibility | Status |
| :--- | :--- | :--- | :--- |
| `NotificationServer` | `apps/notification-service/src/index.js` | HTTP server + event consumer | [Inferred] |
| `EmailProvider` | `apps/notification-service/src/providers/email.provider.js` | SendGrid integration | [Inferred] |
| `SmsProvider` | `apps/notification-service/src/providers/sms.provider.js` | Twilio integration | [Inferred] |

## Internal Dependencies
- None (leaf service, event-driven)

## Data Flow
Kafka Events (order.created, payment.confirmed) → NotificationServer → EmailProvider / SmsProvider
