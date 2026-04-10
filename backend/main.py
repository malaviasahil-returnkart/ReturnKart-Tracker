"""
RETURNKART.IN — FASTAPI ENTRY POINT
PORT is read from environment (injected by Replit). NEVER hardcode it.
Frontend: serves built React app as static files from /frontend/dist
"""
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.api.brands import router as brands_router
from backend.config import PORT, FRONTEND_URL, ENV
from backend.api.health import router as health_router
from backend.api.auth import router as auth_router
from backend.api.orders import router as orders_router
from backend.api.whatsapp import router as whatsapp_router
from backend.api.email_providers import router as email_providers_router
from backend.api.sms import router as sms_router


app = FastAPI(
    title="ReturnKart.in API",
    description="AI-powered e-commerce return window tracker for India",
    version="1.0.0",
    docs_url="/api/docs",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "https://return-kart-tracker.replit.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(health_router,          prefix="/api")
app.include_router(auth_router,            prefix="/api/auth",    tags=["auth"])
app.include_router(orders_router,          prefix="/api/orders",  tags=["orders"])
app.include_router(whatsapp_router,        prefix="/api/whatsapp",tags=["whatsapp"])
app.include_router(email_providers_router, prefix="/api/email",   tags=["email"])
app.include_router(brands_router)
app.include_router(sms_router,             prefix="/api/sms",     tags=["sms"])

# Serve React frontend from /frontend/dist
DIST = Path(__file__).parent.parent / "frontend" / "dist"

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = DIST / "index.html"
        return FileResponse(str(index))
else:
    @app.get("/")
    async def root():
        return {"message": "ReturnKart API is live. Frontend not built yet."}

if __name__ == "__main__":
    print(f"ReturnKart backend starting on port {PORT} [{ENV}]")
    print(f"Frontend dist: {'found' if DIST.exists() else 'NOT FOUND — run: cd frontend && npm run build'}")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=PORT, reload=(ENV != "production"))
