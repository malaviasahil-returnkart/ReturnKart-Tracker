const express = require('express');
const router = express.Router();
const supabase = require('../db/supabase');

function computeStatus(returnDeadline, currentStatus) {
  if (['returned', 'return_initiated'].includes(currentStatus)) return currentStatus;
  if (!returnDeadline) return 'active';
  const now = new Date();
  const daysLeft = (new Date(returnDeadline) - now) / (1000 * 60 * 60 * 24);
  if (daysLeft < 0) return 'expired';
  if (daysLeft <= 2) return 'expiring_soon';
  return 'active';
}

// GET /api/orders
router.get('/', async (req, res) => {
  try {
    const { platform, status, expiring_soon } = req.query;
    let query = supabase.from('orders').select('*');
    if (platform) query = query.eq('platform', platform);
    if (expiring_soon === 'true') query = query.eq('status', 'expiring_soon');
    else if (status) query = query.eq('status', status);
    query = query.order('return_deadline', { ascending: true });
    const { data, error } = await query;
    if (error) throw error;
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/orders/summary/stats
router.get('/summary/stats', async (req, res) => {
  try {
    const { data, error } = await supabase.from('orders').select('status');
    if (error) throw error;
    const stats = { total: data.length, active: 0, expiring_soon: 0, expired: 0, returned: 0 };
    data.forEach(o => {
      if (o.status === 'active') stats.active++;
      else if (o.status === 'expiring_soon') stats.expiring_soon++;
      else if (o.status === 'expired') stats.expired++;
      else if (['returned', 'return_initiated'].includes(o.status)) stats.returned++;
    });
    res.json(stats);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/orders/:orderId
router.get('/:orderId', async (req, res) => {
  try {
    const { data, error } = await supabase
      .from('orders')
      .select('*')
      .eq('order_id', req.params.orderId)
      .single();
    if (error || !data) return res.status(404).json({ error: 'Order not found' });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/orders/bulk
router.post('/bulk', async (req, res) => {
  try {
    const { orders } = req.body;
    if (!Array.isArray(orders)) return res.status(400).json({ error: 'orders must be an array' });
    const { data, error } = await supabase
      .from('orders')
      .upsert(orders, { onConflict: 'order_id' })
      .select();
    if (error) throw error;
    res.json({ saved: data.length, orders: data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/orders/:orderId
router.delete('/:orderId', async (req, res) => {
  try {
    const { error } = await supabase
      .from('orders')
      .delete()
      .eq('order_id', req.params.orderId);
    if (error) throw error;
    res.json({ deleted: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
