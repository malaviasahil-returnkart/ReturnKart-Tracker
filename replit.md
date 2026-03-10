# ReturnKart - E-Commerce Return Tracking App

## Overview
ReturnKart is an Indian e-commerce return tracking application that helps users manage and track their product returns across multiple platforms like Amazon, Flipkart, Myntra, Meesho, AJIO, and Nykaa.

## Architecture
- **Frontend**: React + TypeScript with Vite, TailwindCSS, shadcn/ui components
- **Backend**: Express.js with TypeScript
- **Database**: PostgreSQL with Drizzle ORM
- **Routing**: wouter (frontend), Express (backend)
- **State Management**: TanStack React Query

## Key Features
- Dashboard with return statistics (total, active, completed, refund amounts)
- Create new return requests with platform, reason, and amount
- View all returns with search and filter by status/platform
- Detailed return view with status timeline
- Track returns by order ID

## Project Structure
- `shared/schema.ts` - Database schema and types (returnRequests, statusHistory, users)
- `server/routes.ts` - API endpoints (/api/returns, /api/returns/track/:orderId)
- `server/storage.ts` - Database storage layer using Drizzle ORM
- `server/seed.ts` - Seed data with 5 sample return requests
- `client/src/pages/` - Dashboard, ReturnsList, ReturnDetail, NewReturn, TrackReturn
- `client/src/components/layout.tsx` - App shell with nav header
- `client/src/lib/helpers.ts` - Utility functions for formatting and status colors

## Data Models
- **returnRequests**: orderId, productName, platform, reason, status, amount, tracking info
- **statusHistory**: Tracks status changes with timestamps and notes
- **Return Statuses**: initiated → pickup_scheduled → picked_up → in_transit → received → inspecting → refund_initiated → refund_completed (or rejected)
- **Platforms**: amazon, flipkart, myntra, meesho, ajio, nykaa, other

## Design
- Primary color: Orange (hue 27) - suitable for Indian e-commerce branding
- Font: Plus Jakarta Sans
- Clean, card-based layout with responsive design
