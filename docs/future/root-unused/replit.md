# ReturnKart - E-Commerce Return Tracking App

## Overview
ReturnKart is an Indian e-commerce return tracking application that helps users manage and track their product returns across multiple platforms like Amazon, Flipkart, Myntra, Meesho, AJIO, and Nykaa. Includes Gmail OAuth integration to automatically scan order confirmation emails and track return windows.

## Architecture
- **Frontend**: React + TypeScript with Vite, TailwindCSS, shadcn/ui components
- **Backend**: Express.js with TypeScript
- **Database**: PostgreSQL with Drizzle ORM
- **Routing**: wouter (frontend), Express (backend)
- **State Management**: TanStack React Query
- **Gmail Integration**: Google OAuth2 + Gmail API (googleapis package)

## Key Features
- Dashboard with return statistics and Gmail sync
- Gmail OAuth to scan order emails from Amazon, Flipkart, Myntra, Meesho, AJIO, Nykaa
- Automatic return window tracking with countdown timers
- Create new return requests with platform, reason, and amount
- View all returns with search and filter by status/platform
- Detailed return view with status timeline
- Track returns by order ID

## Project Structure
- `shared/schema.ts` - Database schema and types (returnRequests, statusHistory, users, orders)
- `server/routes.ts` - Return API endpoints
- `server/email.ts` - Gmail OAuth and email sync routes (/api/email/auth-url, /api/email/callback, /api/email/sync, /api/orders, /api/orders/summary/stats)
- `server/storage.ts` - Database storage layer using Drizzle ORM
- `server/seed.ts` - Seed data with sample return requests
- `client/src/pages/` - Dashboard, ReturnsList, ReturnDetail, NewReturn, TrackReturn
- `client/src/lib/api.ts` - Frontend API helpers for Gmail/orders endpoints
- `client/src/lib/helpers.ts` - Utility functions for formatting and status colors
- `client/src/components/layout.tsx` - App shell with nav header

## Data Models
- **returnRequests**: orderId, productName, platform, reason, status, amount, tracking info
- **statusHistory**: Tracks status changes with timestamps and notes
- **orders**: Gmail-synced orders with orderId, productName, platform, status, returnDeadline
- **Return Statuses**: initiated → pickup_scheduled → picked_up → in_transit → received → inspecting → refund_initiated → refund_completed (or rejected)
- **Order Statuses**: active, expiring_soon, expired, return_initiated, returned
- **Platforms**: amazon, flipkart, myntra, meesho, ajio, nykaa, other

## Gmail OAuth Flow
1. User clicks "Connect Gmail" → GET /api/email/auth-url returns Google OAuth URL
2. User authorizes → Google redirects to /api/email/callback with auth code
3. Server exchanges code for tokens, redirects to frontend with tokens in URL params
4. Frontend stores tokens in localStorage, calls POST /api/email/sync to scan emails
5. Server searches Gmail for order-related emails, parses them, stores in orders table
6. CSRF protection via state parameter on OAuth flow

## Server Configuration
- Server listens on port 5000 (primary, webview) and port 3001 (alternate, for proxy compatibility)
- CORS configured for returnkart.in domains

## Design
- Primary color: Orange (hue 27) - suitable for Indian e-commerce branding
- Font: Plus Jakarta Sans
- Clean, card-based layout with responsive design

## Environment Secrets
- GOOGLE_CLIENT_ID - Google OAuth client ID
- GOOGLE_CLIENT_SECRET - Google OAuth client secret
- SESSION_SECRET - Session encryption key
- DATABASE_URL - PostgreSQL connection string (auto-managed)
