# Test Scenario 2: Incremental Diff Update

This scenario evaluates how blublu handles localized feature additions without destroying or overwriting unassociated architectural documentation.

---

## 1. Scenario Objective
Prove that adding a single service (`src/services/paymentService.js`) to an existing project:
1. Triggers an **Incremental Update** rather than a destructive full rebuild.
2. Updates only the affected rows in Section 5 (Module Registry) and Section 6 (Dependency Mapping).
3. Preserves previously verified modules (`Auth`, `User`, `Db`) without resetting them to unverified.
4. Appends a changelog entry to Section 14 (Recent Architectural Changes) and updates the timestamp in Section 15.

---

## 2. Test Setup & Pre-conditions
- **Base Fixture**: `tests/fixtures/simple-node-app`
- **Initial State**: `.agents/codebase-map.md` is present and verified.

---

## 3. Simulated Development Task

### Step 3.1: Developer Adds New Service File
Create a new file `src/services/paymentService.js`:
```javascript
// src/services/paymentService.js
const processPayment = (userId, amount) => {
  return { transactionId: "tx_123", status: "success", amount };
};

module.exports = { processPayment };
```

### Step 3.2: Wire Service into Controller
Edit `src/controllers/userController.js` to import and call `paymentService`:
```javascript
const paymentService = require("../services/paymentService");
```

### Step 3.3: Trigger Update Prompt
Prompt the agent:
> *"I added paymentService.js and imported it into userController.js. Run blublu update."*

---

## 4. Expected Assertions & Validation

### Assertion 1: Git Diff Precision
The agent must run:
```bash
git status --short
git diff --name-only
```
And identify that only `src/services/paymentService.js` and `src/controllers/userController.js` were modified.

### Assertion 2: Surgical Modification in `.agents/codebase-map.md`
- **Section 5 (Module Registry)**:
  - Appends new row:
    ```markdown
    | `PaymentService` | `src/services/paymentService.js` | Payment processing mock logic | None | [Verified] |
    ```
  - Updates `UserController` dependencies column to include `PaymentService`.
  - Untouched rows (`ServerBootstrap`, `UserRoutes`, `UserService`) remain unchanged with `[Verified]` status.
- **Section 14 (Recent Architectural Changes)**:
  - Appends current date entry: `Added PaymentService to handle checkout mock transactions.`
- **Section 15 (Mapping Health)**:
  - Updates `Last Updated` to current UTC date.
  - Updates `Total Tracked Modules` from 4 to 5.

### Assertion 3: Automated Validation
Run the validator to confirm zero regressions:
```bash
python scripts/validate-blueprint.py --path tests/fixtures/simple-node-app/.agents/codebase-map.md --check-files
```
- **Exit Code**: `0`
