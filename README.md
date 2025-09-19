# AI Voice Intake Agent

An intelligent voice agent built with SignalWire and FastAPI that handles loan application calls, performs automated intake, and routes calls to appropriate queues based on debt thresholds.

## Features

- **Automated Call Handling**: AI-powered voice agent answers inbound calls
- **CRM Integration**: Real-time lookup and data sync with OCC CRM
- **Personalized Greetings**: Uses CRM data for customized caller interactions
- **Structured Intake**: Follows precise script to collect loan information
- **Smart Routing**: Routes calls to appropriate 3CX queues based on $35k debt threshold
- **Real-time Sync**: All data synchronized with CRM in real-time

## Architecture

```
Lead calls TFN → SignalWire AI Agent → FastAPI Backend → OCC CRM
                      ↓
              Transfer to 3CX Queue (via Twilio SIP)
```

## Technology Stack

- **Backend**: Python FastAPI
- **AI Voice**: SignalWire Agents SDK with real-time conversation control
- **CRM**: OCC CRM API integration
- **Call Transfer**: Twilio SIP trunk to 3CX
- **Deployment**: Docker + cloud hosting

## Quick Start

### Prerequisites

- Python 3.11+
- Conda (recommended)
- SignalWire account
- OCC CRM access
- 3CX system with SIP trunk

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-voice-intake-agent
   ```

2. **Create conda environment**
   ```bash
   conda create -n ai-voice-intake python=3.11
   conda activate ai-voice-intake
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and configuration
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual container
docker build -t ai-voice-intake .
docker run -p 8000:8000 --env-file .env ai-voice-intake
```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SIGNALWIRE_PROJECT_ID` | SignalWire project ID | `5e876874-6c2d-4960-817e-85e49627632b` |
| `SIGNALWIRE_API_TOKEN` | SignalWire API token | `PTd75a64828b642f6...` |
| `SIGNALWIRE_SPACE_URL` | SignalWire space URL | `easy-finance.signalwire.com` |
| `OCC_CRM_API_URL` | OCC CRM API endpoint | `https://api.occcrm.com/v1` |
| `OCC_CRM_API_KEY` | OCC CRM API key | `your_crm_api_key` |
| `QUEUE_A_DID` | 3CX queue for high debt (≥$35k) | `+1234567890` |
| `QUEUE_B_DID` | 3CX queue for low debt (<$35k) | `+1234567891` |
| `TWILIO_SIP_TRUNK` | Twilio SIP trunk URL | `sip:trunk@your-twilio.pstn.twilio.com` |

### SignalWire Setup

1. **Purchase toll-free number** from SignalWire console
2. **Configure agent endpoint**: Point TFN to `https://your-app.com/agent/intake`
3. **Set up SIP bridging** for low-latency (SIP/WebRTC mode)
4. **Configure voice settings** using `signalwire_config/ai_agent_config.json`

## API Endpoints

### Health Check
```
GET /health
```

### SignalWire Agent Endpoints
- `POST /agent/intake` - Main AI agent endpoint for call handling
- `POST /webhooks/signalwire/call-started` - Backup webhook for call events  
- `POST /webhooks/signalwire/intake-data` - Process collected data
- `POST /webhooks/signalwire/transfer-request` - Handle call transfers
- `POST /webhooks/signalwire/call-ended` - Cleanup call sessions

## Call Flow & How Calls Start

### Call Initiation Process
```
Lead dials TFN → SignalWire Platform → Agent Server (/agent/intake) → AI Conversation → 3CX Transfer
```

### Step-by-Step Flow
1. **Call Setup**: Lead dials SignalWire toll-free number
2. **Agent Activation**: SignalWire routes to `https://your-app.com/agent/intake`
3. **CRM Lookup**: `on_call_start()` performs real-time CRM lookup by phone number
4. **Personalized Greeting**: 
   - Found: "Hi, this is James with Easy Finance. Am I speaking with [Name]? Are you calling about the $[Amount] loan offer?"
   - Not found: "Hi, this is James with Easy Finance. How can I help you today?"
5. **Intake Script**: AI follows exact 9-question script using conversation contexts
6. **Data Collection**: Real-time sync with OCC CRM during conversation
7. **Debt Calculation**: Automatically calculates total unsecured debt
8. **Smart Routing**: Routes to Queue A (≥$35k) or Queue B (<$35k)
9. **SIP Transfer**: "Please hold while I connect you with a senior underwriter"
10. **Cleanup**: Session cleanup on call end

### Starting the System
```bash
# Development with ngrok (for SignalWire testing)
ngrok http 8000  # Get HTTPS URL
# Update SignalWire TFN to point to: https://abc123.ngrok.io/agent/intake

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
# Configure SignalWire TFN to: https://your-domain.com/agent/intake
```

## Routing Logic

- **Queue A**: Total unsecured debt ≥ $35,000
- **Queue B**: Total unsecured debt < $35,000

## Project Structure

```
ai-voice-intake/
├── main.py                     # FastAPI application (root level)
├── app/
│   ├── config.py               # Configuration
│   ├── models/
│   │   ├── call_data.py        # Call data models
│   │   └── crm_models.py       # CRM models
│   ├── services/
│   │   ├── signalwire_agent.py # SignalWire Agents SDK implementation
│   │   ├── agent_server.py     # Agent server management
│   │   ├── crm_service.py      # CRM integration
│   │   └── call_router.py      # Call routing logic
│   └── webhooks/
│       └── signalwire_webhooks.py # Backup webhook handlers
├── signalwire_config/
│   ├── ai_agent_config.json    # AI agent configuration
│   └── intake_script.txt       # Intake script
├── requirements.txt            # Dependencies
├── Dockerfile                  # Docker configuration
└── docker-compose.yml         # Docker Compose setup
```

## Development

### Local Development
```bash
# Activate environment
conda activate ai-voice-intake

# Run with auto-reload (main.py in root)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test with ngrok for webhooks
ngrok http 8000
```

### Testing
```bash
# Health check
curl http://localhost:8000/health

# Expected response
{"status": "healthy", "service": "ai-voice-intake"}
```

## Production Deployment

1. **Set up HTTPS** (required for SignalWire webhooks)
2. **Configure production database** (replace in-memory storage)
3. **Set up monitoring and logging**
4. **Configure auto-scaling** for call volume
5. **Update webhook URLs** in SignalWire configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


