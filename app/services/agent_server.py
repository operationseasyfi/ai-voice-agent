from signalwire_agents import AgentServer
from app.services.signalwire_agent import loan_intake_agent
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class LoanIntakeAgentServer:
    """SignalWire Agent Server for handling inbound calls"""
    
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
            "codec_preference": ["PCMU", "PCMA"]  # High quality, low latency codecs
        })
        
        logger.info("SignalWire Agent Server initialized")
    
    def start(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the agent server"""
        logger.info(f"Starting SignalWire Agent Server on {host}:{port}")
        self.server.run(host=host, port=port)
    
    def get_app(self):
        """Get the FastAPI app for mounting"""
        return self.server.app

# Initialize the agent server
agent_server = LoanIntakeAgentServer()

# How to start calls - Documentation:
"""
CALL INITIATION PROCESS:

1. INBOUND CALL SETUP:
   - Lead dials your SignalWire toll-free number: +1-XXX-XXX-XXXX
   - SignalWire receives the call and routes it to your agent server
   - Agent server URL: https://your-app.com/agent/intake

2. CALL FLOW SEQUENCE:
   a) SignalWire → on_call_start() → CRM lookup → personalized greeting
   b) Agent → on_conversation_start() → sets context to "greeting" step  
   c) Agent → follows intake script through all 9 questions
   d) Agent → collects data → determines routing queue (A/B)
   e) Agent → transfers to 3CX via SIP trunk
   f) Agent → on_call_end() → cleanup

3. TO START RECEIVING CALLS:
   - Deploy this app to HTTPS endpoint (required by SignalWire)
   - Configure SignalWire phone number to point to: https://your-app.com/agent/intake
   - Set environment variables (SIGNALWIRE_PROJECT_ID, etc.)
   - Run: uvicorn main:app --host 0.0.0.0 --port 8000

4. TESTING:
   - Use ngrok for local testing: ngrok http 8000
   - Update SignalWire number config to point to ngrok URL
   - Call the SignalWire number to test full flow
"""