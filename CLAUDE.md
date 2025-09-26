# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Voice Intake Agent built with FastAPI and SignalWire Agents SDK that:
- Handles inbound loan application calls with real-time conversation control
- Performs CRM lookups for personalized greetings using on_call_start() handler
- Runs structured intake scripts with conversation contexts and steps
- Routes calls to appropriate 3CX queues based on debt amount ($35k threshold)
- Transfers calls via SIP/WebRTC bridging for low latency
- Syncs all data with OCC CRM in real-time

## Architecture

```
Lead calls TFN → SignalWire Platform → Agent Server (/agent/intake) → OCC CRM
                                          ↓
                                Transfer to 3CX Queue (via Twilio SIP)
```

## Technology Stack

- **Backend**: Python FastAPI
- **AI Voice**: SignalWire Agents SDK with real-time conversation control
- **CRM**: OCC CRM API integration
- **Call Transfer**: Twilio SIP trunk to 3CX
- **Deployment**: Docker + cloud hosting

## Development Commands

### Local Development Setup
```bash
# Create conda environment
conda create -n ai-voice-intake python=3.11
conda activate ai-voice-intake

# Install dependencies (includes signalwire-agents==1.0.0 and all FastAPI dependencies)
pip install -r requirements.txt

# Run development server (main.py is in root directory)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Remove conda environment (if needed)
conda deactivate
conda env remove -n ai-voice-intake
```

### Docker Commands
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run individual container
docker build -t ai-voice-intake .
docker run -p 8000:8000 --env-file .env ai-voice-intake
```

### Testing
```bash
# Health check endpoint
curl http://localhost:8000/health

# Test agent endpoint (requires ngrok for SignalWire testing)
ngrok http 8000
# Configure SignalWire TFN to point to: https://abc123.ngrok.io/agent/intake
# Call the SignalWire toll-free number to test full conversation flow
```

## Project Structure

```
ai-voice-intake/
├── main.py                     # FastAPI application entry point (root level)
├── app/
│   ├── config.py               # Configuration and environment variables
│   ├── models/
│   │   ├── call_data.py        # Pydantic models for call data
│   │   └── crm_models.py       # CRM data models
│   ├── services/
│   │   ├── signalwire_agent.py # SignalWire Agents SDK implementation
│   │   ├── agent_server.py     # Agent server with SIP/WebRTC config
│   │   ├── crm_service.py      # OCC CRM integration
│   │   └── call_router.py      # Call routing logic ($35k threshold)
│   └── webhooks/
│       └── signalwire_webhooks.py # Backup webhook handlers
├── signalwire_config/
│   ├── ai_agent_config.json    # AI Agent configuration
│   └── intake_script.txt       # Verbatim intake script
└── requirements.txt            # Python dependencies (pinned versions)
```

## Key Components

### Call Routing Logic
- **Queue A**: Total unsecured debt >= $35,000
- **Queue B**: Total unsecured debt < $35,000
- Located in `app/services/call_router.py:302`

### CRM Integration
- Lead lookup by phone number for personalized greetings
- Real-time intake data updates
- Located in `app/services/crm_service.py`

### API Endpoints
- `/agent/intake`: Main SignalWire Agents SDK endpoint for call handling
- `/webhooks/signalwire/call-started`: Backup CRM lookup endpoint
- `/webhooks/signalwire/intake-data`: Process collected intake data
- `/webhooks/signalwire/transfer-request`: Handle 3CX queue transfer  
- `/webhooks/signalwire/call-ended`: Cleanup call session

### How Calls Start
1. Lead dials SignalWire toll-free number
2. SignalWire routes to `/agent/intake` endpoint
3. `on_call_start()` performs CRM lookup and generates personalized greeting
4. `on_conversation_start()` initiates structured intake script
5. Agent follows conversation contexts through all 9 questions
6. Real-time debt calculation and CRM sync
7. SIP transfer to appropriate 3CX queue based on $35k threshold

## Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:
- **SignalWire**: Project ID, API token, space URL
- **OCC CRM**: API URL and key
- **3CX Transfer**: Queue DIDs and Twilio SIP trunk
- **App**: Host, port, webhook base URL

### SignalWire AI Agent
- Configuration: `signalwire_config/ai_agent_config.json`
- Intake script: `signalwire_config/intake_script.txt`
- Webhook URLs must point to your deployed application

## API Keys Location
The guide mentions API keys in `ai_voice_intake_guide.md:670-675`:
- Project ID: `5e876874-6c2d-4960-817e-85e49627632b`
- Space URL: `easy-finance.signalwire.com`
- API Token: `PTd75a64828b642f6ee914728c5d43a44c10922d0eb8b7b959`

## Data Models

### IntakeData Model
Contains all collected information with automatic debt calculation:
- `total_unsecured_debt` property sums credit card, personal loan, and other debt
- Used for routing decisions in call_router.py

### CallSession Model
Tracks active calls with lead info, intake data, and routing decisions
- Stored in-memory (consider Redis for production)

## Deployment Notes

- Use HTTPS for webhook endpoints (SignalWire requirement)
- Configure production database instead of in-memory storage
- Set up monitoring and logging for call volume
- Test end-to-end call flow before production deployment

## Remaining Implementation Tasks

### 1. **Complete SignalWire Agent Conversation Handlers**
- Implement step handlers for each of the 9 intake questions
- Add data extraction logic from user responses during conversation
- Implement step transition logic and response validation
- Add real-time data collection and CRM sync during conversation
- Handle conversation errors and retry logic

### 2. **Twilio SIP Transfer Implementation** 
- Complete `execute_transfer()` method with actual SignalWire SDK calls
- Add Twilio SIP trunk authentication and credentials
- Implement SIP transfer to 3CX queues (Queue A/B based on debt threshold)
- Add transfer error handling and fallback logic
- Test actual call transfers to 3CX system

### 3. **Testing and Integration**
- End-to-end testing: TFN call → Agent conversation → CRM sync → 3CX transfer
- Test personalized greetings with real CRM data
- Validate debt calculation and queue routing logic
- Test call quality and latency with SIP/WebRTC bridging
- Load testing for concurrent call handling

### 4. **Production Readiness**
- Replace in-memory call storage with Redis/database
- Add comprehensive error handling and logging
- Set up monitoring and alerting for call failures
- Configure auto-scaling for high call volume
- Security review and webhook signature validation
- ok just stop we will do twillio work later
- save what things remaining