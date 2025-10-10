from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uvicorn
from app.config import settings
from app.database import get_db
# from app.webhooks.signalwire_webhooks import router as signalwire_router
from app.services.signalwire_agent import LoanIntakeAgent
from app.auth.routes import router as auth_router

app = FastAPI(
    title="AI Voice Agent for loan request",
    description="SignalWire AI Agent for loan and 3CX transfer",
    version="1.0.0",
    openapi_prefix="/api"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# App routes
app.include_router(auth_router, prefix='/auth', tags=["auth"])



# Create SignalWire Agent with proper route
loan_intake_agent = LoanIntakeAgent()
agent_router = loan_intake_agent.as_router()
app.include_router(agent_router, prefix="/webhook", tags=["Signalwire agent SDK"])




@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-voice-intake"}

@app.get("/health/database")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Test database connection and session."""
    try:
        # Test basic query
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



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )