from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config import settings
from app.webhooks.signalwire_webhooks import router as signalwire_router

app = FastAPI(
    title="AI Voice Intake Agent",
    description="SignalWire AI Agent for loan intake and 3CX transfer",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include webhook routes
app.include_router(signalwire_router, prefix="/webhooks/signalwire", tags=["signalwire"])

# Include SignalWire Agent as a router
from app.services.signalwire_agent import loan_intake_agent
agent_router = loan_intake_agent.as_router()
app.include_router(agent_router, prefix="/agent/intake")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-voice-intake"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )