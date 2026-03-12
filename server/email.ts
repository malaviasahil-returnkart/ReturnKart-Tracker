import { google } from "googleapis";
import type { Express } from "express";
import crypto from "crypto";
import { storage } from "./storage";

const SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"];
const pendingStates = new Map<string, number>();

function getOAuth2Client(redirectUri: string) {
  return new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    redirectUri
  );
}

function getRedirectUri(req: any): string {
  const protocol = req.headers["x-forwarded-proto"] || req.protocol || "https";
  const host = req.headers["x-forwarded-host"] || req.headers.host;
  return `${protocol}://${host}/api/email/callback`;
}

const PLATFORM_PATTERNS: Record<string, RegExp> = {
  amazon: /amazon\.(in|com)/i,
  flipkart: /flipkart/i,
  myntra: /myntra/i,
  meesho: /meesho/i,
  ajio: /ajio/i,
  nykaa: /nykaa/i,
};

function detectPlatform(from: string, subject: string): string {
  const text = `${from} ${subject}`;
  for (const [platform, pattern] of Object.entries(PLATFORM_PATTERNS)) {
    if (pattern.test(text)) return platform;
  }
  return "other";
}

function extractOrderId(subject: string, body: string): string {
  const patterns = [
    /order\s*#?\s*([A-Z0-9-]{5,})/i,
    /order\s+id\s*:?\s*([A-Z0-9-]{5,})/i,
    /OD[0-9]{10,}/,
    /[0-9]{3}-[0-9]{7}-[0-9]{7}/,
    /ODFK[0-9]+/i,
  ];
  const text = `${subject} ${body}`;
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return match[1] || match[0];
  }
  return `ORD-${Date.now()}`;
}

function extractProductName(subject: string, snippet: string): string {
  const deliveredMatch = subject.match(/delivered.*?[:\-–]\s*(.+)/i);
  if (deliveredMatch) return deliveredMatch[1].trim().substring(0, 100);

  const shippedMatch = subject.match(/shipped.*?[:\-–]\s*(.+)/i);
  if (shippedMatch) return shippedMatch[1].trim().substring(0, 100);

  const orderMatch = subject.match(/your order (?:of|for) (.+)/i);
  if (orderMatch) return orderMatch[1].trim().substring(0, 100);

  if (snippet && snippet.length > 10) {
    return snippet.substring(0, 80).trim();
  }

  return subject.substring(0, 100);
}

function calculateReturnDeadline(orderDate: Date, platform: string): Date {
  const days: Record<string, number> = {
    amazon: 10,
    flipkart: 10,
    myntra: 15,
    meesho: 7,
    ajio: 15,
    nykaa: 15,
    other: 7,
  };
  const deadline = new Date(orderDate);
  deadline.setDate(deadline.getDate() + (days[platform] || 7));
  return deadline;
}

export function registerEmailRoutes(app: Express) {
  app.get("/api/email/auth-url", (req, res) => {
    try {
      if (!process.env.GOOGLE_CLIENT_ID || !process.env.GOOGLE_CLIENT_SECRET) {
        return res.status(500).json({ message: "Google OAuth credentials not configured" });
      }
      const redirectUri = getRedirectUri(req);
      const oauth2Client = getOAuth2Client(redirectUri);
      const state = crypto.randomBytes(32).toString("hex");
      pendingStates.set(state, Date.now());
      const url = oauth2Client.generateAuthUrl({
        access_type: "offline",
        scope: SCOPES,
        prompt: "consent",
        state,
      });
      res.json({ url });
    } catch (error: any) {
      console.error("Auth URL error:", error);
      res.status(500).json({ message: "Failed to generate auth URL" });
    }
  });

  app.get("/api/email/callback", async (req, res) => {
    try {
      const { code, state } = req.query;
      if (!code || typeof code !== "string") {
        return res.status(400).json({ message: "Authorization code is required" });
      }
      if (!state || typeof state !== "string" || !pendingStates.has(state)) {
        return res.redirect("/?error=invalid_state");
      }
      pendingStates.delete(state);
      for (const [key, ts] of pendingStates) {
        if (Date.now() - ts > 10 * 60 * 1000) pendingStates.delete(key);
      }
      const redirectUri = getRedirectUri(req);
      const oauth2Client = getOAuth2Client(redirectUri);
      const { tokens } = await oauth2Client.getToken(code);
      const encodedTokens = encodeURIComponent(JSON.stringify(tokens));
      res.redirect(`/?tokens=${encodedTokens}`);
    } catch (error: any) {
      console.error("OAuth callback error:", error);
      res.redirect("/?error=auth_failed");
    }
  });

  app.post("/api/email/sync", async (req, res) => {
    try {
      const { access_token, refresh_token } = req.body;
      if (!access_token) {
        return res.status(400).json({ message: "Access token is required" });
      }

      const redirectUri = getRedirectUri(req);
      const oauth2Client = getOAuth2Client(redirectUri);
      oauth2Client.setCredentials({ access_token, refresh_token });

      const gmail = google.gmail({ version: "v1", auth: oauth2Client });

      const query = "from:(amazon OR flipkart OR myntra OR meesho OR ajio OR nykaa) subject:(order OR delivered OR shipped) newer_than:30d";

      const listRes = await gmail.users.messages.list({
        userId: "me",
        q: query,
        maxResults: 50,
      });

      const messages = listRes.data.messages || [];
      let synced = 0;

      for (const msg of messages) {
        try {
          const detail = await gmail.users.messages.get({
            userId: "me",
            id: msg.id!,
            format: "metadata",
            metadataHeaders: ["From", "Subject", "Date"],
          });

          const headers = detail.data.payload?.headers || [];
          const from = headers.find((h) => h.name === "From")?.value || "";
          const subject = headers.find((h) => h.name === "Subject")?.value || "";
          const dateStr = headers.find((h) => h.name === "Date")?.value || "";
          const snippet = detail.data.snippet || "";

          const platform = detectPlatform(from, subject);
          if (platform === "other") continue;

          const orderId = extractOrderId(subject, snippet);
          const existing = await storage.getOrderByOrderId(orderId);
          if (existing) continue;

          const orderDate = dateStr ? new Date(dateStr) : new Date();
          const returnDeadline = calculateReturnDeadline(orderDate, platform);

          const now = new Date();
          const twoDaysFromNow = new Date(now.getTime() + 2 * 24 * 60 * 60 * 1000);
          let status: "active" | "expiring_soon" | "expired" = "active";
          if (returnDeadline < now) status = "expired";
          else if (returnDeadline < twoDaysFromNow) status = "expiring_soon";

          await storage.createOrder({
            orderId,
            productName: extractProductName(subject, snippet),
            platform,
            status,
            amount: null,
            orderDate,
            returnDeadline,
            emailSubject: subject,
          });
          synced++;
        } catch (msgError) {
          console.error("Error processing message:", msgError);
        }
      }

      res.json({ synced, total: messages.length });
    } catch (error: any) {
      console.error("Email sync error:", error);
      if (error.code === 401 || error.message?.includes("invalid_grant")) {
        return res.status(401).json({ message: "Token expired. Please reconnect Gmail." });
      }
      res.status(500).json({ message: "Failed to sync emails" });
    }
  });

  app.get("/api/orders", async (_req, res) => {
    try {
      const allOrders = await storage.getAllOrders();
      res.json(allOrders);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch orders" });
    }
  });

  app.get("/api/orders/summary/stats", async (_req, res) => {
    try {
      const stats = await storage.getOrderStats();
      res.json(stats);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch stats" });
    }
  });
}
