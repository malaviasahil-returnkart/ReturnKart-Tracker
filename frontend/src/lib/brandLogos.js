/**
 * RETURNKART.IN — BRAND LOGO REGISTRY
 *
 * Maps brand names (as returned by Gemini) to their domain.
 * Google favicon API: https://www.google.com/s2/favicons?domain={domain}&sz=64
 * Free, no API key, works for every domain.
 *
 * Fallback: branded coloured initials with brand colour.
 *
 * NOTE: No apostrophes in object keys — use double quotes or plain strings.
 */

export const BRAND_CONFIG = {
  // ── Indian Ecommerce ──
  'Amazon India':       { domain: 'amazon.in',       color: '#FF9900', short: 'AMZ' },
  'Amazon':             { domain: 'amazon.in',       color: '#FF9900', short: 'AMZ' },
  'Flipkart':           { domain: 'flipkart.com',    color: '#2874F0', short: 'FK'  },
  'Myntra':             { domain: 'myntra.com',      color: '#FF3F6C', short: 'MYN' },
  'Meesho':             { domain: 'meesho.com',      color: '#9B59B6', short: 'MEE' },
  'Ajio':               { domain: 'ajio.com',        color: '#E63946', short: 'AJI' },
  'Nykaa':              { domain: 'nykaa.com',       color: '#FC2779', short: 'NYK' },
  'Nykaa Fashion':      { domain: 'nykaafashion.com',color: '#FC2779', short: 'NF'  },
  'JioMart':            { domain: 'jiomart.com',     color: '#0070BA', short: 'JIO' },
  'Tata CLiQ':          { domain: 'tatacliq.com',    color: '#1C1C1C', short: 'TCQ' },
  'TataCliq':           { domain: 'tatacliq.com',    color: '#1C1C1C', short: 'TCQ' },
  'Snapdeal':           { domain: 'snapdeal.com',    color: '#E40000', short: 'SD'  },
  'Croma':              { domain: 'croma.com',       color: '#6ABF45', short: 'CRM' },
  'Reliance Digital':   { domain: 'reliancedigital.in', color: '#003087', short: 'RD' },
  'BigBasket':          { domain: 'bigbasket.com',   color: '#84C225', short: 'BB'  },
  'Blinkit':            { domain: 'blinkit.com',     color: '#F5D000', short: 'BLK' },
  'Zepto':              { domain: 'zeptonow.com',    color: '#8B5CF6', short: 'ZPT' },
  'Swiggy':             { domain: 'swiggy.com',      color: '#FC8019', short: 'SWG' },
  'Paytm Mall':         { domain: 'paytmmall.com',   color: '#002970', short: 'PTM' },
  'Pepperfry':          { domain: 'pepperfry.com',   color: '#F37020', short: 'PFY' },
  'Urban Ladder':       { domain: 'urbanladder.com', color: '#2E7D32', short: 'UL'  },
  'FirstCry':           { domain: 'firstcry.com',    color: '#F4732A', short: 'FCY' },
  'Boat':               { domain: 'boat-lifestyle.com', color: '#000000', short: 'BOT' },
  'Noise':              { domain: 'gonoise.com',     color: '#1A1A1A', short: 'NSE' },
  'Titan':              { domain: 'titan.co.in',     color: '#003087', short: 'TTN' },
  'Tanishq':            { domain: 'tanishq.co.in',   color: '#8B6914', short: 'TNQ' },

  // ── Fashion & Apparel ──
  'Zara':               { domain: 'zara.com',        color: '#1C1C1C', short: 'ZAR' },
  'H&M':                { domain: 'hm.com',          color: '#E50010', short: 'HM'  },
  'Uniqlo':             { domain: 'uniqlo.com',      color: '#E40000', short: 'UNQ' },
  'Mango':              { domain: 'mango.com',       color: '#1C1C1C', short: 'MNG' },
  'Levis':              { domain: 'levi.com',        color: '#C41230', short: 'LVI' },
  'Allen Solly':        { domain: 'allensolly.com',  color: '#003087', short: 'AS'  },
  'Van Heusen':         { domain: 'vanheusenindia.com', color: '#1A1A6E', short: 'VH' },
  'Louis Philippe':     { domain: 'louisphilippe.com', color: '#8B1A1A', short: 'LP' },
  'Peter England':      { domain: 'peterengland.com', color: '#1C3A6E', short: 'PE' },
  'Raymond':            { domain: 'raymond.in',      color: '#1C1C1C', short: 'RMD' },
  'Fabindia':           { domain: 'fabindia.com',    color: '#8B4513', short: 'FBI' },
  'Biba':               { domain: 'biba.in',         color: '#E91E8C', short: 'BBA' },
  'Max Fashion':        { domain: 'maxfashion.in',   color: '#E30613', short: 'MAX' },
  'Westside':           { domain: 'westside.com',    color: '#9B1B30', short: 'WS'  },
  'Pantaloons':         { domain: 'pantaloons.com',  color: '#E30613', short: 'PNT' },
  'Shoppers Stop':      { domain: 'shoppersstop.com', color: '#CC0000', short: 'SS' },

  // ── Electronics & Tech ──
  'Apple':              { domain: 'apple.com',       color: '#555555', short: 'APL' },
  'Samsung':            { domain: 'samsung.com',     color: '#1428A0', short: 'SAM' },
  'Sony':               { domain: 'sony.com',        color: '#003087', short: 'SNY' },
  'LG':                 { domain: 'lg.com',          color: '#A50034', short: 'LG'  },
  'OnePlus':            { domain: 'oneplus.com',     color: '#F5010C', short: 'OP'  },
  'Xiaomi':             { domain: 'mi.com',          color: '#FF6900', short: 'MI'  },
  'Realme':             { domain: 'realme.com',      color: '#FFBE00', short: 'RLM' },
  'Oppo':               { domain: 'oppo.com',        color: '#1D8348', short: 'OPP' },
  'Vivo':               { domain: 'vivo.com',        color: '#415FFF', short: 'VIV' },
  'HP':                 { domain: 'hp.com',          color: '#0096D6', short: 'HP'  },
  'Dell':               { domain: 'dell.com',        color: '#007DB8', short: 'DEL' },
  'Lenovo':             { domain: 'lenovo.com',      color: '#E2231A', short: 'LNV' },
  'Asus':               { domain: 'asus.com',        color: '#1B6FBE', short: 'ASU' },
  'Acer':               { domain: 'acer.com',        color: '#83B81A', short: 'ACR' },
  'JBL':                { domain: 'jbl.com',         color: '#F37020', short: 'JBL' },
  'Bose':               { domain: 'bose.com',        color: '#1C1C1C', short: 'BSE' },
  'Philips':            { domain: 'philips.co.in',   color: '#0B5ED7', short: 'PHL' },

  // ── Beauty & Personal Care ──
  'Nykaa Beauty':       { domain: 'nykaa.com',       color: '#FC2779', short: 'NYK' },
  'Lakme':              { domain: 'lakmeindia.com',  color: '#E91E8C', short: 'LKM' },
  'Maybelline':         { domain: 'maybelline.com',  color: '#CC0000', short: 'MBL' },
  'LOreal':             { domain: 'loreal.com',      color: '#AA151B', short: 'LOR' },
  'Loreal':             { domain: 'loreal.com',      color: '#AA151B', short: 'LOR' },
  'Mamaearth':          { domain: 'mamaearth.in',    color: '#5B8C00', short: 'ME'  },
  'WOW Skin Science':   { domain: 'wowskinscience.com', color: '#00A651', short: 'WOW' },
  'The Body Shop':      { domain: 'thebodyshop.com', color: '#1A6B3C', short: 'TBS' },
  'Himalaya':           { domain: 'himalayawellness.com', color: '#1A6B3C', short: 'HIM' },

  // ── Home & Kitchen ──
  'IKEA':               { domain: 'ikea.com',        color: '#FFDA1A', short: 'IKA' },
  'Godrej':             { domain: 'godrej.com',      color: '#003087', short: 'GDJ' },
  'Prestige':           { domain: 'prestigegroup.com', color: '#CC0000', short: 'PRG' },
  'Milton':             { domain: 'milton.in',       color: '#003087', short: 'MLT' },
  'Borosil':            { domain: 'borosil.com',     color: '#1C3A8A', short: 'BRS' },

  // ── Sports & Fitness ──
  'Nike':               { domain: 'nike.com',        color: '#111111', short: 'NKE' },
  'Adidas':             { domain: 'adidas.com',      color: '#000000', short: 'ADI' },
  'Puma':               { domain: 'puma.com',        color: '#1C1C1C', short: 'PMA' },
  'Reebok':             { domain: 'reebok.com',      color: '#CC0000', short: 'RBK' },
  'Decathlon':          { domain: 'decathlon.in',    color: '#007BC7', short: 'DCT' },
  'Skechers':           { domain: 'skechers.com',    color: '#1C1C1C', short: 'SKC' },
  'Wildcraft':          { domain: 'wildcraft.com',   color: '#2E7D32', short: 'WLD' },
}

/**
 * Get brand config by brand name.
 * Tries exact match first, then case-insensitive, then partial.
 */
export function getBrandConfig(brandName) {
  if (!brandName) return null
  if (BRAND_CONFIG[brandName]) return BRAND_CONFIG[brandName]
  const lower = brandName.toLowerCase()
  for (const [key, val] of Object.entries(BRAND_CONFIG)) {
    if (key.toLowerCase() === lower) return val
  }
  for (const [key, val] of Object.entries(BRAND_CONFIG)) {
    if (lower.includes(key.toLowerCase()) || key.toLowerCase().includes(lower)) {
      return val
    }
  }
  return null
}
