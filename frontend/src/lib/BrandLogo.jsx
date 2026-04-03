/**
 * RETURNKART.IN — BrandLogo Component
 *
 * Displays the brand logo using Google's favicon service.
 * Google's S2 API: https://www.google.com/s2/favicons?domain={domain}&sz=64
 * Free, no API key, works for every domain, serves high-res icons.
 *
 * Fallback chain:
 *   1. Google favicon (domain lookup from brandLogos registry)
 *   2. Branded coloured initials with brand colour (when brand not in registry
 *      or image fails to load)
 *
 * Usage:
 *   <BrandLogo brand="Amazon India" size={32} />
 *   <BrandLogo brand="Flipkart" size={40} className="rounded-xl" />
 */
import { useState } from 'react'
import { getBrandConfig } from './brandLogos'

/** Get Google favicon URL for a domain */
function getGoogleLogoUrl(domain) {
  return `https://www.google.com/s2/favicons?domain=${domain}&sz=64`
}

export default function BrandLogo({ brand, size = 32, className = '' }) {
  const [imgError, setImgError] = useState(false)
  const config = getBrandConfig(brand)

  const style = {
    width: size,
    height: size,
    minWidth: size,
    borderRadius: size * 0.25,
  }

  // Show logo if brand is in registry and image hasn't errored
  if (config?.domain && !imgError) {
    return (
      <img
        src={getGoogleLogoUrl(config.domain)}
        alt={brand}
        style={{ ...style, objectFit: 'contain', background: '#fff', padding: size * 0.08 }}
        className={`flex-shrink-0 ${className}`}
        onError={() => setImgError(true)}
        loading="lazy"
      />
    )
  }

  // Fallback: branded coloured initials
  const bgColor = config?.color || '#2A2A2A'
  const short = config?.short || getInitials(brand)
  const textSize = size <= 28 ? 9 : size <= 36 ? 11 : 13

  return (
    <div
      style={{
        ...style,
        background: bgColor,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
      className={className}
      title={brand}
    >
      <span style={{
        fontSize: textSize,
        fontWeight: 700,
        color: '#fff',
        letterSpacing: '-0.02em',
        lineHeight: 1,
      }}>
        {short}
      </span>
    </div>
  )
}

/** Generate 2-3 letter initials from a brand name */
function getInitials(name) {
  if (!name) return '?'
  const words = name.trim().split(/\s+/)
  if (words.length === 1) return name.slice(0, 3).toUpperCase()
  return words.slice(0, 3).map(w => w[0]).join('').toUpperCase()
}
