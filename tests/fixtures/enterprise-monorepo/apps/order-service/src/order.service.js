'use strict';
const { validateToken } = require('@nexus/shared-auth');
const { KAFKA_TOPICS } = require('@nexus/shared-config');

class OrderService {
  constructor(repo, paymentClient, inventoryClient, publisher) {
    this.repo = repo;
    this.paymentClient = paymentClient;
    this.inventoryClient = inventoryClient;
    this.publisher = publisher;
  }

  async processOrder(dto) {
    const { userId, items, paymentMethodId, idempotencyKey } = dto;

    // Idempotency check
    if (idempotencyKey) {
      const existing = await this.repo.findByIdempotencyKey(idempotencyKey);
      if (existing) return existing;
    }

    // 1. Reserve inventory (MUST succeed before payment)
    const reservation = await this.inventoryClient.reserve(items);

    let charge;
    try {
      // 2. Charge payment
      charge = await this.paymentClient.charge({
        userId,
        amount: reservation.totalAmount,
        paymentMethodId,
        idempotencyKey,
      });
    } catch (err) {
      // Release reservation if payment fails
      await this.inventoryClient.release(reservation.id);
      throw err;
    }

    // 3. Create order record
    const order = await this.repo.create({
      userId,
      items,
      chargeId: charge.id,
      reservationId: reservation.id,
      status: 'confirmed',
      totalAmount: reservation.totalAmount,
      idempotencyKey,
    });

    // 4. Publish domain event (async, non-blocking)
    await this.publisher.emit(KAFKA_TOPICS.ORDER_CREATED, {
      orderId: order.id,
      userId: order.userId,
      totalAmount: order.totalAmount,
    });

    return order;
  }

  async cancelOrder(id, reason) {
    const order = await this.repo.findById(id);
    if (!order) throw new Error(`Order ${id} not found`);

    const cancellableStatuses = ['pending', 'confirmed'];
    if (!cancellableStatuses.includes(order.status)) {
      const err = new Error(`Cannot cancel order in status: ${order.status}`);
      err.name = 'OrderNotCancellableError';
      throw err;
    }

    // Release inventory reservation
    if (order.reservationId) {
      await this.inventoryClient.release(order.reservationId);
    }

    return this.repo.update(id, { status: 'cancelled', cancelReason: reason });
  }

  async getOrderStatus(id) {
    const order = await this.repo.findById(id);
    if (!order) throw new Error(`Order ${id} not found`);
    return { id: order.id, status: order.status, updatedAt: order.updatedAt };
  }

  async listOrders(userId, filters = {}) {
    return this.repo.findByUser(userId, filters);
  }
}

module.exports = { OrderService };
