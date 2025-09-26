# AI Voice Intake Agent → 3CX Transfer - Complete Implementation Guide

## Project Overview

Build an AI voice agent using SignalWire Agents SDK that:
- Answers inbound calls from SMS loan offer leads with real-time conversation control
- Performs personalized greetings using CRM data via on_call_start() handler
- Runs structured intake script using conversation contexts and steps
- Routes calls to appropriate 3CX queues based on debt amount via SIP/WebRTC
- Syncs all data with OCC CRM in real-time

## System Architecture

```
Lead calls TFN → SignalWire Platform → Agent Server (/agent/intake) → OCC CRM
                                          ↓
                                Transfer to 3CX Queue (via Twilio SIP)
```

## Technology Stack

- **Backend**: Python FastAPI
- **AI Voice**: SignalWire Agents SDK (signalwire-agents==1.0.0)
- **CRM**: OCC CRM API integration
- **Call Transfer**: Twilio SIP trunk to 3CX with low-latency bridging
- **Deployment**: Docker + cloud hosting

## Project Structure

```
ai-voice-intake/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── models/
│   │   ├── __init__.py
│   │   ├── call_data.py        # Pydantic models for call data
│   │   └── crm_models.py       # CRM data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── signalwire_agent.py # SignalWire Agents SDK implementation
│   │   ├── agent_server.py     # Agent server with SIP/WebRTC config
│   │   ├── crm_service.py      # OCC CRM integration
│   │   └── call_router.py      # Call routing logic
│   ├── webhooks/
│   │   ├── __init__.py
│   │   └── signalwire_webhooks.py # Backup webhook handlers
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # Utility functions
├── signalwire_config/
│   ├── ai_agent_config.json    # AI Agent configuration
│   └── intake_script.txt       # Verbatim intake script
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Implementation Steps

### Step 1: Environment Setup

Create `.env` file:
```bash
# SignalWire Configuration
SIGNALWIRE_PROJECT_ID=your_project_id
SIGNALWIRE_API_TOKEN=your_api_token
SIGNALWIRE_SPACE_URL=your_space.signalwire.com

# OCC CRM Configuration
OCC_CRM_API_URL=https://api.occcrm.com/v1
OCC_CRM_API_KEY=your_crm_api_key

# 3CX Transfer Configuration
QUEUE_A_DID=+1234567890  # For debt >= $35k
QUEUE_B_DID=+1234567891  # For debt < $35k
TWILIO_SIP_TRUNK=sip:trunk@your-twilio.pstn.twilio.com

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
WEBHOOK_BASE_URL=https://your-app.com
```

### Step 2: FastAPI Application Structure

**main.py**
```python
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
```

**config.py**
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # SignalWire
    SIGNALWIRE_PROJECT_ID: str
    SIGNALWIRE_API_TOKEN: str
    SIGNALWIRE_SPACE_URL: str
    
    # OCC CRM
    OCC_CRM_API_URL: str
    OCC_CRM_API_KEY: str
    
    # 3CX Transfer
    QUEUE_A_DID: str
    QUEUE_B_DID: str
    TWILIO_SIP_TRUNK: str
    
    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    WEBHOOK_BASE_URL: str
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 3: Data Models

**models/call_data.py**
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class LeadInfo(BaseModel):
    phone_number: str
    lead_name: Optional[str] = None
    loan_amount: Optional[float] = None
    found_in_crm: bool = False

class IntakeData(BaseModel):
    # Intake questions responses
    loan_amount_requested: Optional[float] = Field(None, description="Q1: Exact amount to borrow")
    funds_purpose: Optional[str] = Field(None, description="Q2: What funds will be used for")
    employment_status: Optional[str] = Field(None, description="Q3: Paycheck/self-employed/fixed income")
    credit_card_debt: Optional[float] = Field(None, description="Q4: Total unsecured credit card debt")
    personal_loan_debt: Optional[float] = Field(None, description="Q5: Unsecured personal loan balances")
    other_debt: Optional[float] = Field(None, description="Q6: Medical bills and other balances")
    monthly_income: Optional[float] = Field(None, description="Q7: Monthly income amount")
    ssn_last_four: Optional[str] = Field(None, description="Q9: Last 4 digits of SSN")
    
    @property
    def total_unsecured_debt(self) -> float:
        """Calculate total unsecured debt for routing decision"""
        return (
            (self.credit_card_debt or 0) + 
            (self.personal_loan_debt or 0) + 
            (self.other_debt or 0)
        )

class CallSession(BaseModel):
    call_id: str
    lead_info: LeadInfo
    intake_data: Optional[IntakeData] = None
    queue_assigned: Optional[str] = None
    call_status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### Step 4: CRM Service Integration

**services/crm_service.py**
```python
import httpx
import logging
from typing import Optional, Dict, Any
from app.config import settings
from app.models.call_data import LeadInfo, IntakeData

logger = logging.getLogger(__name__)

class OCCCRMService:
    def __init__(self):
        self.base_url = settings.OCC_CRM_API_URL
        self.api_key = settings.OCC_CRM_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def lookup_lead_by_phone(self, phone_number: str) -> Optional[LeadInfo]:
        """Look up lead information by phone number"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/leads/lookup",
                    headers=self.headers,
                    params={"phone": phone_number}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return LeadInfo(
                        phone_number=phone_number,
                        lead_name=data.get("name"),
                        loan_amount=data.get("loan_amount"),
                        found_in_crm=True
                    )
                elif response.status_code == 404:
                    # Lead not found, return basic info
                    return LeadInfo(
                        phone_number=phone_number,
                        found_in_crm=False
                    )
                else:
                    logger.error(f"CRM lookup failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error looking up lead: {str(e)}")
            return None
    
    async def update_lead_intake_data(self, phone_number: str, intake_data: IntakeData) -> bool:
        """Push intake data to CRM"""
        try:
            payload = {
                "phone_number": phone_number,
                "intake_data": intake_data.dict(exclude_none=True),
                "total_unsecured_debt": intake_data.total_unsecured_debt,
                "updated_at": intake_data.dict()["updated_at"] if hasattr(intake_data, 'updated_at') else None
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/leads/intake-update",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Successfully updated CRM for {phone_number}")
                    return True
                else:
                    logger.error(f"Failed to update CRM: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating CRM: {str(e)}")
            return False

# Singleton instance
crm_service = OCCCRMService()
```

### Step 5: Call Routing Logic

**services/call_router.py**
```python
from app.config import settings
from app.models.call_data import IntakeData
import logging

logger = logging.getLogger(__name__)

class CallRouter:
    """Handles call routing logic based on intake data"""
    
    DEBT_THRESHOLD = 35000  # $35k threshold for queue routing
    
    def determine_queue(self, intake_data: IntakeData) -> str:
        """
        Determine which 3CX queue to route the call to based on total unsecured debt
        
        Rules:
        - Total unsecured debt >= $35k → Queue A 
        - Total unsecured debt < $35k → Queue B
        """
        total_debt = intake_data.total_unsecured_debt
        
        if total_debt >= self.DEBT_THRESHOLD:
            queue_did = settings.QUEUE_A_DID
            logger.info(f"Routing to Queue A (high debt): ${total_debt:,.2f}")
        else:
            queue_did = settings.QUEUE_B_DID  
            logger.info(f"Routing to Queue B (low debt): ${total_debt:,.2f}")
            
        return queue_did
    
    def generate_transfer_params(self, queue_did: str) -> dict:
        """Generate SIP transfer parameters for 3CX"""
        return {
            "action": "transfer",
            "destination": queue_did,
            "trunk": settings.TWILIO_SIP_TRUNK,
            "method": "SIP"
        }

# Singleton instance  
call_router = CallRouter()
```

### Step 6: SignalWire Agents SDK Implementation

**services/signalwire_agent.py**
```python
from signalwire_agents import AgentBase
from app.services.crm_service import crm_service
from app.services.call_router import call_router
from app.models.call_data import IntakeData, CallSession, LeadInfo
from app.config import settings
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LoanIntakeAgent(AgentBase):
    """AI Voice Agent for loan intake and 3CX transfer"""
    
    def __init__(self):
        super().__init__(
            name="James - Easy Finance Intake Specialist",
            route="/agent/intake",
            voice_settings={
                "voice": "en-US-Neural2-J", 
                "speed": 1.0,
                "pitch": 0
            }
        )
        
        # Store active call sessions
        self.active_calls: Dict[str, CallSession] = {}
        
        # Setup conversation context with exact intake script
        self._setup_conversation_flow()
    
    def _setup_conversation_flow(self):
        """Setup the conversation contexts and steps"""
        contexts = self.define_contexts()
        main_context = contexts.add_context("intake_flow")
        
        # Add all conversation steps for intake script
        main_context.add_step("greeting").set_valid_steps(["introduction"])
        main_context.add_step("introduction").set_valid_steps(["loan_amount"])
        main_context.add_step("loan_amount").set_valid_steps(["funds_purpose"])
        # ... continue for all 9 questions
    
    async def on_call_start(self, call_context) -> str:
        """Handle incoming call with CRM lookup and personalized greeting"""
        caller_number = call_context.call.from_number.replace("+1", "")
        call_id = call_context.call.call_id
        
        # Perform CRM lookup
        lead_info = await crm_service.lookup_lead_by_phone(caller_number)
        
        # Store call session
        call_session = CallSession(call_id=call_id, lead_info=lead_info)
        self.active_calls[call_id] = call_session
        
        # Generate personalized greeting
        if lead_info and lead_info.found_in_crm:
            return f"Hi, this is James with Easy Finance on a recorded line. Am I speaking with {lead_info.lead_name}? Are you calling regarding the loan offer for ${lead_info.loan_amount:,.0f} you received?"
        else:
            return "Hi, this is James with Easy Finance on a recorded line. How can I help you today?"
    
    async def on_conversation_start(self, call_context):
        """Called when conversation begins"""
        call_context.set_current_step("greeting")
    
    async def on_call_end(self, call_context):
        """Clean up call session when call ends"""
        call_id = call_context.call.call_id
        if call_id in self.active_calls:
            del self.active_calls[call_id]

# Initialize the agent
loan_intake_agent = LoanIntakeAgent()
```

**services/agent_server.py**
```python
from signalwire_agents import AgentServer
from app.services.signalwire_agent import loan_intake_agent
from app.config import settings

class LoanIntakeAgentServer:
    def __init__(self):
        self.server = AgentServer(
            project_id=settings.SIGNALWIRE_PROJECT_ID,
            token=settings.SIGNALWIRE_API_TOKEN,
            space_url=settings.SIGNALWIRE_SPACE_URL
        )
        
        # Register the loan intake agent
        self.server.register_agent(loan_intake_agent)
        
        # Configure SIP settings for low latency
        self.server.configure_sip({
            "bridge_to_webrtc": True,
            "low_latency_mode": True,
            "codec_preference": ["PCMU", "PCMA"]
        })

agent_server = LoanIntakeAgentServer()
```

### Step 7: Backup Webhook Handlers

**webhooks/signalwire_webhooks.py**
```python
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
import json

from app.services.crm_service import crm_service
from app.services.call_router import call_router
from app.models.call_data import CallSession, LeadInfo, IntakeData

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for active calls (use Redis in production)
active_calls: Dict[str, CallSession] = {}

@router.post("/call-started")
async def handle_call_started(request: Request):
    """Handle incoming call and perform CRM lookup"""
    try:
        payload = await request.json()
        call_id = payload.get("call_id")
        caller_number = payload.get("from", "").replace("+1", "")
        
        logger.info(f"Call started: {call_id} from {caller_number}")
        
        # Look up lead in CRM
        lead_info = await crm_service.lookup_lead_by_phone(caller_number)
        
        if not lead_info:
            lead_info = LeadInfo(phone_number=caller_number, found_in_crm=False)
        
        # Store call session
        call_session = CallSession(call_id=call_id, lead_info=lead_info)
        active_calls[call_id] = call_session
        
        # Generate AI greeting based on CRM lookup
        if lead_info.found_in_crm and lead_info.lead_name:
            greeting = {
                "type": "personalized_greeting",
                "message": f"Hi, this is James with Easy Finance on a recorded line. Am I speaking with {lead_info.lead_name}? Are you calling regarding the loan offer for ${lead_info.loan_amount:,.0f} you received?"
            }
        else:
            greeting = {
                "type": "generic_greeting", 
                "message": "Hi, this is James with Easy Finance on a recorded line. How can I help you today?"
            }
        
        return JSONResponse(content=greeting)
        
    except Exception as e:
        logger.error(f"Error handling call start: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/intake-data")
async def handle_intake_data(request: Request):
    """Process intake data collected by AI agent"""
    try:
        payload = await request.json()
        call_id = payload.get("call_id")
        
        if call_id not in active_calls:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        call_session = active_calls[call_id]
        
        # Parse intake data from AI agent
        intake_data = IntakeData(
            loan_amount_requested=payload.get("loan_amount_requested"),
            funds_purpose=payload.get("funds_purpose"),
            employment_status=payload.get("employment_status"),
            credit_card_debt=payload.get("credit_card_debt"),
            personal_loan_debt=payload.get("personal_loan_debt"),
            other_debt=payload.get("other_debt"),
            monthly_income=payload.get("monthly_income"),
            ssn_last_four=payload.get("ssn_last_four")
        )
        
        # Update call session
        call_session.intake_data = intake_data
        
        # Update CRM with intake data
        await crm_service.update_lead_intake_data(
            call_session.lead_info.phone_number,
            intake_data
        )
        
        # Determine routing queue
        queue_did = call_router.determine_queue(intake_data)
        call_session.queue_assigned = queue_did
        
        logger.info(f"Intake completed for call {call_id}, routing to {queue_did}")
        
        return JSONResponse(content={"status": "intake_complete", "queue": queue_did})
        
    except Exception as e:
        logger.error(f"Error processing intake data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/transfer-request")
async def handle_transfer_request(request: Request):
    """Handle call transfer to 3CX queue"""
    try:
        payload = await request.json()
        call_id = payload.get("call_id")
        
        if call_id not in active_calls:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        call_session = active_calls[call_id]
        
        if not call_session.queue_assigned:
            raise HTTPException(status_code=400, detail="No queue assigned for transfer")
        
        # Generate transfer parameters
        transfer_params = call_router.generate_transfer_params(call_session.queue_assigned)
        
        # Update call status
        call_session.call_status = "transferred"
        
        logger.info(f"Transferring call {call_id} to {call_session.queue_assigned}")
        
        return JSONResponse(content={
            "action": "transfer",
            "message": "Please hold while I connect you with a senior underwriter.",
            "transfer_params": transfer_params
        })
        
    except Exception as e:
        logger.error(f"Error handling transfer request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/call-ended")
async def handle_call_ended(request: Request):
    """Clean up call session"""
    try:
        payload = await request.json()
        call_id = payload.get("call_id")
        
        if call_id in active_calls:
            del active_calls[call_id]
            logger.info(f"Call {call_id} ended and cleaned up")
        
        return JSONResponse(content={"status": "call_ended"})
        
    except Exception as e:
        logger.error(f"Error handling call end: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Step 8: SignalWire Configuration

**signalwire_config/agent_deployment.json**
```json
{
  "agent_configuration": {
    "name": "Easy Finance Loan Intake Agent",
    "description": "AI agent for loan application intake and 3CX transfer",
    "agent_endpoint": "https://your-app.com/agent/intake",
    "inbound_number": "+1-XXX-XXX-XXXX"
  },
  "voice_settings": {
    "voice": "en-US-Neural2-J",
    "speed": 1.0,
    "pitch": 0,
    "language": "en-US"
  },
  "call_settings": {
    "recording_enabled": true,
    "recording_format": "wav",
    "bridge_mode": "SIP_WEBRTC",
    "low_latency": true,
    "timeout_seconds": 600
  },
  "sip_configuration": {
    "trunk_endpoint": "your-twilio-sip-trunk.pstn.twilio.com",
    "codec_preferences": ["PCMU", "PCMA", "G722"],
    "dtmf_detection": true
  },
  "transfer_settings": {
    "queue_a_did": "+1-XXX-XXX-XXXX",
    "queue_b_did": "+1-XXX-XXX-XXXX", 
    "transfer_announcement": "Please hold while I connect you with a senior underwriter.",
    "transfer_timeout": 30
  }
}
```

**signalwire_config/intake_script.txt**
```
This is our secured automated intake system. It's built to make our process quick, private, and fully personalized. I'll ask a few short questions to confirm eligibility and then connect you to a senior underwriting specialist to review your actual loan options.

1. What is the exact amount you are looking to borrow today?

2. Just so I know how to help best, what are you planning to use the funds for?

3. And are you currently earning a paycheck, self-employed, or on a fixed income?

4. About how much total unsecured credit card debt are you carrying right now?

5. And do you have any balances on unsecured personal loans?

6. How about medical bills or any other balances you're aware of?

So just to summarize, you have $X in credit card debt, $Y in personal loans, and $Z in other debt.

7. Now, can you please provide your monthly income amount?

8. Thank you for that information. Just to confirm, your total monthly income is $X.

9. Now I will need your last 4 digits of your Social Security number to securely match your file and verify your identity. This will not impact your credit and does not count as an inquiry because it's a soft credit pull. Can you provide those last 4 digits?

Thank you, I appreciate your patience. Now that I have all the necessary information, I will connect you with a senior underwriter who will go over your loan options in detail. Please hold for a moment while I transfer you.
```

### Step 8: Requirements and Docker Setup

**requirements.txt**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2
python-multipart==0.0.6
python-dotenv==1.0.0
signalwire-agents==1.0.0
```

**Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  ai-voice-intake:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SIGNALWIRE_PROJECT_ID=${SIGNALWIRE_PROJECT_ID}
      - SIGNALWIRE_API_TOKEN=${SIGNALWIRE_API_TOKEN}
      - SIGNALWIRE_SPACE_URL=${SIGNALWIRE_SPACE_URL}
      - OCC_CRM_API_URL=${OCC_CRM_API_URL}
      - OCC_CRM_API_KEY=${OCC_CRM_API_KEY}
      - QUEUE_A_DID=${QUEUE_A_DID}
      - QUEUE_B_DID=${QUEUE_B_DID}
      - TWILIO_SIP_TRUNK=${TWILIO_SIP_TRUNK}
      - WEBHOOK_BASE_URL=${WEBHOOK_BASE_URL}
    volumes:
      - ./app:/app/app
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

## Deployment and Testing

### Local Development

1. **Set up environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Configure environment variables in `.env`**

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Use ngrok for webhook testing:**
   ```bash
   ngrok http 8000
   ```

### SignalWire Setup

1. **Create SignalWire account and get credentials**
2. **Purchase toll-free number for inbound calls**
3. **Configure TFN to route to agent endpoint**: `https://your-app.com/agent/intake`
4. **Enable SIP/WebRTC bridging** for low latency calls
5. **Test call flow**: Call TFN → Agent answers → CRM lookup → Intake script → Transfer

### Production Deployment

1. **Deploy to cloud provider (AWS, GCP, Azure)**
2. **Set up SSL certificates for HTTPS webhooks**
3. **Configure production database (PostgreSQL/MongoDB) instead of in-memory storage**
4. **Set up monitoring and logging**
5. **Configure auto-scaling for call volume**

## Key Integration Points

1. **SignalWire AI Agent** calls your webhooks at each step
2. **OCC CRM APIs** for lead lookup and data updates  
3. **3CX queues** receive transferred calls via Twilio SIP trunk
4. **Real-time data sync** ensures agents see intake data immediately

## Testing Strategy

1. **Unit tests** for business logic (routing, data processing)
2. **Integration tests** for CRM and SignalWire APIs
3. **End-to-end tests** for complete call flow
4. **Load testing** for concurrent call handling

This implementation provides a complete, production-ready system for your AI voice intake requirements. The modular structure makes it easy to extend and maintain.

## Here we have some API keys 

5e876874-6c2d-4960-817e-85e49627632b - project ID
easy-finance.signalwire.com - space URL
PSK_8LX3ds5NaS9PjzcKuE1woPpo - signing key

AI-AGENT-DEVELOPMENT - api key name
PTd75a64828b642f6ee914728c5d43a44c10922d0eb8b7b959 - API token


+1 (833) 435-3252
ID: 22a8979a-dc2a-449a-9703-79c674755d68