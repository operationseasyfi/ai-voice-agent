from signalwire_agents import AgentBase, SwaigFunctionResult
from app.services.call_router import call_router
from app.services.call_record_service import call_record_service
from app.models.call_records import TransferTier, DisconnectionReason
from app.config import settings
import logging
import asyncio
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# DNC (Do Not Call) detection phrases
DNC_PHRASES = [
    "remove me from the list",
    "remove me from your list",
    "take me off the list",
    "take me off your list",
    "stop calling me",
    "stop calling",
    "do not call",
    "don't call me",
    "don't call",
    "quit calling",
    "remove my number",
    "delete my number",
    "unsubscribe",
    "opt out",
    "opt-out",
    "no more calls",
    "never call again",
    "put me on do not call",
    "add me to do not call",
]


class LoanIntakeAgent(AgentBase):
    """
    AI Voice Agent for loan intake with structured conversation flow.
    Features:
    - 3-tier transfer routing based on total debt
    - DNC phrase detection
    - Comprehensive data collection
    """

    def __init__(self, **kwargs):
        # Initialize the base agent with a name
        super().__init__(
            name="Jessica - Easy Finance Specialist",
            route="/webhook",
            **kwargs
        )
    
    def _check_basic_auth(self, request) -> bool:
        """
        Override authentication check to allow SignalWire webhook requests.
        SignalWire doesn't send Basic Auth credentials by default.
        For production, consider implementing SignalWire signature verification instead.
        """
        # Always allow requests - SignalWire webhooks don't include Basic Auth
        logger.info("✅ Allowing webhook request (auth bypassed for SignalWire)")
        return True

        # Configure voice - using ElevenLabs Turbo v2.5 for best quality + low latency
        self.add_language(
            name="English (US)",
            code="en-US",
            voice="elevenlabs.rachel:eleven_turbo_v2_5"  # Changed from eleven_flash_v2_5
        )

        self.prompt_add_section(
            'personality',
            """You are Jessica, a professional specialist for Easy Finance on a recorded line. You handle inbound calls from leads who received SMS loan offers.

            CRITICAL RULES:
            - Follow the intake script EXACTLY as written - do not add extra words or improvise
            - Ask ONE question at a time and WAIT for the caller's full response
            - MANDATORY: You MUST call the collection function IMMEDIATELY after receiving each answer - never skip this step
            - The conversation CANNOT proceed until you call the required collection function for each step
            - Be professional, warm, and efficient
            - Keep your responses brief and natural
            - If the caller says anything like "remove me from the list", "stop calling", "do not call", etc., 
              IMMEDIATELY call the handle_dnc_request function
            """
        )

        # Setup conversation flow
        self._setup_conversation_flow()

        # Enable debug routes for testing
        self.enable_debug_routes()

    def _get_intake_state(self, raw_data):
        """Get current intake progress from global_data"""
        global_data = raw_data.get('global_data', {})

        default_state = {
            # Call metadata
            "call_id": raw_data.get("call_id"),
            "caller_number": raw_data.get("caller_id_num", "").replace("+1", ""),
            "lead_name": None,
            
            # Multi-tenant tracking
            "client_id": None,
            "agent_id": None,

            # Question answers (all nullable initially)
            "loan_amount": None,
            "funds_purpose": None,
            "employment_status": None,
            "credit_card_debt": None,
            "personal_loan_debt": None,
            "other_debt": None,
            "monthly_income": None,
            "ssn_last_four": None,

            # Calculated values
            "total_debt": 0.0,
            
            # Transfer tracking
            "transfer_tier": None,
            "transfer_did": None,
            "transfer_initiated": False,
            
            # DNC tracking
            "is_dnc": False,
            "dnc_phrase": None,

            # Progress tracking
            "answered": [],
        }
        lead_data = global_data.get('caller_data', default_state)
        
        # Clean up answered list
        if 'answered' in lead_data and isinstance(lead_data['answered'], list):
            for key, val in lead_data.items():
                if val is None and key in lead_data['answered']:
                    lead_data['answered'].remove(key)

        return lead_data, global_data

    def _save_intake_state(self, result: SwaigFunctionResult, lead_data: dict, global_data):
        """Save intake state to global_data"""
        # Remove duplicates while preserving order
        if 'answered' in lead_data and isinstance(lead_data['answered'], list):
            lead_data['answered'] = list(dict.fromkeys(lead_data['answered']))
        
        logger.info(f"Saving intake state: {lead_data}")
        global_data['caller_data'] = lead_data
        result.update_global_data(global_data)
        return result

    def _check_for_dnc(self, text: str) -> Optional[str]:
        """Check if text contains DNC phrases. Returns the detected phrase or None."""
        if not text:
            return None
        text_lower = text.lower()
        for phrase in DNC_PHRASES:
            if phrase in text_lower:
                return phrase
        return None

    def _calculate_total_debt(self, intake_state: dict) -> float:
        """Calculate total unsecured debt from intake state"""
        return (
            float(intake_state.get("credit_card_debt") or 0) +
            float(intake_state.get("personal_loan_debt") or 0) +
            float(intake_state.get("other_debt") or 0)
        )

    def _determine_transfer_info(self, intake_state: dict) -> Dict[str, Any]:
        """Determine transfer tier and DID based on total debt"""
        total_debt = self._calculate_total_debt(intake_state)
        transfer_info = call_router.get_transfer_info(total_debt)
        return transfer_info

    def _setup_conversation_flow(self):
        # Define contexts (conversation containers)
        contexts = self.define_contexts()
        intake_context = (
            contexts.add_context("default")
            .add_section("Goal", "Complete the loan intake process by following the EXACT script in sequence")
            .add_section("Critical Rules", """
                - Ask ONLY ONE question per step - never combine questions
                - WAIT for the caller's complete response before proceeding
                - IMMEDIATELY call the collection function after receiving each answer - this is MANDATORY
                - Do NOT proceed to the next step until the collection function has been called
                - Do NOT skip any steps or questions
                - Do NOT add extra commentary, explanations, or questions
                - Do not repeat questions if you get their answer
                - If caller requests to be removed from calling list, call handle_dnc_request immediately
                - Sequence: greeting → introduction → loan_amount → funds_purpose → employment → credit_card_debt → personal_loan_debt → other_debt → debt_summary → monthly_income → income_confirmation → transfer
            """)
        )

        # ============================================
        # STEP 1: GREETING
        # ============================================
        intake_context.add_step("greeting") \
            .add_section("Current Task", "Greet the caller and collect their name") \
            .add_bullets("Process", [
                "Say: 'Hi, this is Jessica with Easy Finance on a recorded line. May I have your name please?'",
                "WAIT for their name response",
                "NEVER use numbers or phone numbers as a name",
                "REMEMBER to call collect_caller_name function after they tell their name",
                "Do NOT move to next step until function is called",
                "If they ask to be removed from the list, call handle_dnc_request immediately"
            ]) \
            .set_step_criteria("collect_caller_name function called successfully") \
            .set_functions(["collect_caller_name", "handle_dnc_request"]) \
            .set_valid_steps(["introduction"])

        # ============================================
        # STEP 2: INTRODUCTION
        # ============================================
        intake_context.add_step("introduction") \
            .add_section("Current Task", "Explain the automated intake system") \
            .add_bullets("Process", [
                "Say EXACTLY: 'This is our secured automated intake system. It's built to make our process quick, private, and fully personalized. I'll ask a few short questions to confirm eligibility and then connect you to a senior underwriting specialist to review your actual loan options.'",
            ]) \
            .set_step_criteria("Introduction script delivered") \
            .set_functions(["handle_dnc_request"]) \
            .set_valid_steps(["loan_amount"])

        # ============================================
        # STEP 3: LOAN AMOUNT (Question 1)
        # ============================================
        intake_context.add_step("loan_amount") \
            .add_section("Current Task", "Ask Question 1 from the script") \
            .add_bullets("Process", [
                "Ask EXACTLY: 'What is the exact amount you are looking to borrow today?'",
                "WAIT for their response",
                "Do NOT add extra commentary",
                "IMMEDIATELY call collect_loan_amount function with the amount they provided",
                "CRITICAL: Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_loan_amount function called successfully") \
            .set_functions(["collect_loan_amount", "handle_dnc_request"]) \
            .set_valid_steps(["funds_purpose"])

        # ============================================
        # STEP 4: PURPOSE OF FUNDS (Question 2)
        # ============================================
        intake_context.add_step("funds_purpose") \
            .add_section("Current Task", "Ask Question 2 from the script") \
            .add_bullets("Process", [
                "Ask EXACTLY: 'Just so I know how to help best, what are you planning to use the funds for?'",
                "WAIT for their explanation",
                "Do NOT add extra commentary",
                "IMMEDIATELY call collect_funds_purpose function after they explain the purpose",
                "Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_funds_purpose function called successfully") \
            .set_functions(["collect_funds_purpose", "handle_dnc_request"]) \
            .set_valid_steps(["employment"])

        # ============================================
        # STEP 5: EMPLOYMENT STATUS (Question 3)
        # ============================================
        intake_context.add_step("employment") \
            .add_section("Current Task", "Ask Question 3 from the script") \
            .add_bullets("Process", [
                "Ask EXACTLY: 'And are you currently earning a paycheck, self-employed, or on a fixed income?'",
                "WAIT for their employment type",
                "Do NOT add extra commentary",
                "IMMEDIATELY call collect_employment function after they tell their employment status",
                "Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_employment function called successfully") \
            .set_functions(["collect_employment", "handle_dnc_request"]) \
            .set_valid_steps(["credit_card_debt"])

        # ============================================
        # STEP 6: CREDIT CARD DEBT (Question 4)
        # ============================================
        intake_context.add_step("credit_card_debt") \
            .add_section("Current Task", "Ask Question 4 from the script") \
            .add_bullets("Process", [
                "Ask EXACTLY: 'About how much total unsecured credit card debt are you carrying right now?'",
                "WAIT for the amount (use 0 if they say none)",
                "Do NOT add extra commentary",
                "IMMEDIATELY call collect_credit_card_debt function after they provide the amount",
                "Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_credit_card_debt function called successfully") \
            .set_functions(["collect_credit_card_debt", "handle_dnc_request"]) \
            .set_valid_steps(["personal_loan_debt"])

        # ============================================
        # STEP 7: PERSONAL LOAN DEBT (Question 5)
        # ============================================
        intake_context.add_step("personal_loan_debt") \
            .add_section("Current Task", "Ask Question 5 from the script") \
            .add_bullets("Process", [
                "Ask EXACTLY: 'And do you have any balances on unsecured personal loans?'",
                "WAIT for the amount (use 0 if they say no)",
                "Do NOT add extra commentary",
                "IMMEDIATELY call collect_personal_loan_debt function after they provide the amount",
                "Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_personal_loan_debt function called successfully") \
            .set_functions(["collect_personal_loan_debt", "handle_dnc_request"]) \
            .set_valid_steps(["other_debt"])

        # ============================================
        # STEP 8: OTHER DEBT (Question 6)
        # ============================================
        intake_context.add_step("other_debt") \
            .add_section("Current Task", "Ask Question 6 from the script") \
            .add_bullets("Process", [
                "Ask EXACTLY: 'How about medical bills or any other balances you're aware of?'",
                "WAIT for the amount (use 0 if they say none)",
                "Do NOT add extra commentary",
                "IMMEDIATELY call collect_other_debt function after they provide the amount",
                "Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_other_debt function called successfully") \
            .set_functions(["collect_other_debt", "handle_dnc_request"]) \
            .set_valid_steps(["debt_summary"])

        # ============================================
        # STEP 9: DEBT SUMMARY
        # ============================================
        intake_context.add_step("debt_summary") \
            .add_section("Current Task", "Summarize all debt collected") \
            .add_bullets("Process", [
                "Say EXACTLY: 'So just to summarize, you have $[X] in credit card debt, $[Y] in personal loans, and $[Z] in other debt.'",
                "Use the ACTUAL amounts collected from previous steps",
                "Do NOT wait for response - move immediately to monthly_income"
            ]) \
            .set_step_criteria("Debt summary delivered") \
            .set_functions(["handle_dnc_request"]) \
            .set_valid_steps(["monthly_income"])

        # ============================================
        # STEP 10: MONTHLY INCOME (Question 7)
        # ============================================
        intake_context.add_step("monthly_income") \
            .add_section("Current Task", "Ask Question 7 from the script") \
            .add_bullets("Process", [
                "Ask EXACTLY: 'Now, can you please provide your monthly income amount?'",
                "WAIT for the dollar amount",
                "Do NOT add extra commentary",
                "IMMEDIATELY call collect_monthly_income function after they tell their monthly income",
                "Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_monthly_income function called successfully") \
            .set_functions(["collect_monthly_income", "handle_dnc_request"]) \
            .set_valid_steps(["income_confirmation"])

        # ============================================
        # STEP 10: INCOME CONFIRMATION
        # ============================================
        intake_context.add_step("income_confirmation") \
            .add_section("Current Task", "Confirm the income amount is monthly") \
            .add_bullets("Process", [
                "Confirm EXACTLY: 'And that's your monthly take-home after taxes, correct?'",
                "WAIT for their confirmation",
                "If they confirm, proceed to transfer",
                "If they clarify (e.g., 'No, that's before taxes'), ask for the after-tax amount"
            ]) \
            .set_step_criteria("Income confirmed as monthly take-home") \
            .set_functions(["handle_dnc_request"]) \
            .set_valid_steps(["transfer"])  # Changed from ["ssn_last_four"]

        # ============================================
        # STEP 11: TRANSFER
        # ============================================
        intake_context.add_step("transfer") \
            .add_section("Current Task", "Deliver transfer message from script") \
            .add_bullets("Process", [
                "Say EXACTLY: 'Thank you, I appreciate your patience. Now that I have all the necessary information, I will connect you with a senior underwriter who will go over your loan options in detail. Please hold for a moment while I transfer you.'",
                "Call transfer_call function to initiate the transfer",
                "Do NOT wait for response - call will be transferred automatically"
            ]) \
            .set_step_criteria("Transfer message delivered") \
            .set_functions(['transfer_call']) \
            .set_valid_steps([])  # End of flow

    # ============================================
    # LIFECYCLE HOOKS
    # ============================================

    def on_swml_request(self, request_data=None, callback_path=None, request=None):
        """
        Called when a call first comes in (SignalWire's actual lifecycle hook).
        """
        try:
            if request_data and 'call' in request_data:
                call_info = request_data['call']
                call_id = call_info.get('call_id', 'unknown')
                caller_number = call_info.get('from_number', call_info.get('from', ''))

                logger.info(f"📞 Call started: {call_id} from {caller_number}")

                # Initial global_data will be set up via _get_intake_state() in first SWAIG call
                logger.info(f"✅ Call session started - state will be managed in global_data")

        except Exception as e:
            logger.error(f"❌ Error in on_swml_request: {str(e)}")

        return super().on_swml_request(request_data, callback_path, request)


    # ============================================
    # SWAIG FUNCTIONS (Data Collection Tools)
    # ============================================

    @AgentBase.tool(
        name="handle_dnc_request",
        description="Handle a Do Not Call (DNC) request when the caller asks to be removed from the calling list. Call this immediately if the caller says things like 'remove me from the list', 'stop calling', 'do not call', etc.",
        parameters={
            "type": "object",
            "properties": {
                "phrase_detected": {
                    "type": "string",
                    "description": "The phrase the caller used to request removal (e.g., 'remove me from the list')"
                }
            },
            "required": ["phrase_detected"]
        }
    )
    def handle_dnc_request(self, args, raw_data):
        """Handle DNC request - flag caller and end call gracefully"""
        try:
            phrase = args.get('phrase_detected', 'DNC request')
            intake_state, global_data = self._get_intake_state(raw_data)
            
            # Flag as DNC
            intake_state['is_dnc'] = True
            intake_state['dnc_phrase'] = phrase
            
            logger.warning(f"🚫 DNC Request detected: '{phrase}' from {intake_state.get('caller_number')}")
            
            # Save call record to database with DNC flag (async in background)
            call_id = intake_state.get("call_id")
            if call_id:
                asyncio.create_task(
                    call_record_service.save_call_record(
                        call_sid=call_id,
                        intake_state=intake_state,
                        client_id=intake_state.get("client_id"),
                        agent_id=intake_state.get("agent_id")
                    )
                )
            
            result = SwaigFunctionResult(
                response="I understand. I've noted your request and you've been added to our do not call list. "
                         "You will not receive any further calls from us. Have a good day."
            )
            
            # Save state before ending
            self._save_intake_state(result, intake_state, global_data)
            
            # End the call gracefully
            return result.hangup()
            
        except Exception as e:
            logger.error(f"❌ Error handling DNC request: {str(e)}")
            return SwaigFunctionResult(
                response="I've noted your request. You will not receive any further calls. Goodbye."
            ).hangup()

    @AgentBase.tool(
        name="collect_caller_name",
        description="Store the caller's name after they tell you their name in the greeting step. Call this immediately when the user provides their name.",
        parameters={
            "type": "object",
            "properties": {
                "caller_name": {
                    "type": "string",
                    "description": "The caller's first name or full name (e.g., 'John', 'Mary Smith')"
                }
            },
            "required": ['caller_name']
        }
    )
    def collect_caller_name(self, args, raw_data):
        try:
            caller_name = args.get('caller_name')
            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state['lead_name'] = str(caller_name)
            intake_state['answered'].append('caller_name')

            logger.info(f'👤 Collected Caller Name: {caller_name}')

            result = SwaigFunctionResult(
                response=f"Collected caller name: {caller_name}."
            )
            return self._save_intake_state(result, intake_state, global_data)
            
        except Exception as e:
            logger.error(f"❌ Error in collect_caller_name: {str(e)}")
            return SwaigFunctionResult(response="Could not collect name.")

    @AgentBase.tool(
        name="collect_loan_amount",
        description="Collect the loan amount in the caller data.",
        parameters={
            "type": "object",
            "properties": {
                "amount": {
                    "type": ["number", "string"],
                    "description": "The loan amount in dollars (e.g., 15000, '15000', or '$15,000')"
                }
            },
            "required": ["amount"]
        }
    )
    def collect_loan_amount(self, args, raw_data):
        try:
            amount = args.get("amount")
            # Clean the amount if it's a string
            if isinstance(amount, str):
                amount = float(amount.replace('$', '').replace(',', ''))
            
            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["loan_amount"] = float(amount)
            intake_state["answered"].append("loan_amount")

            logger.info(f"💰 Collected loan amount: ${amount:,.2f}")

            result = SwaigFunctionResult(
                response=f"Got it, ${amount:,.0f}."
            )

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            logger.error(f"❌ Error in collect_loan_amount: {str(e)}")
            return SwaigFunctionResult(response="Error collecting amount")

    @AgentBase.tool(
        name="collect_funds_purpose",
        description="Collect the purpose of the loan amount in caller data.",
        parameters={
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "What the user will use the funds for (e.g., 'debt consolidation', 'home repairs')"
                }
            },
            "required": ["purpose"]
        }
    )
    def collect_funds_purpose(self, args, raw_data):
        """Collect and store the purpose of the loan"""
        try:
            purpose = args.get("purpose")

            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["funds_purpose"] = purpose
            intake_state["answered"].append("funds_purpose")

            logger.info(f"🎯 Collected purpose: {purpose}")

            result = SwaigFunctionResult(
                response=f"Understood, for {purpose}."
            )

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            logger.error(f"❌ Error in collect_funds_purpose: {str(e)}")
            return SwaigFunctionResult(response="Error collecting purpose")

    @AgentBase.tool(
        name="collect_employment",
        description="Collect the employment status of the caller in caller data.",
        parameters={
            "type": "object",
            "properties": {
                "employment_status": {
                    "type": "string",
                    "description": "Employment type: 'employed', 'self_employed', or 'fixed_income'"
                }
            },
            "required": ["employment_status"]
        }
    )
    def collect_employment(self, args, raw_data):
        """Collect and store employment status"""
        try:
            employment_status = args.get("employment_status")

            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["employment_status"] = employment_status
            intake_state["answered"].append("employment")

            logger.info(f"💼 Collected employment: {employment_status}")

            result = SwaigFunctionResult(
                response="Thank you."
            )

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            logger.error(f"❌ Error in collect_employment: {str(e)}")
            return SwaigFunctionResult(response="Error collecting employment")

    @AgentBase.tool(
        name="collect_credit_card_debt",
        description="Collect the credit card debt of the caller in caller data.",
        parameters={
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Credit card debt in dollars (use 0 if they say none, no, or zero)"
                }
            },
            "required": ["amount"]
        }
    )
    def collect_credit_card_debt(self, args, raw_data):
        """Collect credit card debt"""
        try:
            amount = args.get("amount", 0)

            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["credit_card_debt"] = float(amount)
            intake_state["answered"].append("credit_card_debt")

            logger.info(f"💳 Collected CC debt: ${amount:,.2f}")

            result = SwaigFunctionResult(
                response=f"Okay, ${amount:,.0f} in credit card debt."
            )

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            logger.error(f"❌ Error in collect_credit_card_debt: {str(e)}")
            return SwaigFunctionResult(response="Error collecting debt")

    @AgentBase.tool(
        name="collect_personal_loan_debt",
        description="Collect personal loan debt of the caller in caller data.",
        parameters={
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Personal loan debt in dollars (use 0 if they say none, no, or zero)"
                }
            },
            "required": ["amount"]
        }
    )
    def collect_personal_loan_debt(self, args, raw_data):
        """Collect personal loan debt"""
        try:
            amount = args.get("amount", 0)

            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["personal_loan_debt"] = float(amount)
            intake_state["answered"].append("personal_loan_debt")

            logger.info(f"🏦 Collected personal loan debt: ${amount:,.2f}")

            result = SwaigFunctionResult(response=f"Got it, ${amount:,.0f} in personal loans.")

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            logger.error(f"❌ Error in collect_personal_loan_debt: {str(e)}")
            return SwaigFunctionResult(response="Error collecting debt")

    @AgentBase.tool(
        name="collect_other_debt",
        description="Collect the other debt of the caller in caller data.",
        parameters={
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Medical bills and other debt in dollars (use 0 if they say none, no, or zero)"
                }
            },
            "required": ["amount"]
        }
    )
    def collect_other_debt(self, args, raw_data):
        """Collect other debt (medical, etc.)"""
        try:
            amount = args.get("amount", 0)

            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["other_debt"] = float(amount)
            intake_state["answered"].append("other_debt")

            # Calculate total debt and determine transfer tier
            total_debt = self._calculate_total_debt(intake_state)
            intake_state["total_debt"] = total_debt
            
            # Determine transfer tier based on 3-tier routing
            transfer_info = call_router.get_transfer_info(total_debt)
            intake_state["transfer_tier"] = transfer_info["tier"].value
            intake_state["transfer_did"] = transfer_info["did"]

            logger.info(f"🏥 Collected other debt: ${amount:,.2f}")
            logger.info(f"📊 Total unsecured debt: ${total_debt:,.2f}")
            logger.info(f"🎯 Transfer tier: {transfer_info['tier_name']} -> {transfer_info['did']}")

            result = SwaigFunctionResult(response="Thank you.")

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            logger.error(f"❌ Error in collect_other_debt: {str(e)}")
            return SwaigFunctionResult(response="Error collecting debt")

    @AgentBase.tool(
        name="collect_monthly_income",
        description="Collect the monthly income of the caller in caller data.",
        parameters={
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Monthly income in dollars (e.g., 5000 for $5,000/month)"
                }
            },
            "required": ["amount"]
        }
    )
    def collect_monthly_income(self, args, raw_data):
        """Collect monthly income"""
        try:
            amount = args.get("amount")

            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["monthly_income"] = float(amount)
            intake_state["answered"].append("monthly_income")

            logger.info(f"💵 Collected monthly income: ${amount:,.2f}")

            result = SwaigFunctionResult(response="Thank you.")

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            logger.error(f"❌ Error in collect_monthly_income: {str(e)}")
            return SwaigFunctionResult(response="Error collecting income")

    @AgentBase.tool(
        name="collect_ssn_last_four",
        description="Collect the social security number (SSN) last four digits of the caller in caller data.",
        parameters={
            "type": "object",
            "properties": {
                "digits": {
                    "type": "string",
                    "description": "Last 4 digits of SSN as a string (e.g., '1234'). Must be exactly 4 digits."
                }
            },
            "required": ["digits"]
        }
    )
    def collect_ssn_last_four(self, args, raw_data):
        """Collect SSN last 4 digits"""
        try:
            digits = str(args.get("digits"))

            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["ssn_last_four"] = digits
            intake_state["answered"].append("ssn_last_four")

            logger.info(f"🔒 Collected SSN last 4: ***{digits}")
            self._print_collected_data(intake_state)

            result = SwaigFunctionResult(
                response="Collected social security number."
            )
            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            logger.error(f"❌ Error in collect_ssn_last_four: {str(e)}")
            return SwaigFunctionResult(response="Error collecting SSN")

    @AgentBase.tool(
        name='transfer_call',
        description='Initiate call transfer to the appropriate queue based on total debt tier.',
    )
    def transfer_call(self, args, raw_data):
        """
        Transfer the call to the appropriate queue based on total debt.
        
        Transfer Tiers:
        - HIGH: Total debt >= $35,000
        - MID: Total debt >= $10,000 and < $35,000
        - LOW: Total debt < $10,000
        """
        try:
            intake_state, global_data = self._get_intake_state(raw_data)
            
            # Get transfer info from intake state (calculated earlier) or recalculate
            total_debt = intake_state.get("total_debt", 0)
            transfer_tier = intake_state.get("transfer_tier", "low")
            transfer_did = intake_state.get("transfer_did", "")
            
            if not transfer_did:
                # Recalculate if not set
                transfer_info = call_router.get_transfer_info(total_debt)
                transfer_tier = transfer_info["tier"].value
                transfer_did = transfer_info["did"]
            
            # Mark transfer as initiated
            intake_state["transfer_initiated"] = True
            intake_state["transfer_tier"] = transfer_tier
            intake_state["transfer_did"] = transfer_did
            
            logger.info(f"📞 Initiating transfer for ${total_debt:,.2f} debt")
            logger.info(f"   Tier: {transfer_tier.upper()}")
            logger.info(f"   DID: {transfer_did}")
            
            # Print final summary
            self._print_collected_data(intake_state)
            
            # Save call record to database (async in background)
            call_id = intake_state.get("call_id")
            if call_id:
                asyncio.create_task(
                    call_record_service.save_call_record(
                        call_sid=call_id,
                        intake_state=intake_state,
                        client_id=intake_state.get("client_id"),
                        agent_id=intake_state.get("agent_id")
                    )
                )
            
            # Save final state
            result = SwaigFunctionResult(
                response="Thank you! I appreciate your patience. Now that I have all the necessary information, "
                         "I will connect you with a senior underwriter who will go over your loan options in detail. "
                         "Please hold for a moment while I transfer you."
            )
            self._save_intake_state(result, intake_state, global_data)
            
            # For now, end the call gracefully (actual SIP transfer implementation pending)
            # In production, this would initiate the actual transfer via SWML
            return result.hangup()
            
        except Exception as e:
            logger.error(f"❌ Error in transfer_call: {str(e)}")
            return SwaigFunctionResult(
                response="I apologize, but I'm having trouble completing the transfer. "
                         "A representative will call you back shortly."
            ).hangup()
    
    
    # ============================================
    # HELPER METHODS
    # ============================================

    def _print_collected_data(self, intake_state: dict):
        """Print all collected data to terminal for debugging/review."""
        total_debt = intake_state.get('total_debt', 0)
        transfer_tier = intake_state.get('transfer_tier', 'unknown')
        
        logger.info("\n" + "="*60)
        logger.info("📋 CALL INTAKE DATA SUMMARY")
        logger.info("="*60)
        logger.info(f"Call ID: {intake_state.get('call_id')}")
        logger.info(f"Phone Number: {intake_state.get('caller_number')}")
        logger.info(f"Lead Name: {intake_state.get('lead_name') or 'Not provided'}")
        logger.info("-"*60)

        logger.info("LOAN REQUEST:")
        if intake_state.get('loan_amount'):
            logger.info(f"  Amount Requested: ${intake_state.get('loan_amount'):,.2f}")
        else:
            logger.info("  Amount Requested: Not collected")
        logger.info(f"  Purpose: {intake_state.get('funds_purpose') or 'Not collected'}")
        logger.info(f"  Employment: {intake_state.get('employment_status') or 'Not collected'}")

        logger.info("\nDEBT INFORMATION:")
        logger.info(f"  Credit Card Debt: ${intake_state.get('credit_card_debt', 0):,.2f}")
        logger.info(f"  Personal Loan Debt: ${intake_state.get('personal_loan_debt', 0):,.2f}")
        logger.info(f"  Other Debt: ${intake_state.get('other_debt', 0):,.2f}")
        logger.info(f"  TOTAL UNSECURED DEBT: ${total_debt:,.2f}")

        logger.info("\nTRANSFER ROUTING:")
        logger.info(f"  Tier: {transfer_tier.upper()}")
        logger.info(f"  DID: {intake_state.get('transfer_did') or 'Not set'}")

        logger.info("\nINCOME:")
        if intake_state.get('monthly_income'):
            logger.info(f"  Monthly Income: ${intake_state.get('monthly_income'):,.2f}")
        else:
            logger.info("  Monthly Income: Not collected")

        logger.info("\nVERIFICATION:")
        if intake_state.get('ssn_last_four'):
            logger.info(f"  SSN Last 4: ***{intake_state.get('ssn_last_four')}")
        else:
            logger.info("  SSN Last 4: Not collected")

        logger.info("\nDNC STATUS:")
        logger.info(f"  Is DNC: {intake_state.get('is_dnc', False)}")
        if intake_state.get('dnc_phrase'):
            logger.info(f"  DNC Phrase: {intake_state.get('dnc_phrase')}")

        logger.info("\nPROGRESS:")
        logger.info(f"  Questions Answered: {len(intake_state.get('answered', []))}/9")

        logger.info("="*60 + "\n")
