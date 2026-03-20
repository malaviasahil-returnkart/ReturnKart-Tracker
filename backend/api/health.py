"""Health check + diagnostic endpoints"""
from fastapi import APIRouter
from backend.config import ENV, GEMINI_API_KEY

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "env": ENV}

@router.get("/debug")
async def debug_check():
    """Diagnostic endpoint — checks if all dependencies are available."""
    checks = {}

    # 1. Check GEMINI_API_KEY
    checks["gemini_key_set"] = bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 5)
    checks["gemini_key_prefix"] = GEMINI_API_KEY[:8] + "..." if GEMINI_API_KEY else "MISSING"

    # 2. Check google-generativeai import
    try:
        import google.generativeai as genai
        checks["google_genai_installed"] = True
        checks["google_genai_version"] = getattr(genai, "__version__", "unknown")
    except ImportError as e:
        checks["google_genai_installed"] = False
        checks["google_genai_error"] = str(e)

    # 3. Check supabase import
    try:
        from supabase import create_client
        checks["supabase_installed"] = True
    except ImportError as e:
        checks["supabase_installed"] = False
        checks["supabase_error"] = str(e)

    # 4. Check knowledge_base.json
    from pathlib import Path
    kb_path = Path(__file__).parent.parent / "data" / "knowledge_base.json"
    checks["knowledge_base_exists"] = kb_path.exists()

    # 5. Python path
    import sys
    checks["python_path_count"] = len(sys.path)
    checks["python_version"] = sys.version.split()[0]

    return checks
