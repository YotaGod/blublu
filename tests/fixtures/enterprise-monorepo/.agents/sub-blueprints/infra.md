# Domain Blueprint: Infrastructure
**Level 2 — Domain Architecture**
**Last Updated**: 2026-11-27 | **Status**: [Inferred]

## Domain Responsibility
AWS infrastructure as code: ECS, RDS, ElastiCache, MSK (Kafka), S3 definitions via Terraform.

## Modules

| Module | Path | Responsibility | Status |
| :--- | :--- | :--- | :--- |
| `ECSCluster` | `infra/terraform/ecs.tf` | Fargate task definitions and services | [Inferred] |
| `RDSInstance` | `infra/terraform/rds.tf` | PostgreSQL RDS provisioning | [Inferred] |
| `MSKCluster` | `infra/terraform/msk.tf` | Managed Kafka cluster | [Inferred] |
| `S3Buckets` | `infra/terraform/s3.tf` | Static assets and backup buckets | [Inferred] |

## Internal Dependencies
- None (IaC layer, no runtime dependencies)

## Data Flow
Terraform CLI → AWS API → ECS/RDS/MSK/S3 resources
