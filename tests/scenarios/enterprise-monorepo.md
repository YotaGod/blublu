# Test Scenarios: Enterprise Monorepo Hierarchical Navigation (v2.0.0)

This document defines the test scenarios for verifying hierarchical blueprint navigation on the enterprise monorepo fixture.

**Fixture**: `tests/fixtures/enterprise-monorepo/`
**Blueprint**: `.agents/codebase-map.md` (Level 1) + `.agents/sub-blueprints/order.md` (Level 2) + `.agents/sub-blueprints/order/order-service.md` (Level 3)

---

## Scenario 1: Initialize Blueprint on 15-Service Monorepo

**Input**: Run `codsblu init --distributed --path tests/fixtures/enterprise-monorepo` on a fresh checkout.

**Expected Agent Behavior**:
- Scans the top-level directory tree (apps/, packages/, services/, infra/).
- Groups 15 packages into ~10 logical domains.
- Creates `.agents/codebase-map.md` with all 15 sections populated.
- Section 5 Module Registry lists 10–13 high-level domain rows (not 50+ individual files).
- Section 5 Sub-Blueprints Index table is populated with 10 domain entries.
- Creates stub domain sub-blueprints in `.agents/sub-blueprints/` for each domain.

**Expected CLI Output**:
```
✔ Initialized blueprint: tests/fixtures/enterprise-monorepo/.agents/codebase-map.md
✔ Architecture Mode: Distributed
✔ Sub-blueprints created: 10
✔ Total modules tracked at Level 1: 13
```

**Pass Criteria**:
- Exit code: 0
- `.agents/codebase-map.md` exists and is non-empty.
- `.agents/sub-blueprints/` directory exists with ≥1 `.md` file.
- Level 1 token budget: Content is concise (target ≤700 tokens).
- `codsblu validate --path tests/fixtures/enterprise-monorepo` passes with exit code 0.

---

## Scenario 2: Domain-Scoped Context Loading — Order API Rate Limiting

**Input**: User prompt: *"Add rate limiting to the Order API checkout route."*

**Expected Agent Behavior**:
1. Agent reads `.agents/codebase-map.md` (Level 1).
2. Agent identifies "order" domain is touched (checkout route → Order Service).
3. Agent reads `.agents/sub-blueprints/order.md` (Level 2) ONLY.
4. Agent does NOT load `billing.md`, `user.md`, `shared-libs.md`, or any other sub-blueprint.
5. Agent finds `OrderController` → `src/controllers/order.controller.ts` and implements rate limiting there.
6. After implementation, agent updates `order.md` Section 3 (Module Registry) to reflect the new middleware.

**Expected Sub-Blueprint Load Trace**:
```
[LOAD] .agents/codebase-map.md (Level 1 — 1 file)
[IDENTIFY] Domain: order (from "Order API" in prompt)
[LOAD] .agents/sub-blueprints/order.md (Level 2 — 1 file)
[SKIP] billing.md, user.md, shared-libs.md, inventory.md, ... (not relevant)
```

**Pass Criteria**:
- Only 2 blueprint files loaded (codebase-map.md + order.md).
- Changes are made in `apps/order-service/` only.
- Blueprint update is confined to `order.md` (not codebase-map.md, unless domain boundary changed).
- Token overhead from blueprint loading: ≤1,300 tokens (Level 1 + Level 2).

---

## Scenario 3: Module-Level Context — OrderService Signature Change

**Input**: User prompt: *"Change the OrderService.processOrder() method to accept a new 'coupon_code' field."*

**Expected Agent Behavior**:
1. Agent reads `.agents/codebase-map.md` (Level 1).
2. Agent reads `.agents/sub-blueprints/order.md` (Level 2).
3. Agent identifies this is a **public interface change** (method signature alteration).
4. Agent reads `.agents/sub-blueprints/order/order-service.md` (Level 3) for the full public interface table.
5. Agent modifies `src/services/order.service.ts` and `src/services/order.service.js`.
6. After implementation, agent updates the Level 3 `processOrder` signature row in `order-service.md`.

**Expected File Load Sequence**:
```
[LOAD] .agents/codebase-map.md        (Level 1)
[LOAD] .agents/sub-blueprints/order.md (Level 2)
[IDENTIFY] Interface-level change → Load Level 3
[LOAD] .agents/sub-blueprints/order/order-service.md (Level 3)
```

**Pass Criteria**:
- 3 blueprint files loaded.
- Level 3 file `order-service.md` has updated `processOrder` signature.
- Level 2 `order.md` is NOT modified (no structural domain change occurred).
- Level 1 `codebase-map.md` is NOT modified.

---

## Scenario 4: Cross-Domain Task — Shared Auth Breaking Change

**Input**: User prompt: *"Add a new required field 'tenant_id' to the JWT payload in shared-auth."*

**Expected Agent Behavior**:
1. Agent reads `.agents/codebase-map.md` (Level 1).
2. Agent identifies "shared-libs" domain is touched (shared-auth → `packages/shared-auth`).
3. Agent reads `.agents/sub-blueprints/shared-libs.md` (Level 2).
4. Agent identifies downstream consumers: api-gateway, user-service, order-service, billing-service (all listed in the cross-domain table).
5. Agent warns user: "Breaking change — 8 services import shared-auth. All consumers must handle the new 'tenant_id' field."
6. Agent implements the change in `packages/shared-auth/src/index.js`.
7. Agent updates `shared-libs.md` to reflect the new JWT payload field.

**Expected CLI Output (codsblu validate after change)**:
```
[WARN] shared-auth interface changed. 8 downstream consumers may be affected.
       Consumers: api-gateway, user-service, order-service, billing-service, ...
       Recommendation: Run integration tests for all consumers.
```

**Pass Criteria**:
- Agent loads `shared-libs.md` (Level 2), not individual service sub-blueprints.
- Warning about downstream impact is surfaced.
- Change is confined to `packages/shared-auth/`.

---

## Scenario 5: CLI Status Command on Enterprise Fixture

**Command**: `python scripts/codsblu.py status --path tests/fixtures/enterprise-monorepo`

**Expected Output** (approximate):
```
============================================================
 Codsblu (blublu) v2.0.0 — Architecture Status
============================================================
Project Root:       tests/fixtures/enterprise-monorepo
Blueprint:          .agents/codebase-map.md
Architecture Mode:  Distributed (10 sub-blueprints)
Total Modules:      13
Verification Ratio: 46% (Initial Scan)
  - Verified:       6
  - Inferred:       5
  - Unverified:     2
  - Stale:          0
Sub-Blueprints:     10 registered, 8 missing, 0 orphaned
Health:             Healthy
------------------------------------------------------------
Background Watcher: Not running
------------------------------------------------------------
```

**Pass Criteria**:
- Exit code: 0
- Architecture Mode shows "Distributed"
- Sub-blueprint count ≥ 2 (order.md and shared-libs.md exist physically)
- No crash or traceback

---

## Regression: Backward Compatibility with v1.x Single-File Fixtures

Run the full v1.x regression suite to confirm hierarchical changes do not break existing fixtures:

```bash
python scripts/validate-blueprint.py --path tests/fixtures/simple-node-app/.agents/codebase-map.md
# Expected: ✔ PASS (Single-File), Exit 0

python scripts/validate-blueprint.py --path tests/fixtures/laravel-app/.agents/codebase-map.md
# Expected: ✔ PASS (Single-File), Exit 0

python scripts/validate-blueprint.py --path tests/fixtures/react-app/.agents/codebase-map.md
# Expected: ✔ PASS (Single-File), Exit 0

python scripts/validate-blueprint.py --path tests/fixtures/non-git-app/.agents/codebase-map.md
# Expected: ✔ PASS (Single-File), Exit 0

python scripts/validate-blueprint.py --path tests/fixtures/distributed-app/.agents/codebase-map.md --check-files --strict
# Expected: ✔ PASS (Distributed), Exit 0
```

**Pass Criteria**: All 5 fixtures pass with exit code 0. No regressions from v2.0.0 changes.
