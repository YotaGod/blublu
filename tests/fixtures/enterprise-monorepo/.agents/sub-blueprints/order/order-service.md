# Module Blueprint: OrderService [Level 3]

> **blublu Architecture Level**: Level 3 — Module Architecture
> Load this file ONLY when making interface-level or contract-breaking changes to OrderService.
> For general order domain work, use `.agents/sub-blueprints/order.md` (Level 2) instead.

---

## 1. Module Identity

- **Name**: OrderService
- **Domain**: Order
- **Path**: `apps/order-service/src/services/order.service.ts`
- **Type**: Core Business Logic Service
- **Status**: [Verified] — 2026-11-27
- **Verified By**: blublu v2.0.0

---

## 2. Entry Points & Bootstrap

- Instantiated at `apps/order-service/src/index.js:14`:
  ```js
  const orderService = new OrderService(repo, paymentClient, inventoryClient, publisher);
  ```
- Dependencies are constructor-injected (dependency injection pattern).
- No global singletons; all dependencies are passed explicitly.

---

## 3. Public Interface

| Symbol | Signature | Description |
| :--- | :--- | :--- |
| `processOrder` | `processOrder(dto: CreateOrderDto): Promise<Order>` | Full checkout orchestration: reserve inventory → charge payment → create order → emit event |
| `cancelOrder` | `cancelOrder(id: string, reason: string): Promise<Order>` | Cancels a pending or confirmed order; releases inventory reservation |
| `getOrderStatus` | `getOrderStatus(id: string): Promise<OrderStatus>` | Returns lightweight status object (id, status, updatedAt) |
| `listOrders` | `listOrders(userId: string, filters: OrderFilters): Promise<Order[]>` | Returns paginated order history for a user |

### Type Definitions

```typescript
interface CreateOrderDto {
  userId: string;
  items: Array<{ productId: string; quantity: number }>;
  paymentMethodId: string;
}

interface OrderStatus {
  id: string;
  status: 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  updatedAt: Date;
}

interface OrderFilters {
  status?: string;
  limit?: number;
  offset?: number;
  fromDate?: Date;
}
```

---

## 4. Local Dependencies (within Order domain)

| Dependency | Import Path | Usage |
| :--- | :--- | :--- |
| `OrderRepository` | `../repositories/order.repository` | Persist and query order records |
| `PaymentClient` | `../clients/payment.client` | Charge customer via billing-service |
| `InventoryClient` | `../clients/inventory.client` | Reserve stock via inventory-service |
| `ShippingClient` | `../clients/shipping.client` | Create shipping label (Inferred — not yet inspected) |
| `EventPublisher` | `../events/publisher` | Emit Kafka domain events |

---

## 5. Cross-Domain Dependencies

| Target | Type | Evidence | Confidence |
| :--- | :--- | :--- | :--- |
| `@nexus/shared-auth` | `lib` | `import { validateToken } from '@nexus/shared-auth'` at line 5 | Confirmed |
| `@nexus/shared-config` | `lib` | `import { KAFKA_TOPICS } from '@nexus/shared-config'` at line 6 | Confirmed |

---

## 6. Database Entities Owned

| Table | Columns | Description |
| :--- | :--- | :--- |
| `orders` | `id, user_id, status, total_amount, charge_id, reservation_id, cancel_reason, created_at, updated_at` | Master order records with lifecycle status |
| `order_items` | `id, order_id, product_id, quantity, unit_price` | Line items per order |

---

## 7. Business Invariants (Critical Rules)

1. **Atomic checkout**: Inventory reservation MUST succeed before payment is charged. If payment fails, reservation is released immediately.
2. **Cancellation guard**: Orders in `shipped` or `delivered` status cannot be cancelled. The `cancelOrder` method throws `OrderNotCancellableError` for these states.
3. **Idempotency**: `processOrder` accepts an optional `idempotencyKey`; duplicate submissions return the existing order without re-charging.

---

## 8. Verification Metadata

- **Last Verified**: 2026-11-27
- **Verified By**: blublu v2.0.0 (blublu)
- **Verification Method**: Direct source file inspection (`apps/order-service/src/order.service.js`)
- **Next Review Trigger**: Any change to `processOrder`, `cancelOrder`, or the orders/order_items schema
