const { google } = require('googleapis');
const dayjs = require('dayjs');

// ─── Supported Indian ecommerce senders ───────────────────────────────────────
const KNOWN_SENDERS = {
  'auto-confirm@amazon.in': 'Amazon',
  'order-update@amazon.in': 'Amazon',
  'noreply@flipkart.com': 'Flipkart',
  'orders@meesho.com': 'Meesho',
  'noreply@myntra.com': 'Myntra',
  'noreply@ajio.com': 'AJIO',
  'noreply@nykaa.com': 'Nykaa',
  'support@snapdeal.com': 'Snapdeal',
  'noreply@jiomart.com': 'JioMart',
};

// ─── Return windows by platform (days) ────────────────────────────────────────
const RETURN_WINDOWS = {
  Amazon: 30,
  Flipkart: 10,
  Meesho: 7,
  Myntra: 30,
  AJIO: 15,
  Nykaa: 15,
  Snapdeal: 7,
  JioMart: 7,
  Default: 10,
};

// ─── Regex patterns for order data ────────────────────────────────────────────
const PATTERNS = {
  orderId: /(?:order(?:\s*id)?(?:\s*#|:|\s))\s*([A-Z0-9\-]{6,})/i,
  amount: /(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)/i,
  deliveryDate: /(?:deliver(?:ed|y)|arrives?|expected)\s*(?:by|on)?\s*([A-Za-z]+\s+\d{1,2}(?:,?\s*\d{4})?)/i,
  productName: /(?:your\s+)?(?:item|product|order)\s*[:\-]?\s*([^\n]{5,60})/i,
  otp: /\b(\d{4,6})\b(?=.*(?:otp|one.time|verification|code))/i,
  refundAmount: /(?:refund|amount\s+credited)\s*(?:of\s*)?(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)/i,
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getOAuthClient() {
  const client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    process.env.GOOGLE_REDIRECT_URI
  );
  return client;
}

function decodeBase64(str) {
  return Buffer.from(str.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf-8');
}

function extractBody(payload) {
  if (!payload) return '';

  if (payload.body?.data) return decodeBase64(payload.body.data);

  if (payload.parts) {
    for (const part of payload.parts) {
      if (part.mimeType === 'text/plain' && part.body?.data) {
        return decodeBase64(part.body.data);
      }
    }
    for (const part of payload.parts) {
      if (part.mimeType === 'text/html' && part.body?.data) {
        return decodeBase64(part.body.data).replace(/<[^>]*>/g, ' ');
      }
    }
  }

  return '';
}

function extractHeader(headers, name) {
  return headers?.find(h => h.name.toLowerCase() === name.toLowerCase())?.value || '';
}

// ─── Core parser ──────────────────────────────────────────────────────────────
function parseEmailToOrder(message) {
  const headers = message.payload?.headers || [];
  const from = extractHeader(headers, 'from');
  const subject = extractHeader(headers, 'subject');
  const dateStr = extractHeader(headers, 'date');
  const body = extractBody(message.payload);
  const fullText = `${subject}\n${body}`;

  // Identify platform
  const senderEmail = (from.match(/<(.+?)>/) || [null, from])[1]?.toLowerCase();
  const platform = KNOWN_SENDERS[senderEmail] || 'Unknown';

  // Extract fields
  const orderId = fullText.match(PATTERNS.orderId)?.[1] || null;
  const amount = fullText.match(PATTERNS.amount)?.[1]?.replace(/,/g, '') || null;
  const otp = fullText.match(PATTERNS.otp)?.[1] || null;
  const refundAmount = fullText.match(PATTERNS.refundAmount)?.[1]?.replace(/,/g, '') || null;
  const productNameRaw = fullText.match(PATTERNS.productName)?.[1]?.trim() || null;

  // Delivery date
  const deliveryRaw = fullText.match(PATTERNS.deliveryDate)?.[1];
  const deliveryDate = deliveryRaw ? dayjs(deliveryRaw).toISOString() : null;

  // Return window calculation
  const receivedDate = deliveryDate ? dayjs(deliveryDate) : dayjs(dateStr);
  const windowDays = RETURN_WINDOWS[platform] || RETURN_WINDOWS.Default;
  const returnDeadline = receivedDate.add(windowDays, 'day').toISOString();
  const daysRemaining = dayjs(returnDeadline).diff(dayjs(), 'day');

  // Email type classification
  let emailType = 'unknown';
  const subjectLower = subject.toLowerCase();
  if (subjectLower.includes('order') && subjectLower.includes('confirm')) emailType = 'order_confirmation';
  else if (subjectLower.includes('ship') || subjectLower.includes('dispatch')) emailType = 'shipment';
  else if (subjectLower.includes('deliver')) emailType = 'delivery';
  else if (subjectLower.includes('return')) emailType = 'return';
  else if (subjectLower.includes('refund')) emailType = 'refund';
  else if (subjectLower.includes('otp') || subjectLower.includes('verify')) emailType = 'otp';

  return {
    gmailMessageId: message.id,
    platform,
    emailType,
    orderId,
    subject,
    from,
    amount: amount ? parseFloat(amount) : null,
    otp,
    refundAmount: refundAmount ? parseFloat(refundAmount) : null,
    productName: productNameRaw,
    deliveryDate,
    returnDeadline,
    daysRemaining,
    returnWindowDays: windowDays,
    receivedAt: new Date(dateStr),
    rawSnippet: message.snippet,
  };
}

// ─── Gmail API fetcher ────────────────────────────────────────────────────────
async function fetchOrderEmails(accessToken, maxResults = 50) {
  const auth = getOAuthClient();
  auth.setCredentials({ access_token: accessToken });

  const gmail = google.gmail({ version: 'v1', auth });

  // Search query targets major Indian ecommerce senders
  const query = 'from:(amazon.in OR flipkart.com OR meesho.com OR myntra.com OR ajio.com OR nykaa.com OR snapdeal.com OR jiomart.com) subject:(order OR delivered OR return OR refund OR OTP)';

  const listRes = await gmail.users.messages.list({
    userId: 'me',
    q: query,
    maxResults,
  });

  const messages = listRes.data.messages || [];

  const parsed = await Promise.all(
    messages.map(async ({ id }) => {
      try {
        const msg = await gmail.users.messages.get({
          userId: 'me',
          id,
          format: 'full',
        });
        return parseEmailToOrder(msg.data);
      } catch (err) {
        console.error(`Error parsing message ${id}:`, err.message);
        return null;
      }
    })
  );

  return parsed.filter(Boolean);
}

module.exports = { fetchOrderEmails, parseEmailToOrder, getOAuthClient, RETURN_WINDOWS };
