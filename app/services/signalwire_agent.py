from signalwire_agents import AgentBase, SwaigFunctionResult
from app.services.crm_service import crm_service
from app.services.call_router import call_router
from app.services.intake_handlers import IntakeStepHandlers
from app.services.conversation_config import IntakeConversationConfig
from app.models.call_data import CallSession, LeadInfo
from app.config import settings
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
print('voice id: ', settings.ELEVEN_LABS_VOICE_ID)
class LoanIntakeAgent(AgentBase):
    """Clean AI Voice Agent for loan intake and 3CX transfer"""

    def __init__(self, **kwargs):

        super().__init__(
            name="James - Easy Finance Intake Specialist",
            **kwargs
        )

        # Add language/voice configuration (required for voice AI agents to enable speaking and fillers)
        self.add_language(
            name="English (US)",
            code="en-US",
            voice=settings.ELEVEN_LABS_VOICE_ID,
            engine="elevenlabs", 
            speech_fillers=[
                "Let me check that...", 
                "One moment please...",  
                "uhh ha,",
                "aah ha,",
                "hmm...",
                "let's see,"
            ],
            function_fillers=["I'm looking that up...", "Let me check that..."]
        )

        # Set AI parameters to enable the AI section (use a supported model)
        self.set_params({
            "ai_model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 150
        })

        # Add core skills (this is what creates the AI sections with POM and SWAIG)
        self.add_skill("datetime")
        self.add_skill("math")

        # Store active call sessions
        self.active_calls: Dict[str, CallSession] = {}

        # Initialize step handlers with access to active calls
        self.step_handlers = IntakeStepHandlers(self.active_calls)

        # Get conversation configuration
        self.conversation_config = IntakeConversationConfig()
        self.intake_script = self.conversation_config.get_intake_script()


        # Setup agent prompt and capabilities
        self._setup_agent_prompt()

        # Set the main prompt for the AI verb
        self.set_prompt_text("You are James, an AI voice agent for Easy Finance specializing in loan intake. Conduct professional loan application interviews following the structured conversation flow.")

        # Setup conversation flow
        self._setup_conversation_flow()

        # Enable debug routes for testing
        self.enable_debug_routes()

    def _setup_agent_prompt(self):
        """Setup agent prompt using Prompt Object Model (POM)"""
        # Add role section
        self.prompt_add_section(
            "Role",
            "You are James, an AI voice agent specializing in loan intake for Easy Finance. You conduct professional, efficient loan application interviews."
        )

        # Add capabilities section
        self.prompt_add_section(
            "Loan Intake Capabilities",
            "You can help customers through the complete loan application process.",
            bullets=[
                "Collect exact loan amount requested",
                "Gather debt information for eligibility assessment",
                "Record employment and income details",
                "Securely collect SSN verification",
                "Route calls to appropriate underwriting queues"
            ]
        )

        # Add conversation guidelines
        self.prompt_add_section(
            "Conversation Guidelines",
            "Follow these principles during loan intake calls:",
            bullets=[
                "Maintain professional, friendly demeanor throughout",
                "Ask questions clearly and wait for complete responses",
                "Confirm all financial amounts for accuracy",
                "Explain the secure nature of the process",
                "Prepare customer for transfer to underwriter"
            ]
        )

    def _setup_conversation_flow(self):
        """Setup the conversation contexts and steps using configuration"""
        contexts = self.define_contexts()
        main_context = contexts.add_context("default")
        
        # Get step definitions from configuration
        steps = self.conversation_config.get_conversation_steps()
        
        for step_config in steps:
            step = main_context.add_step(step_config["name"])
            
            # Set step text from script
            text_path = step_config["text"]
            if "." in text_path:
                # Handle nested paths like "questions.loan_amount"
                parts = text_path.split(".")
                text = self.intake_script
                for part in parts:
                    text = text[part]
            else:
                # Handle direct keys like "intro"
                text = self.intake_script[text_path]
            
            step.set_text(text)
            
            # Set criteria if specified
            if "criteria" in step_config:
                step.set_step_criteria(step_config["criteria"])
            
            # Set valid next steps
            if step_config["next_steps"]:
                step.set_valid_steps(step_config["next_steps"])
    
    async def on_call_start(self, call_context) -> str:
        """Handle incoming call with CRM lookup and personalized greeting"""
        try:
            # Extract call information from context
            caller_number = call_context.call.from_number.replace("+1", "")
            call_id = call_context.call.call_id
            
            logger.info(f"Call started: {call_id} from {caller_number}")
            
            # Perform CRM lookup
            lead_info = await crm_service.lookup_lead_by_phone(caller_number)
            
            if not lead_info:
                lead_info = LeadInfo(phone_number=caller_number, found_in_crm=False)
            
            # Store call session
            call_session = CallSession(call_id=call_id, lead_info=lead_info)
            self.active_calls[call_id] = call_session
            
            # Generate personalized greeting
            if lead_info.found_in_crm and lead_info.lead_name:
                greeting = f"Hi, this is James with Easy Finance on a recorded line. Am I speaking with {lead_info.lead_name}? Are you calling regarding the loan offer for ${lead_info.loan_amount:,.0f} you received?"
            else:
                greeting = "Hi, this is James with Easy Finance on a recorded line. How can I help you today?"
            
            return greeting
            
        except Exception as e:
            logger.error(f"Error handling call start: {str(e)}")
            return "Hi, this is James with Easy Finance on a recorded line. How can I help you today?"
    
    async def on_call_end(self, call_context):
        """Clean up call session when call ends"""
        try:
            call_id = call_context.call.call_id
            if call_id in self.active_calls:
                del self.active_calls[call_id]
                logger.info(f"Call {call_id} ended and cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up call: {str(e)}")
    
    async def on_conversation_start(self, call_context):
        """Called when conversation begins - trigger CRM lookup and set initial context"""
        try:
            call_id = call_context.call.call_id
            
            # Set the conversation to start with greeting
            call_context.set_current_step("greeting")
            
            logger.info(f"Conversation started for call {call_id}")
            
        except Exception as e:
            logger.error(f"Error starting conversation: {str(e)}")
    
    # SWAIG Functions using @AgentBase.tool decorators
    @AgentBase.tool(
        name="collect_loan_amount",
        description="Collect and validate the loan amount from user response",
        parameters={
            "user_response": {
                "type": "string",
                "description": "The user's response containing the loan amount"
            },
            "call_id": {
                "type": "string", 
                "description": "The unique call identifier"
            }
        }
    )
    def collect_loan_amount(self, args, raw_data):
        """SWAIG function to collect loan amount"""
        return self.step_handlers.collect_loan_amount(args, raw_data)
    
    @AgentBase.tool(
        name="collect_debt_amounts",
        description="Collect credit card, personal loan, and other debt amounts",
        parameters={
            "cc_debt": {
                "type": "string",
                "description": "Credit card debt amount"
            },
            "personal_debt": {
                "type": "string",
                "description": "Personal loan debt amount"
            },
            "other_debt": {
                "type": "string", 
                "description": "Other debt amount (medical bills, etc.)"
            },
            "call_id": {
                "type": "string",
                "description": "The unique call identifier"
            }
        }
    )
    def collect_debt_amounts(self, args, raw_data):
        """SWAIG function to collect all debt amounts"""
        return self.step_handlers.collect_debt_amounts(args, raw_data)
    
    @AgentBase.tool(
        name="finalize_intake",
        description="Collect final information and prepare for transfer",
        parameters={
            "monthly_income": {
                "type": "string",
                "description": "Monthly income amount"
            },
            "ssn_last_four": {
                "type": "string",
                "description": "Last 4 digits of Social Security Number"
            },
            "call_id": {
                "type": "string",
                "description": "The unique call identifier"
            }
        }
    )
    def finalize_intake(self, args, raw_data):
        """SWAIG function to finalize intake and prepare transfer"""
        return self.step_handlers.finalize_intake(args, raw_data)
    
    async def execute_transfer(self, queue_did: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute call transfer to 3CX queue via Twilio SIP trunk"""
        try:
            # Get transfer parameters from call router
            base_params = call_router.generate_transfer_params(queue_did)
            
            # Configure SIP transfer with additional settings
            transfer_config = {
                **base_params,  # Include base transfer params
                "announce": "Please hold while I connect you with a senior underwriter.",
                "bridge_type": "SIP",  # Use SIP bridging for low latency
                "call_data": call_data  # Include call data for context
            }
            
            logger.info(f"Executing transfer to {queue_did} with data: {call_data.get('call_id', 'unknown')}")
            return transfer_config
            
        except Exception as e:
            logger.error(f"Error executing transfer: {str(e)}")
            raise


