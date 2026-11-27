'use strict';
const express = require('express');
const { OrderController } = require('./controllers/order.controller');
const { OrderService } = require('./services/order.service');
const { OrderRepository } = require('./repositories/order.repository');
const { PaymentClient } = require('./clients/payment.client');
const { InventoryClient } = require('./clients/inventory.client');
const { EventPublisher } = require('./events/publisher');

const app = express();
app.use(express.json());

const repo = new OrderRepository();
const paymentClient = new PaymentClient(process.env.BILLING_SERVICE_URL);
const inventoryClient = new InventoryClient(process.env.INVENTORY_SERVICE_URL);
const publisher = new EventPublisher(process.env.KAFKA_BROKERS);
const orderService = new OrderService(repo, paymentClient, inventoryClient, publisher);
const orderController = new OrderController(orderService);

app.use('/api/orders', orderController.router());

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => {
  console.log(`Order Service listening on port ${PORT}`);
});

module.exports = { app };
