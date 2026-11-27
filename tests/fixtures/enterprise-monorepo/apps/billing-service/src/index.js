'use strict';
const express = require('express');
const { PrismaClient } = require('@nexus/shared-db');
const { validateToken } = require('@nexus/shared-auth');

const app = express();
app.use(express.json());

const prisma = new PrismaClient();

// Auth middleware
function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  try {
    req.user = validateToken(authHeader.slice(7));
    next();
  } catch (err) {
    res.status(401).json({ error: 'Invalid token' });
  }
}

// POST /charge — charge a customer for an order
app.post('/charge', requireAuth, async (req, res) => {
  const { userId, amount, paymentMethodId, idempotencyKey } = req.body;
  try {
    // Check idempotency
    if (idempotencyKey) {
      const existing = await prisma.charge.findFirst({ where: { idempotencyKey } });
      if (existing) return res.json({ id: existing.id, status: existing.status });
    }

    const charge = await prisma.charge.create({
      data: { userId, amount, paymentMethodId, idempotencyKey, status: 'completed' },
    });
    res.json({ id: charge.id, status: charge.status });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /invoices/:userId
app.get('/invoices/:userId', requireAuth, async (req, res) => {
  const invoices = await prisma.invoice.findMany({ where: { userId: req.params.userId } });
  res.json(invoices);
});

const PORT = process.env.PORT || 3004;
app.listen(PORT, () => console.log(`Billing Service on port ${PORT}`));

module.exports = { app };
