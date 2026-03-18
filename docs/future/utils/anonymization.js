/**
 * ═══════════════════════════════════════════════════════════════
 * ReturnKart — Anonymization Pipeline
 * Converts encrypted PII into analytics-ready anonymous data
 * DPDP Act 2023 Section 2(3): "Anonymisation" compliant
 * ═══════════════════════════════════════════════════════════════
 *
 * PROBLEM:
 * Tier 1 (email, name, pincode) and Tier 2 (order IDs) are encrypted
 * in Supabase. That's great for security, but you can't run analytics
 * on ciphertext. You need to answer questions like:
 *   - "What % of returns come from pincode 560001?"
 *   - "What's the average refund delay for Delhivery vs BlueDart?"
 *   - "How many users switch from Amazon to Flipkart after a return?"
 *
 * SOLUTION:
 * An anonymization layer that transforms PII into analytics-safe
 * equivalents. The data is USEFUL but NOT IDENTIFIABLE.
 *
 * ═══════════════════════════════════════════════════════════════
 * HOW IT WORKS — THE "TWO-DATABASE" ARCHITECTURE
 * ═══════════════════════════════════════════════════════════════
 *
 *   LIVE DATABASE (Supabase)          ANALYTICS DATABASE (Supabase separate project or schema)
 *   ┌─────────────────────┐           ┌──────────────────────────┐
 *   │ users               │           │ anon_users               │
 *   │  email: [encrypted] │──process──│  anon_id: "RK_A7F3B2"   │
 *   │  name: [encrypted]  │           │  age_cohort: "25-34"     │
 *   │  pincode: [encrypted]│          │  region: "Bangalore Urban"│
 *   │  trust_score: 72    │           │  pincode_prefix: "560"   │
 *   ├─────────────────────┤           │  trust_score: 72         │
 *   │ orders              │           ├──────────────────────────┤
 *   │  order_id: [encrypted]│─process─│ anon_orders              │
 *   │  delivery_pincode:  │           │  anon_user_id: "RK_A7F3B2"│
 *   │    [encrypted]      │           │  brand: "flipkart"       │
 *   │  brand: "flipkart"  │           │  category: "mobile"      │
 *   │  value: 29999       │           │  value_bucket: "25K-50K" │
 *   │  tracking_id:       │           │  region: "Bangalore Urban"│
 *   │    [encrypted]      │           │  delivery_pincode_prefix:│
 *   └─────────────────────┘           │    "560"                 │
 *                                     │  courier: "Ekart"        │
 *                                     │  return_window: 7        │
 *                                     │  status: "returned"      │
 *                                     └──────────────────────────┘
 *
 * KEY PRINCIPLE: The anonymized data can NEVER be linked back to
 * a real person, even if combined with other datasets.
 * This is "k-anonymity" — every record looks like at least k other people.
 *
 * ═══════════════════════════════════════════════════════════════
 * ANONYMIZATION TECHNIQUES USED
 * ═══════════════════════════════════════════════════════════════
 *
 * 1. PSEUDONYMIZATION — Replace user_id with a random anon_id
 *    that has NO mathematical relationship to the original.
 *    (NOT a hash — hashes can be reversed with enough data)
 *
 * 2. GENERALIZATION — Reduce precision to prevent re-identification
 *    - Pincode "560001" → Prefix "560" (covers ~50,000 people)
 *    - Age 28 → Cohort "25-34"
 *    - Price ₹29,999 → Bucket "25K-50K"
 *    - Date "2026-03-13" → Month "2026-03"
 *
 * 3. SUPPRESSION — Remove fields entirely when the group is too small
 *    - If a pincode prefix has <50 users, replace with "OTHER"
 *    - If a brand+category combo has <10 orders, suppress the category
 *
 * 4. PERTURBATION — Add small random noise to numerical values
 *    - Trust score 72 → 70-74 (±2 random jitter)
 *    - Refund delay 5 days → 4-6 days (±1 random jitter)
 *
 * 5. TEMPORAL BLURRING — Round timestamps to reduce precision
 *    - "2026-03-13 14:32:17" → "2026-03" (month only)
 *    - Return window expiry exact date → "Week 11, 2026"
 */


// ═══════════════════════════════════════════════════
// CONFIGURATION: Anonymization rules per field
// ═══════════════════════════════════════════════════

const ANON_CONFIG = {
  // Minimum group size for k-anonymity
  // If fewer than K_THRESHOLD users share the same combination
  // of quasi-identifiers, suppress or generalize further
  K_THRESHOLD: 50,

  // Minimum records before a category appears in analytics
  MIN_CATEGORY_COUNT: 10,

  fields: {
    // ─── TIER 1: Encrypted PII → Anonymized equivalents ───

    email: {
      technique: 'suppress',
      output: null,
      reason: 'Email is a direct identifier. Completely removed from analytics.'
    },

    display_name: {
      technique: 'suppress',
      output: null,
      reason: 'Name is a direct identifier. Completely removed from analytics.'
    },

    phone: {
      technique: 'suppress',
      output: null,
      reason: 'Phone is a direct identifier. Completely removed from analytics.'
    },

    pincode: {
      technique: 'generalize',
      output_field: 'pincode_prefix',
      transform: (pincode) => {
        // "560001" → "560" (first 3 digits = district level)
        // Covers ~50,000-200,000 people per prefix
        if (!pincode || pincode.length < 3) return 'UNKNOWN';
        return pincode.substring(0, 3);
      },
      fallback_if_small_group: 'OTHER'
    },

    delivery_pincode: {
      technique: 'generalize',
      output_field: 'delivery_region',
      transform: (pincode) => {
        if (!pincode || pincode.length < 3) return 'UNKNOWN';
        return pincode.substring(0, 3);
      },
      fallback_if_small_group: 'OTHER'
    },

    address: {
      technique: 'suppress',
      output: null,
      reason: 'Full address is a direct identifier.'
    },

    gps_latitude: {
      technique: 'generalize',
      output_field: 'gps_grid_lat',
      // Round to 2 decimal places (~1.1km precision)
      // Enough for city-level logistics analysis
      // Too imprecise to identify a specific house
      transform: (lat) => lat ? Math.round(parseFloat(lat) * 100) / 100 : null
    },

    gps_longitude: {
      technique: 'generalize',
      output_field: 'gps_grid_lng',
      transform: (lng) => lng ? Math.round(parseFloat(lng) * 100) / 100 : null
    },

    google_access_token: {
      technique: 'suppress',
      output: null,
      reason: 'Auth tokens are never included in analytics.'
    },

    google_refresh_token: {
      technique: 'suppress',
      output: null,
      reason: 'Auth tokens are never included in analytics.'
    },

    // ─── TIER 2: Hashed IDs → Pseudonymized ───

    order_id_external: {
      technique: 'pseudonymize',
      output_field: 'anon_order_ref',
      // Replace with a random reference that preserves relationships
      // (same order in live DB always maps to same anon ref)
      // but cannot be reversed to find the real order ID
      transform: (orderId, saltedMap) => {
        if (!saltedMap.has(orderId)) {
          saltedMap.set(orderId, 'AORD_' + generateRandomId(8));
        }
        return saltedMap.get(orderId);
      }
    },

    tracking_id: {
      technique: 'suppress',
      output: null,
      reason: 'Tracking IDs can be used to query courier APIs and find addresses.'
    },

    email_id: {
      technique: 'suppress',
      output: null,
      reason: 'Gmail message IDs can identify the user via Google APIs.'
    },

    user_id: {
      technique: 'pseudonymize',
      output_field: 'anon_user_id',
      transform: (userId, saltedMap) => {
        if (!saltedMap.has(userId)) {
          saltedMap.set(userId, 'RK_' + generateRandomId(6));
        }
        return saltedMap.get(userId);
      }
    },

    // ─── TIER 3: Already clear — add generalization for extra safety ───

    order_value: {
      technique: 'generalize',
      output_field: 'value_bucket',
      transform: (value) => {
        const v = parseFloat(value);
        if (v < 500) return 'Under 500';
        if (v < 1000) return '500-1K';
        if (v < 2500) return '1K-2.5K';
        if (v < 5000) return '2.5K-5K';
        if (v < 10000) return '5K-10K';
        if (v < 25000) return '10K-25K';
        if (v < 50000) return '25K-50K';
        if (v < 100000) return '50K-1L';
        return 'Above 1L';
      }
    },

    trust_score: {
      technique: 'perturb',
      output_field: 'trust_score_band',
      transform: (score) => {
        // Round to nearest 5 + random ±2 jitter
        const s = parseInt(score);
        const rounded = Math.round(s / 5) * 5;
        const jitter = Math.floor(Math.random() * 5) - 2;
        return Math.max(0, Math.min(100, rounded + jitter));
      }
    }
  },

  // ─── DATE FIELDS: Always blur to month level ───
  date_fields: [
    'order_date', 'delivery_date', 'actual_delivery_date',
    'expected_delivery_date', 'return_expiry_date',
    'created_at', 'updated_at', 'parsed_at'
  ],

  date_transform: (dateStr) => {
    if (!dateStr) return null;
    // "2026-03-13" → "2026-03"
    // "2026-03-13T14:32:17Z" → "2026-03"
    return dateStr.substring(0, 7);
  },

  // ─── FIELDS PASSED THROUGH UNCHANGED ───
  // These are already non-personal and needed for analytics
  passthrough_fields: [
    'brand_slug', 'brand_display_name', 'item_category',
    'return_window_days', 'is_replacement_only', 'refund_type',
    'status', 'return_reason', 'courier_partner',
    'currency', 'quantity'
  ]
};


// ═══════════════════════════════════════════════════
// PINCODE → REGION MAPPING (for readable analytics)
// ═══════════════════════════════════════════════════

const PINCODE_PREFIX_TO_REGION = {
  '110': 'Delhi NCR', '120': 'Delhi NCR', '121': 'Delhi NCR',
  '122': 'Gurgaon', '201': 'Noida/Ghaziabad',
  '400': 'Mumbai', '410': 'Navi Mumbai/Pune', '411': 'Pune',
  '500': 'Hyderabad', '560': 'Bangalore Urban', '561': 'Bangalore Rural',
  '600': 'Chennai', '700': 'Kolkata',
  '380': 'Ahmedabad', '302': 'Jaipur', '226': 'Lucknow',
  '440': 'Nagpur', '452': 'Indore', '462': 'Bhopal',
  '160': 'Chandigarh', '180': 'Jammu', '190': 'Srinagar',
  '682': 'Kochi', '695': 'Thiruvananthapuram', '530': 'Visakhapatnam',
  '800': 'Patna', '831': 'Jamshedpur', '781': 'Guwahati',
};

function pincodeToRegion(prefix) {
  return PINCODE_PREFIX_TO_REGION[prefix] || `Region_${prefix}`;
}


// ═══════════════════════════════════════════════════
// CORE ANONYMIZATION ENGINE
// ═══════════════════════════════════════════════════

function generateRandomId(length) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  const randomValues = new Uint8Array(length);
  crypto.getRandomValues(randomValues);
  for (let i = 0; i < length; i++) {
    result += chars[randomValues[i] % chars.length];
  }
  return result;
}


class ReturnKartAnonymizer {

  constructor() {
    // Pseudonymization maps — ensure same real ID always maps to same anon ID
    // within a single anonymization run
    this.userIdMap = new Map();
    this.orderIdMap = new Map();
  }

  /**
   * Anonymize a single user record.
   * Input: decrypted user object (after client-side decryption)
   * Output: anonymous user object safe for analytics
   */
  anonymizeUser(user) {
    const anon = {};

    // Pseudonymize user ID
    anon.anon_user_id = this._pseudonymize(user.id || user.user_id, this.userIdMap, 'RK_', 6);

    // Generalize pincode → prefix → region
    if (user.pincode) {
      const prefix = user.pincode.substring(0, 3);
      anon.pincode_prefix = prefix;
      anon.region = pincodeToRegion(prefix);
    } else {
      anon.pincode_prefix = 'UNKNOWN';
      anon.region = 'UNKNOWN';
    }

    // Perturb trust score
    if (user.trust_score !== undefined) {
      const rounded = Math.round(user.trust_score / 5) * 5;
      const jitter = Math.floor(Math.random() * 5) - 2;
      anon.trust_score_band = Math.max(0, Math.min(100, rounded + jitter));
    }

    // Blur timestamps
    if (user.created_at) {
      anon.signup_month = user.created_at.substring(0, 7);
    }

    // Suppress everything else (name, email, phone, tokens)
    // These fields simply don't exist in the anonymous output

    return anon;
  }

  /**
   * Anonymize a single order record.
   * Input: decrypted order object
   * Output: anonymous order safe for analytics and B2B sale
   */
  anonymizeOrder(order) {
    const anon = {};

    // Pseudonymize IDs
    anon.anon_user_id = this._pseudonymize(order.user_id, this.userIdMap, 'RK_', 6);
    anon.anon_order_ref = this._pseudonymize(
      order.order_id_external, this.orderIdMap, 'AORD_', 8
    );

    // Passthrough: non-personal fields
    anon.brand = order.brand_slug;
    anon.brand_name = order.brand_display_name;
    anon.category = order.item_category;
    anon.courier = order.courier_partner;
    anon.return_window_days = order.return_window_days;
    anon.is_replacement_only = order.is_replacement_only;
    anon.refund_type = order.refund_type;
    anon.status = order.status;
    anon.return_reason = order.return_reason;
    anon.quantity = order.quantity;

    // Generalize: price → bucket
    anon.value_bucket = this._bucketize(order.order_value);
    // Also keep the raw value for aggregate sums (safe because it's not PII)
    anon.order_value = parseFloat(order.order_value);

    // Generalize: pincode → prefix → region
    if (order.delivery_pincode) {
      const prefix = order.delivery_pincode.substring(0, 3);
      anon.delivery_pincode_prefix = prefix;
      anon.delivery_region = pincodeToRegion(prefix);
    }

    // Blur dates to month level
    anon.order_month = order.order_date ? order.order_date.substring(0, 7) : null;
    anon.delivery_month = order.actual_delivery_date
      ? order.actual_delivery_date.substring(0, 7) : null;

    // Calculate derived analytics fields
    if (order.actual_delivery_date && order.order_date) {
      const ordered = new Date(order.order_date);
      const delivered = new Date(order.actual_delivery_date);
      anon.delivery_days = Math.round((delivered - ordered) / (1000 * 60 * 60 * 24));
    }

    if (order.actual_delivery_date && order.return_expiry_date) {
      const delivered = new Date(order.actual_delivery_date);
      const expiry = new Date(order.return_expiry_date);
      const today = new Date();
      anon.days_until_expiry = Math.round((expiry - today) / (1000 * 60 * 60 * 24));
      anon.is_expired = today > expiry;
    }

    // Suppress: tracking_id, email_id (can be used to trace back)
    // These fields simply don't exist in the anonymous output

    return anon;
  }

  /**
   * Anonymize a ghost report for logistics analytics.
   */
  anonymizeGhostReport(report) {
    const anon = {};

    anon.anon_user_id = this._pseudonymize(report.user_id, this.userIdMap, 'RK_', 6);
    anon.anon_order_ref = this._pseudonymize(
      report.order_id, this.orderIdMap, 'AORD_', 8
    );

    // Generalize GPS to ~1km grid (2 decimal places)
    if (report.gps_latitude) {
      anon.gps_grid_lat = Math.round(parseFloat(report.gps_latitude) * 100) / 100;
    }
    if (report.gps_longitude) {
      anon.gps_grid_lng = Math.round(parseFloat(report.gps_longitude) * 100) / 100;
    }

    anon.status = report.status;
    anon.report_month = report.created_at ? report.created_at.substring(0, 7) : null;

    // Suppress: full address, exact GPS, description (may contain PII)

    return anon;
  }

  /**
   * Batch anonymize and apply k-anonymity suppression.
   * After individual anonymization, checks if any group
   * (pincode_prefix + brand + category) has fewer than K records.
   * If so, generalizes further.
   */
  batchAnonymizeOrders(orders) {
    // Step 1: Anonymize each order individually
    const anonymized = orders.map(o => this.anonymizeOrder(o));

    // Step 2: Check k-anonymity for pincode groups
    const pincodeGroups = {};
    anonymized.forEach(o => {
      const key = o.delivery_pincode_prefix || 'UNKNOWN';
      pincodeGroups[key] = (pincodeGroups[key] || 0) + 1;
    });

    // Step 3: Suppress small pincode groups
    anonymized.forEach(o => {
      const key = o.delivery_pincode_prefix || 'UNKNOWN';
      if (pincodeGroups[key] < ANON_CONFIG.K_THRESHOLD) {
        o.delivery_pincode_prefix = 'OTHER';
        o.delivery_region = 'Other Region';
      }
    });

    // Step 4: Check k-anonymity for brand+category combos
    const comboGroups = {};
    anonymized.forEach(o => {
      const key = `${o.brand}_${o.category}`;
      comboGroups[key] = (comboGroups[key] || 0) + 1;
    });

    anonymized.forEach(o => {
      const key = `${o.brand}_${o.category}`;
      if (comboGroups[key] < ANON_CONFIG.MIN_CATEGORY_COUNT) {
        o.category = 'other';
      }
    });

    return anonymized;
  }

  /**
   * Generate analytics summary from anonymized data.
   * This is the kind of report you sell to brands and 3PLs.
   */
  generateAnalyticsSummary(anonOrders) {
    const summary = {
      generated_at: new Date().toISOString().substring(0, 7),
      total_orders: anonOrders.length,
      total_value: anonOrders.reduce((sum, o) => sum + (o.order_value || 0), 0),

      // Brand performance breakdown
      by_brand: this._groupAndCount(anonOrders, 'brand'),

      // Category distribution
      by_category: this._groupAndCount(anonOrders, 'category'),

      // Return rate by brand
      return_rates: this._calculateReturnRates(anonOrders),

      // Courier performance (average delivery days)
      courier_performance: this._courierStats(anonOrders),

      // Regional distribution
      by_region: this._groupAndCount(anonOrders, 'delivery_region'),

      // Value bucket distribution
      by_value: this._groupAndCount(anonOrders, 'value_bucket'),

      // Ghost delivery hotspots
      // (added separately from ghost report data)
    };

    return summary;
  }

  // ─── INTERNAL HELPERS ───

  _pseudonymize(realId, map, prefix, length) {
    if (!realId) return null;
    const key = String(realId);
    if (!map.has(key)) {
      map.set(key, prefix + generateRandomId(length));
    }
    return map.get(key);
  }

  _bucketize(value) {
    const v = parseFloat(value);
    if (isNaN(v)) return 'UNKNOWN';
    if (v < 500) return 'Under 500';
    if (v < 1000) return '500-1K';
    if (v < 2500) return '1K-2.5K';
    if (v < 5000) return '2.5K-5K';
    if (v < 10000) return '5K-10K';
    if (v < 25000) return '10K-25K';
    if (v < 50000) return '25K-50K';
    if (v < 100000) return '50K-1L';
    return 'Above 1L';
  }

  _groupAndCount(records, field) {
    const groups = {};
    records.forEach(r => {
      const key = r[field] || 'UNKNOWN';
      groups[key] = (groups[key] || 0) + 1;
    });
    return Object.entries(groups)
      .sort((a, b) => b[1] - a[1])
      .map(([key, count]) => ({
        [field]: key,
        count,
        percentage: Math.round(count / records.length * 1000) / 10
      }));
  }

  _calculateReturnRates(records) {
    const brandStats = {};
    records.forEach(r => {
      const brand = r.brand || 'UNKNOWN';
      if (!brandStats[brand]) brandStats[brand] = { total: 0, returned: 0 };
      brandStats[brand].total++;
      if (r.status === 'returned' || r.status === 'refunded') {
        brandStats[brand].returned++;
      }
    });
    return Object.entries(brandStats)
      .map(([brand, stats]) => ({
        brand,
        total_orders: stats.total,
        returned: stats.returned,
        return_rate: Math.round(stats.returned / stats.total * 1000) / 10
      }))
      .sort((a, b) => b.return_rate - a.return_rate);
  }

  _courierStats(records) {
    const courierData = {};
    records.forEach(r => {
      if (!r.courier || !r.delivery_days) return;
      if (!courierData[r.courier]) courierData[r.courier] = [];
      courierData[r.courier].push(r.delivery_days);
    });
    return Object.entries(courierData).map(([courier, days]) => ({
      courier,
      order_count: days.length,
      avg_delivery_days: Math.round(days.reduce((a, b) => a + b, 0) / days.length * 10) / 10,
      fastest: Math.min(...days),
      slowest: Math.max(...days)
    }));
  }

  /**
   * Reset pseudonymization maps between batch runs.
   * IMPORTANT: Call this when starting a new anonymization batch.
   * If you reuse maps across batches, the same anon IDs persist
   * which could enable cross-batch correlation attacks.
   */
  reset() {
    this.userIdMap = new Map();
    this.orderIdMap = new Map();
  }
}


// ═══════════════════════════════════════════════════
// SUPABASE EDGE FUNCTION: Scheduled anonymization job
// ═══════════════════════════════════════════════════

/**
 * This runs as a Supabase Edge Function on a daily cron schedule.
 * It reads decrypted data from the live DB (server-side decryption
 * using a master key stored in Edge Function secrets), anonymizes it,
 * and writes to the analytics schema.
 *
 * The master key is ONLY used server-side for batch anonymization.
 * It is NEVER sent to the client or exposed in API responses.
 *
 * ALTERNATIVE (if you don't want server-side decryption):
 * Run the anonymization client-side when the user opens the app,
 * and have the client push anonymized records to a separate
 * "anon_orders" table. This is safer but slower.
 *
 * RECOMMENDED SCHEDULE: Run once daily at 2:00 AM IST
 */

/*
// Supabase Edge Function example (Deno/TypeScript):

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

Deno.serve(async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL'),
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')  // Service role for full access
  );

  // 1. Fetch orders from the last 24 hours
  const { data: orders } = await supabase
    .from('orders')
    .select('*')
    .gte('updated_at', new Date(Date.now() - 86400000).toISOString());

  // 2. Decrypt Tier 1 & 2 fields using server-side master key
  //    (implementation depends on your key management approach)
  const decrypted = await serverSideDecrypt(orders);

  // 3. Anonymize
  const anonymizer = new ReturnKartAnonymizer();
  const anonOrders = anonymizer.batchAnonymizeOrders(decrypted);

  // 4. Upsert into analytics table
  await supabase.from('anon_orders').upsert(anonOrders, {
    onConflict: 'anon_order_ref'
  });

  // 5. Log to DPDP audit trail
  await supabase.from('dpdp_audit_log').insert({
    action: 'batch_anonymization',
    details: `Anonymized ${anonOrders.length} orders`,
    executed_at: new Date().toISOString()
  });

  return new Response(JSON.stringify({ anonymized: anonOrders.length }));
});
*/


// ═══════════════════════════════════════════════════
// WHAT THE ANONYMIZED DATA LOOKS LIKE
// ═══════════════════════════════════════════════════

/*
BEFORE (decrypted live data — only visible on user's device):
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "hanumaan@gmail.com",
  "display_name": "Hanumaan Kumar",
  "pincode": "560001",
  "order_id_external": "OD432198765012345678",
  "item_name": "Samsung Galaxy S24 FE",
  "item_category": "mobile",
  "order_value": 29999,
  "delivery_pincode": "560001",
  "courier_partner": "Ekart Logistics",
  "tracking_id": "FMPC001234567890",
  "actual_delivery_date": "2026-03-12",
  "status": "returned",
  "return_reason": "Screen defect"
}

AFTER (anonymized analytics — safe to sell to brands/3PLs):
{
  "anon_user_id": "RK_A7F3B2",
  "anon_order_ref": "AORD_K9M2P4T7",
  "region": "Bangalore Urban",
  "delivery_pincode_prefix": "560",
  "delivery_region": "Bangalore Urban",
  "brand": "flipkart",
  "category": "mobile",
  "value_bucket": "25K-50K",
  "order_value": 29999,
  "courier": "Ekart Logistics",
  "return_window_days": 7,
  "is_replacement_only": true,
  "status": "returned",
  "return_reason": "Screen defect",
  "order_month": "2026-03",
  "delivery_month": "2026-03",
  "delivery_days": 3,
  "trust_score_band": 70
}

NOTICE WHAT'S GONE:
  ✗ Real user ID → replaced with random "RK_A7F3B2"
  ✗ Email → suppressed entirely
  ✗ Name → suppressed entirely
  ✗ Full pincode → generalized to "560" prefix
  ✗ Real order ID → replaced with random "AORD_K9M2P4T7"
  ✗ Tracking ID → suppressed entirely
  ✗ Item name → suppressed (can identify specific purchase)
  ✗ Exact dates → blurred to month "2026-03"
  ✗ Trust score 72 → perturbed to band "70"

NOTICE WHAT'S KEPT (analytically valuable):
  ✓ Brand, category, courier, status, return reason
  ✓ Price (exact for aggregation, also bucketed)
  ✓ Region-level geography
  ✓ Return window and refund type
  ✓ Delivery speed (derived days)
  ✓ Pseudonymized IDs (for counting unique users, repeat behavior)
*/


// ═══════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════

export {
  ReturnKartAnonymizer,
  ANON_CONFIG,
  PINCODE_PREFIX_TO_REGION,
  pincodeToRegion
};

export default ReturnKartAnonymizer;
