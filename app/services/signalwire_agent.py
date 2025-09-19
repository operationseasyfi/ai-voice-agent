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
        
        # Intake script steps
        self.intake_script = {
            "intro": "This is our secured automated intake system. It's built to make our process quick, private, and fully personalized. I'll ask a few short questions to confirm eligibility and then connect you to a senior underwriting specialist to review your actual loan options.",
            "questions": [
                "What is the exact amount you are looking to borrow today?",
                "Just so I know how to help best, what are you planning to use the funds for?", 
                "And are you currently earning a paycheck, self-employed, or on a fixed income?",
                "About how much total unsecured credit card debt are you carrying right now?",
                "And do you have any balances on unsecured personal loans?",
                "How about medical bills or any other balances you're aware of?",
                "Now, can you please provide your monthly income amount?",
                "Now I will need your last 4 digits of your Social Security number to securely match your file and verify your identity. This will not impact your credit and does not count as an inquiry because it's a soft credit pull. Can you provide those last 4 digits?"
            ],
            "transfer": "Thank you, I appreciate your patience. Now that I have all the necessary information, I will connect you with a senior underwriter who will go over your loan options in detail. Please hold for a moment while I transfer you."
        }
        
        # Setup conversation context
        self._setup_conversation_flow()
    
    def _setup_conversation_flow(self):
        """Setup the conversation contexts and steps"""
        contexts = self.define_contexts()
        main_context = contexts.add_context("intake_flow")
        
        # Greeting step
        main_context.add_step("greeting") \
            .set_text("Personalizing greeting based on CRM lookup...") \
            .set_valid_steps(["introduction"])
        
        # Introduction step
        main_context.add_step("introduction") \
            .set_text(self.intake_script["intro"]) \
            .set_valid_steps(["loan_amount"])
        
        # Loan amount question
        main_context.add_step("loan_amount") \
            .set_text(self.intake_script["questions"][0]) \
            .set_step_criteria("Amount collected and confirmed") \
            .set_valid_steps(["funds_purpose"])
        
        # Funds purpose question  
        main_context.add_step("funds_purpose") \
            .set_text(self.intake_script["questions"][1]) \
            .set_step_criteria("Purpose collected") \
            .set_valid_steps(["employment"])
        
        # Employment question
        main_context.add_step("employment") \
            .set_text(self.intake_script["questions"][2]) \
            .set_step_criteria("Employment status collected") \
            .set_valid_steps(["credit_card_debt"])
        
        # Credit card debt question
        main_context.add_step("credit_card_debt") \
            .set_text(self.intake_script["questions"][3]) \
            .set_step_criteria("Credit card debt amount collected") \
            .set_valid_steps(["personal_loan_debt"])
        
        # Personal loan debt question
        main_context.add_step("personal_loan_debt") \
            .set_text(self.intake_script["questions"][4]) \
            .set_step_criteria("Personal loan debt collected") \
            .set_valid_steps(["other_debt"])
        
        # Other debt question
        main_context.add_step("other_debt") \
            .set_text(self.intake_script["questions"][5]) \
            .set_step_criteria("Other debt collected") \
            .set_valid_steps(["debt_summary"])
        
        # Debt summary
        main_context.add_step("debt_summary") \
            .set_text("Summarizing debt amounts...") \
            .set_step_criteria("Debt summary confirmed") \
            .set_valid_steps(["monthly_income"])
        
        # Monthly income question
        main_context.add_step("monthly_income") \
            .set_text(self.intake_script["questions"][6]) \
            .set_step_criteria("Monthly income collected and confirmed") \
            .set_valid_steps(["ssn_last_four"])
        
        # SSN last 4 question
        main_context.add_step("ssn_last_four") \
            .set_text(self.intake_script["questions"][7]) \
            .set_step_criteria("SSN last 4 digits collected") \
            .set_valid_steps(["transfer"])
        
        # Transfer step
        main_context.add_step("transfer") \
            .set_text(self.intake_script["transfer"]) \
            .set_step_criteria("Transfer initiated")
    
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
    
    async def collect_intake_data(self, conversation_data: Dict[str, Any]) -> IntakeData:
        """Extract and validate intake data from conversation"""
        try:
            intake_data = IntakeData(
                loan_amount_requested=conversation_data.get("loan_amount"),
                funds_purpose=conversation_data.get("funds_purpose"),
                employment_status=conversation_data.get("employment_status"),
                credit_card_debt=conversation_data.get("credit_card_debt"),
                personal_loan_debt=conversation_data.get("personal_loan_debt"),
                other_debt=conversation_data.get("other_debt"),
                monthly_income=conversation_data.get("monthly_income"),
                ssn_last_four=conversation_data.get("ssn_last_four")
            )
            
            # Update CRM with intake data
            caller_number = conversation_data.get("caller_number")
            if caller_number:
                await crm_service.update_lead_intake_data(caller_number, intake_data)
            
            logger.info(f"Intake data collected: total debt ${intake_data.total_unsecured_debt:,.2f}")
            return intake_data
            
        except Exception as e:
            logger.error(f"Error collecting intake data: {str(e)}")
            raise
    
    async def determine_transfer_queue(self, intake_data: IntakeData) -> str:
        """Determine which 3CX queue to transfer to based on debt amount"""
        try:
            queue_did = call_router.determine_queue(intake_data)
            
            logger.info(f"Transfer queue determined: {queue_did} for debt ${intake_data.total_unsecured_debt:,.2f}")
            return queue_did
            
        except Exception as e:
            logger.error(f"Error determining transfer queue: {str(e)}")
            # Default to Queue B for errors
            return settings.QUEUE_B_DID
    
    async def execute_transfer(self, queue_did: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute call transfer to 3CX queue via Twilio SIP trunk"""
        try:
            transfer_params = call_router.generate_transfer_params(queue_did)
            
            # Configure SIP transfer
            transfer_config = {
                "action": "transfer",
                "destination": queue_did,
                "method": "SIP",
                "trunk": settings.TWILIO_SIP_TRUNK,
                "announce": "Please hold while I connect you with a senior underwriter.",
                "bridge_type": "SIP"  # Use SIP bridging for low latency
            }
            
            logger.info(f"Executing transfer to {queue_did}")
            return transfer_config
            
        except Exception as e:
            logger.error(f"Error executing transfer: {str(e)}")
            raise

# Initialize the agent
loan_intake_agent = LoanIntakeAgent()