# Codebase Blueprint: Malformed Mermaid Fixture

> Auto-generated and maintained by **blublu**. Source code is the ultimate truth.

---

## 1. Project Overview

- **Name**: malformed-mermaid-fixture
- **Core Purpose**: Deliberately corrupted Mermaid diagram fixture for testing the Codsblu v1.1.0 validator.
- **Primary Tech Stack**: Node.js
- **Target Platform**: Node.js
- **Repository Pattern**: Monolith

---

## 2. Entry Points

| Entry Point | File Path | Type | Purpose / Trigger |
| :--- | :--- | :--- | :--- |
| Index | `index.js` | Bootstrap | App entry point |

---

## 3. Directory Structure

```
malformed-mermaid/
├── index.js
└── package.json
```

---

## 4. Architecture Overview

- **Architectural Style**: Monolith

---

## 5. Module Registry

| Module | Path | Responsibility | Dependencies | Status |
| :--- | :--- | :--- | :--- | :--- |
| `App` | `index.js` | Root application | `AuthService` | [Verified] |
| `AuthService` | `src/auth.js` | Authentication helper | None | [Verified] |

---

## 6. Dependency Mapping

```mermaid
graph TD
    App[index.js -> AuthService["src/auth.js"]
    AuthService -> UserDb["src/db.js"]
```

---

## 7. Main Data Flows

### Flow 1: Auth flow
1. App calls AuthService.

---

## 8. API Mapping

*N/A — Test fixture.*

---

## 9. Database Mapping

*N/A — Test fixture.*

---

## 10. External Integrations

*N/A — Test fixture.*

---

## 11. Project Conventions

- Standard JS conventions.

---

## 12. Important Business Rules

- None.

---

## 13. Known Limitations & Technical Debt

- Broken Mermaid diagram in Section 6.

---

## 14. Recent Architectural Changes

- **2026-11-27**: Created malformed Mermaid test fixture.

---

## 15. Mapping Health

- **Last Updated**: 2026-11-27 09:10 UTC
- **Agent / Tool**: blublu v1.1.0
- **Health Status**: Healthy
- **Total Tracked Modules**: 2
- **Verification Ratio**: 100%
