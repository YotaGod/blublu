# Domain Blueprint: AnalyticsService
**Level 2 — Domain Architecture**
**Last Updated**: 2026-11-27 | **Status**: [Inferred]

## Domain Responsibility
Event aggregation, reporting dashboards, and data export pipelines.

## Modules

| Module | Path | Responsibility | Status |
| :--- | :--- | :--- | :--- |
| `AnalyticsServer` | `apps/analytics-service/src/index.js` | HTTP server + Kafka consumer | [Inferred] |
| `EventAggregator` | `apps/analytics-service/src/services/aggregator.service.js` | Event batch processing | [Inferred] |
| `ReportGenerator` | `apps/analytics-service/src/services/report.service.js` | Report generation | [Inferred] |

## Internal Dependencies
- `SharedDb` (packages/shared-db) — analytics data store

## Data Flow
Kafka Events (order.*) → EventAggregator → SharedDb → ReportGenerator
