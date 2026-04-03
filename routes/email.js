const express = require('express');
const router = express.Router();
const { google } = require('googleapis');
const supabase = require('../db/supabase');

const SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'];

function getOAuthClient() {
  return new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    process.env.GOOGLE_REDIRECT_URI
  );
}

// GET /api/email/auth-url
router.get('/auth-url', (req, res) => {
  const oauth2Client = getOAuthClient();
  const url = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent',
  });
  res.json({ url });
});

// GET /api/email/callback
router.get('/callback', async (req, res) => {
  const { code } = req.query;
  if (!code) return res.status(400).json({ error: 'No code provided' });
  try {
    const oauth2Client = getOAuthClient();
    const { tokens } = await oauth2Client.getToken(code);
    const frontendUrl = process.env.FRONTEND_URL || 'https://return-manager.replit.app';
    res.redirect(`${frontendUrl}/?tokens=${encodeURIComponent(JSON.stringify(tokens))}`);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/email/refresh-token
router.post('/refresh-token', async (req, res) => {
  const { refresh_token } = req.body;
  if (!refresh_token) return res.status(400).json({ error: 'No refresh_token' });
  try {
    const oauth2Client = getOAuthClient();
    oauth2Client.setCredentials({ refresh_token });
    const { credentials } = await oauth2Client.refreshAccessToken();
    res.json({ tokens: credentials });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/email/sync
router.post('/sync', async (req, res) => {
  const { access_token, refresh_token } = req.body;
  if (!access_token) return res.status(400).json({ error: 'No access_token' });

  try {
    const oauth2Client = getOAuthClient();
    oauth2Client.setCredentials({ access_token, refresh_token });
    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

    const searchQueries = [
      'subject:(order confirmed OR order placed OR order shipped) from:(amazon OR flipkart OR myntra OR nykaa OR ajio OR meesho)',
      'subject:(your order) from:(noreply@amazon.in OR noreply@flipkart.com OR myntra)',
    ];

    const allMessages = [];
    for (const q of searchQueries) {
      try {
        const response = await gmail.users.messages.list({ userId: 'me', q, maxResults: 20 });
        if (response.data.messages) allMessages.push(...response.data.messages);
      } catch (e) { console.error('Search error:', e.message); }
    }

    const uniqueMessages = [...new Map(allMessages.map(m => [m.id, m])).values()];
    const returnWindows = { amazon: 30, flipkart: 10, myntra: 30, nykaa: 15, ajio: 45, meesho: 7, other: 7 };
    const parsedOrders = [];

    for (const msg of uniqueMessages.slice(0, 30)) {
      try {
        const full = await gmail.users.messages.get({
          userId: 'me', id: msg.id, format: 'metadata',
          metadataHeaders: ['Subject', 'From', 'Date'],
        });
        const headers = full.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || '';
        const from = headers.find(h => h.name === 'From')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value || '';
        const snippet = full.data.snippet || '';

        let platform = 'other';
        if (from.toLowerCase().includes('amazon')) platform = 'amazon';
        else if (from.toLowerCase().includes('flipkart')) platform = 'flipkart';
        else if (from.toLowerCase().includes('myntra')) platform = 'myntra';
        else if (from.toLowerCase().includes('nykaa')) platform = 'nykaa';
        else if (from.toLowerCase().includes('ajio')) platform = 'ajio';
        else if (from.toLowerCase().includes('meesho')) platform = 'meesho';

        const orderIdMatch = (subject + ' ' + snippet).match(/(?:order[# ]*|#)([A-Z0-9\-]{6,20})/i);
        const orderId = orderIdMatch ? orderIdMatch[1] : msg.id;
        const orderDate = new Date(date);
        const returnWindowDays = returnWindows[platform] || 7;
        const deliveryDate = new Date(orderDate.getTime() + 5 * 24 * 60 * 60 * 1000);
        const returnDeadline = new Date(deliveryDate.getTime() + returnWindowDays * 24 * 60 * 60 * 1000);

        const now = new Date();
        const daysLeft = (returnDeadline - now) / (1000 * 60 * 60 * 24);
        let status = 'active';
        if (daysLeft < 0) status = 'expired';
        else if (daysLeft <= 2) status = 'expiring_soon';

        const orderData = {
          order_id: orderId,
          platform,
          product_name: subject.replace(/^(re:|fwd:)/i, '').trim().substring(0, 100),
          order_date: orderDate.toISOString(),
          delivery_date: deliveryDate.toISOString(),
          return_window_days: returnWindowDays,
          return_deadline: returnDeadline.toISOString(),
          status,
          email_id: msg.id,
          raw_email_snippet: snippet.substring(0, 300),
        };

        const { error } = await supabase
          .from('orders')
          .upsert(orderData, { onConflict: 'order_id' });
        if (error) console.error('Upsert error:', error.message);
        else parsedOrders.push(orderData);
      } catch (e) { console.error('Parse error:', e.message); }
    }

    res.json({ synced: parsedOrders.length, orders: parsedOrders });
  } catch (err) {
    console.error('Sync error:', err);
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
