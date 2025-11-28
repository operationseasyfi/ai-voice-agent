from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uvicorn
from app.config import settings
from app.database import get_db
from app.logging_config import configure_logging, get_logger
from app.services.signalwire_agent import LoanIntakeAgent
from app.auth.routes import router as auth_router
from app.routers import calls, dashboard, agents, phone_numbers, dnc, billing

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="AI Voice Agent Platform",
    description="SignalWire AI Agent for loan intake with multi-tenant support",
    version="2.0.0"
)

# CORS middleware - configure for production
# Note: Wildcards don't work with allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:8000",
        "https://ai-voice-agent-frontend-l6bu.onrender.com",  # Frontend on Render
        "https://ai-voice-agent-30yv.onrender.com",  # Backend on Render (for Swagger)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Auth routes
app.include_router(auth_router, prefix='/auth', tags=["Authentication"])

# API routes
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(calls.router, prefix="/api/calls", tags=["Call History"])
app.include_router(agents.router, prefix="/api/agents", tags=["AI Agents"])
app.include_router(phone_numbers.router, prefix="/api/phone-numbers", tags=["Phone Numbers"])
app.include_router(dnc.router, prefix="/api/dnc", tags=["DNC Management"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])

# SignalWire Agent webhook
loan_intake_agent = LoanIntakeAgent()
agent_router = loan_intake_agent.as_router()
app.include_router(agent_router, prefix="/webhook", tags=["SignalWire Agent"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Voice Agent Platform",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth",
            "dashboard": "/api/dashboard",
            "calls": "/api/calls",
            "agents": "/api/agents",
            "phone_numbers": "/api/phone-numbers",
            "dnc": "/api/dnc",
            "billing": "/api/billing",
            "webhook": "/webhook"
        }
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "ai-voice-agent"}


@app.get("/health/database")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Test database connection and session."""
    try:
        result = await db.execute(text("SELECT 1 as test, NOW() as current_time"))
        row = result.fetchone()
        
        return {
            "status": "healthy",
            "database": "connected",
            "test_query": row.test,
            "timestamp": row.current_time,
            "message": "Database session working correctly"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "message": "Database session failed"
        }


@app.get("/health/full")
async def full_health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check including all services"""
    health = {
        "status": "healthy",
        "services": {}
    }
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
        health["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    # SignalWire check (basic config check)
    if settings.SIGNALWIRE_PROJECT_ID and settings.SIGNALWIRE_API_TOKEN:
        health["services"]["signalwire"] = {"status": "configured"}
    else:
        health["services"]["signalwire"] = {"status": "not_configured"}
        health["status"] = "degraded"
    
    # Redis check (placeholder - implement when Redis is integrated)
    health["services"]["redis"] = {"status": "not_implemented"}
    
    return health


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
