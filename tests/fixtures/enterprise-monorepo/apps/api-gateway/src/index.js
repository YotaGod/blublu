'use strict';
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { requireAuth } = require('@nexus/shared-auth');

const app = express();

const SERVICES = {
  USER_SERVICE:      process.env.USER_SERVICE_URL      || 'http://user-service:3001',
  ORDER_SERVICE:     process.env.ORDER_SERVICE_URL     || 'http://order-service:3002',
  INVENTORY_SERVICE: process.env.INVENTORY_SERVICE_URL || 'http://inventory-service:3003',
  BILLING_SERVICE:   process.env.BILLING_SERVICE_URL   || 'http://billing-service:3004',
  ANALYTICS_SERVICE: process.env.ANALYTICS_SERVICE_URL || 'http://analytics-service:3005',
};

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'api-gateway' }));

// Public routes (no auth required)
app.use('/api/auth', createProxyMiddleware({ target: SERVICES.USER_SERVICE, changeOrigin: true }));

// Protected routes (JWT required)
app.use('/api/orders',    requireAuth, createProxyMiddleware({ target: SERVICES.ORDER_SERVICE,     changeOrigin: true }));
app.use('/api/inventory', requireAuth, createProxyMiddleware({ target: SERVICES.INVENTORY_SERVICE, changeOrigin: true }));
app.use('/api/billing',   requireAuth, createProxyMiddleware({ target: SERVICES.BILLING_SERVICE,   changeOrigin: true }));
app.use('/api/analytics', requireAuth, createProxyMiddleware({ target: SERVICES.ANALYTICS_SERVICE, changeOrigin: true }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`API Gateway running on port ${PORT}`));

module.exports = { app };
