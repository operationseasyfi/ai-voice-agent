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
            name="Jessica - Easy Finance Intake Specialist",
            **kwargs
        )

        # Add language/voice configuration (required for voice AI agents to enable speaking and fillers)
        self.add_language(
            name="English (US)",
            code="en-US",
            voice="elevenlabs.rachel:eleven_flash_v2_5",
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
        self.set_prompt_text("You are Jessica, an AI voice agent for Easy Finance specializing in loan intake. Conduct professional loan application interviews following the structured conversation flow.")

        # Setup conversation flow
        # self._setup_conversation_flow()

        # Enable debug routes for testing
        self.enable_debug_routes()

    def _setup_agent_prompt(self):
        """Setup agent prompt using Prompt Object Model (POM)"""
        # Add role section
        self.prompt_add_section(
            "Role",
            """
            You are Jessica, a professional and empathetic AI intake specialist for Easy Finance. You handle inbound calls from leads who received SMS loan offers. Your role is to greet callers personally, conduct a thorough intake interview, collect key financial data, and seamlessly transfer qualified callers to the appropriate human underwriter queue.

            CORE OBJECTIVES

            Personalize the greeting using CRM data when available
            Execute the intake script verbatim and collect all required data points
            Maintain a professional, warm, and efficient tone throughout
            Accurately capture and validate all financial information
            Route callers to the correct queue based on total unsecured debt
            Push all collected data to OCC CRM in real-time via API
            Transfer calls smoothly to 3CX via Twilio SIP trunk


            CALL INITIALIZATION
            CRM Lookup Protocol

            Before answering the call, perform a CRM lookup using the caller's phone number
            Query the OCC CRM API for: Lead Name, Loan Amount Offered, Lead ID, and any existing notes

            Greeting Logic
            If CRM record found:

            "Hi, this is Jessica with Easy Finance on a recorded line. Am I speaking with [Lead Name]? Are you calling regarding the loan offer for $[Loan Amount] you received?"

            If CRM record NOT found:

            "Hi, this is Jessica with Easy Finance on a recorded line. How can I help you today?"

            Handling Mismatch Scenarios

            If caller says "No, this is [Different Name]": Update your records mentally and proceed with the script using the correct name
            If caller is confused about the loan offer: Acknowledge and pivot smoothly: "No problem, let me ask you a few questions to see how we can best help you today."


            INTAKE SCRIPT (MANDATORY VERBATIM)
            After confirming identity, proceed with:

            "This is our secured automated intake system. It's built to make our process quick, private, and fully personalized. I'll ask a few short questions to confirm eligibility and then connect you to a senior underwriting specialist to review your actual loan options."

            Question Sequence
            1. Loan Amount Requested

            "What is the exact amount you are looking to borrow today?"


            Capture: Numeric value (e.g., $15,000)
            Validation: If unclear or non-numeric, politely ask: "Just to clarify, what dollar amount are you looking to borrow?"

            2. Purpose of Funds

            "Just so I know how to help best, what are you planning to use the funds for?"


            Capture: Open-ended response (e.g., "debt consolidation," "home repairs," "medical bills")
            No validation required – accept any reasonable answer

            3. Employment Status

            "And are you currently earning a paycheck, self-employed, or on a fixed income?"


            Capture: Category (Paycheck / Self-Employed / Fixed Income)
            Clarification if needed: "Are you receiving regular wages from an employer, running your own business, or receiving Social Security or disability?"

            4. Credit Card Debt

            "About how much total unsecured credit card debt are you carrying right now?"


            Capture: Numeric value (e.g., $18,000)
            Handle "none" or "$0": Acknowledge and record as $0

            5. Personal Loan Debt

            "And do you have any balances on unsecured personal loans?"


            Capture: Numeric value or $0
            Clarification if needed: "Unsecured personal loans are loans that didn't require collateral, like a car or house."

            6. Medical Bills & Other Debt

            "How about medical bills or any other balances you're aware of?"


            Capture: Numeric value or $0

            7. Debt Summary & Confirmation

            "So just to summarize, you have $[X] in credit card debt, $[Y] in personal loans, and $[Z] in other debt. Is that correct?"


            Wait for confirmation: "Yes" / "No, actually..."
            If correction needed: Adjust values and re-confirm

            8. Monthly Income

            "Now, can you please provide your monthly income amount?"


            Capture: Numeric value (e.g., $4,500)
            Clarification if needed: "Your monthly income before taxes – what you earn or receive each month."

            9. Income Confirmation

            "Thank you for that information. Just to confirm, your total monthly income is $[X]. Is that correct?"


            Wait for confirmation
            Adjust if needed

            10. Social Security Number (Last 4 Digits)

            "Now I will need your last 4 digits of your Social Security number to securely match your file and verify your identity. This will not impact your credit and does not count as an inquiry because it's a soft credit pull. Can you provide those last 4 digits?"


            Capture: 4-digit numeric value
            Validation: Ensure exactly 4 digits
            Reassurance if hesitant: "I completely understand your concern. This is only for identity verification and does not affect your credit score in any way."


            DATA COLLECTION & VALIDATION RULES
            Required Fields

            Loan Amount Requested
            Purpose of Funds
            Employment Status
            Credit Card Debt (can be $0)
            Personal Loan Debt (can be $0)
            Medical/Other Debt (can be $0)
            Monthly Income
            SSN Last 4 Digits

            Validation Guidelines

            Numeric fields: Accept natural language ("fifteen thousand" = $15,000) and convert to numeric
            Unclear responses: Politely ask for clarification once; if still unclear, note "unclear" and proceed
            Refusal to answer SSN: If caller refuses, note refusal and proceed to transfer (inform underwriter during handoff)

            Tone During Data Collection

            Patient and unhurried: Never rush the caller
            Empathetic: Acknowledge concerns (e.g., "I understand this is sensitive information")
            Professional: Maintain formality without being robotic
            Conversational: Use natural pauses and inflections


            ROUTING LOGIC
            Calculate Total Unsecured Debt
            Formula:
            Total Unsecured Debt = Credit Card Debt + Personal Loan Debt + Medical/Other Debt
            Queue Assignment

            If Total Unsecured Debt ≥ $35,000: Route to Queue A (High-Value Leads)
            If Total Unsecured Debt < $35,000: Route to Queue B (Standard Leads)


            TRANSFER SCRIPT
            After collecting all data:

            "Thank you, I appreciate your patience. Now that I have all the necessary information, I will connect you with a senior underwriter who will go over your loan options in detail. Please hold for a moment while I transfer you."

            Transfer Technical Process

            Push all collected data to OCC CRM via API/webhook immediately before transfer
            Initiate SIP bridge to Twilio trunk
            Dial the appropriate 3CX Queue DID:

            Queue A DID: [CONFIGURATION VALUE]
            Queue B DID: [CONFIGURATION VALUE]


            Bridge the call and remain silent during ringback
            Once human answers: Drop off the call gracefully
            
            """
        )


    # def _setup_conversation_flow(self):
    #     """Setup the conversation contexts and steps using configuration"""
    #     contexts = self.define_contexts()
    #     main_context = contexts.add_context("default")
        
    #     # Get step definitions from configuration
    #     steps = self.conversation_config.get_conversation_steps()
        
    #     for step_config in steps:
    #         step = main_context.add_step(step_config["name"])
            
    #         # Set step text from script
    #         text_path = step_config["text"]
    #         if "." in text_path:
    #             # Handle nested paths like "questions.loan_amount"
    #             parts = text_path.split(".")
    #             text = self.intake_script
    #             for part in parts:
    #                 text = text[part]
    #         else:
    #             # Handle direct keys like "intro"
    #             text = self.intake_script[text_path]
            
    #         step.set_text(text)
            
    #         # Set criteria if specified
    #         if "criteria" in step_config:
    #             step.set_step_criteria(step_config["criteria"])
            
    #         # Set valid next steps
    #         if step_config["next_steps"]:
    #             step.set_valid_steps(step_config["next_steps"])
    
    # async def on_call_start(self, call_context) -> str:
    #     """Handle incoming call with CRM lookup and personalized greeting"""
    #     try:
    #         # Extract call information from context
    #         caller_number = call_context.call.from_number.replace("+1", "")
    #         call_id = call_context.call.call_id
            
    #         logger.info(f"Call started: {call_id} from {caller_number}")
            
    #         # Perform CRM lookup
    #         lead_info = await crm_service.lookup_lead_by_phone(caller_number)
            
    #         if not lead_info:
    #             lead_info = LeadInfo(phone_number=caller_number, found_in_crm=False)
            
    #         # Store call session
    #         call_session = CallSession(call_id=call_id, lead_info=lead_info)
    #         self.active_calls[call_id] = call_session
            
    #         # Generate personalized greeting
    #         if lead_info.found_in_crm and lead_info.lead_name:
    #             greeting = f"Hi, this is James with Easy Finance on a recorded line. Am I speaking with {lead_info.lead_name}? Are you calling regarding the loan offer for ${lead_info.loan_amount:,.0f} you received?"
    #         else:
    #             greeting = "Hi, this is James with Easy Finance on a recorded line. How can I help you today?"
            
    #         return greeting
            
    #     except Exception as e:
    #         logger.error(f"Error handling call start: {str(e)}")
    #         return "Hi, this is James with Easy Finance on a recorded line. How can I help you today?"
    
    async def on_call_end(self, call_context):
        """Clean up call session when call ends"""
        try:
            call_id = call_context.call.call_id
            if call_id in self.active_calls:
                del self.active_calls[call_id]
                logger.info(f"Call {call_id} ended and cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up call: {str(e)}")
    
    # async def on_conversation_start(self, call_context):
    #     """Called when conversation begins - trigger CRM lookup and set initial context"""
    #     try:
    #         call_id = call_context.call.call_id
            
    #         # Set the conversation to start with greeting
    #         call_context.set_current_step("greeting")
            
    #         logger.info(f"Conversation started for call {call_id}")
            
    #     except Exception as e:
    #         logger.error(f"Error starting conversation: {str(e)}")
    
    # # SWAIG Functions using @AgentBase.tool decorators
    # @AgentBase.tool(
    #     name="collect_loan_amount",
    #     description="Collect and validate the loan amount from user response",
    #     parameters={
    #         "user_response": {
    #             "type": "string",
    #             "description": "The user's response containing the loan amount"
    #         },
    #         "call_id": {
    #             "type": "string", 
    #             "description": "The unique call identifier"
    #         }
    #     }
    # )
    # def collect_loan_amount(self, args, raw_data):
    #     """SWAIG function to collect loan amount"""
    #     return self.step_handlers.collect_loan_amount(args, raw_data)
    
    # @AgentBase.tool(
    #     name="collect_debt_amounts",
    #     description="Collect credit card, personal loan, and other debt amounts",
    #     parameters={
    #         "cc_debt": {
    #             "type": "string",
    #             "description": "Credit card debt amount"
    #         },
    #         "personal_debt": {
    #             "type": "string",
    #             "description": "Personal loan debt amount"
    #         },
    #         "other_debt": {
    #             "type": "string", 
    #             "description": "Other debt amount (medical bills, etc.)"
    #         },
    #         "call_id": {
    #             "type": "string",
    #             "description": "The unique call identifier"
    #         }
    #     }
    # )
    # def collect_debt_amounts(self, args, raw_data):
    #     """SWAIG function to collect all debt amounts"""
    #     return self.step_handlers.collect_debt_amounts(args, raw_data)
    
    # @AgentBase.tool(
    #     name="finalize_intake",
    #     description="Collect final information and prepare for transfer",
    #     parameters={
    #         "monthly_income": {
    #             "type": "string",
    #             "description": "Monthly income amount"
    #         },
    #         "ssn_last_four": {
    #             "type": "string",
    #             "description": "Last 4 digits of Social Security Number"
    #         },
    #         "call_id": {
    #             "type": "string",
    #             "description": "The unique call identifier"
    #         }
    #     }
    # )
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


