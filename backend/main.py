import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .auth.routes import router as auth_router
from .rag.retriever import router as rag_router
from .utils.config import settings

app = FastAPI(
    title="SANDYLLM Production API",
    description="Vertex AI Powered RAG System",
    version="2.0.0"
)

# CORS Configuration
# Adjust FRONTEND_URL in .env for production (e.g., https://your-frontend.vercel.app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Management
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    session_cookie="sandy_session",
    max_age=3600 * 24 * 7, # 7 days
    same_site="lax", # Required for OAuth redirect
    https_only=not settings.DEBUG # Use HTTPS only in production
)

# Routers
app.include_router(auth_router)
app.include_router(rag_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=settings.PORT, 
        reload=settings.DEBUG
    )
