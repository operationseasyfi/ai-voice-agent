from signalwire_agents import AgentBase, SwaigFunctionResult
from app.services.call_router import call_router
from app.config import settings
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LoanIntakeAgent(AgentBase):
    """
    AI Voice Agent for loan intake with structured conversation flow.
    """

    def __init__(self, **kwargs):
        # Initialize the base agent with a name
        super().__init__(
            name="Jessica - Easy Finance Specialist",
            route="/webhook",
            **kwargs
        )

        # Configure voice and language (required for voice agents)
        self.add_language(
            name="English (US)",
            code="en-US",
            voice="elevenlabs.rachel:eleven_flash_v2_5"
        )

        # Set AI model parameters
        # self.set_params({
        #     "ai_model": "gpt-4o-mini",
        #     "temperature": 0.5,
        #     "max_tokens": 200,
        # })

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

            # Progress tracking
            "answered": [],
        }
        lead_data = global_data.get('caller_data', default_state)
        for key, val in lead_data.items():
            if val is None and key in lead_data['answered']:
                lead_data['answered'].remove(key)

        return lead_data , global_data

    def _save_intake_state(self, result: SwaigFunctionResult, lead_data : dict, global_data):
        """Save intake state to global_data"""
        # Remove duplicates while preserving order
        if 'answered' in lead_data and isinstance(lead_data['answered'], list):
            lead_data['answered'] = list(dict.fromkeys(lead_data['answered']))
        
        print(" Lead Data: ", lead_data)
        global_data['caller_data'] = lead_data
        result.update_global_data(global_data)
        return result

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
                - Sequence: greeting → introduction → loan_amount → funds_purpose → employment → credit_card_debt → personal_loan_debt → other_debt → debt_summary → monthly_income → income_confirmation → ssn_last_four
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
                "Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_caller_name function called successfully") \
            .set_functions(["collect_caller_name"]) \
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
            .set_functions(["collect_loan_amount"]) \
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
            .set_functions(["collect_funds_purpose"]) \
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
            .set_functions(["collect_employment"]) \
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
            .set_functions(["collect_credit_card_debt"]) \
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
            .set_functions(["collect_personal_loan_debt"]) \
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
            .set_functions(["collect_other_debt"]) \
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
            .set_functions(["collect_monthly_income"]) \
            .set_valid_steps(["income_confirmation"])

        # ============================================
        # STEP 11: INCOME CONFIRMATION (Question 8)
        # ============================================
        intake_context.add_step("income_confirmation") \
            .add_section("Current Task", "Confirm monthly income") \
            .add_bullets("Process", [
                "Say EXACTLY: 'Thank you for that information. Just to confirm, your total monthly income is $[amount].'",
                "Use the ACTUAL income amount collected",
                "WAIT for their confirmation (yes/okay/correct)",
            ]) \
            .set_step_criteria("Income confirmed by caller") \
            .set_valid_steps(["ssn_last_four"])

        # ============================================
        # STEP 12: SSN LAST 4 (Question 9)
        # ============================================
        intake_context.add_step("ssn_last_four") \
            .add_section("Current Task", "Ask Question 9 from the script") \
            .add_bullets("Process", [
                "Say EXACTLY: 'Now I will need your last 4 digits of your Social Security number to securely match your file and verify your identity. This will not impact your credit and does not count as an inquiry because it's a soft credit pull. Can you provide those last 4 digits?'",
                "WAIT for exactly 4 digits",
                "Do NOT add extra commentary",
                "IMMEDIATELY call collect_ssn_last_four function with the 4 digits they provided",
                "CRITICAL: Do NOT move to next step until function is called"
            ]) \
            .set_step_criteria("collect_ssn_last_four function called successfully") \
            .set_functions(["collect_ssn_last_four"]) \
            .set_valid_steps(["transfer"])

        # ============================================
        # STEP 13: TRANSFER
        # ============================================
        intake_context.add_step("transfer") \
            .add_section("Current Task", "Deliver transfer message from script") \
            .add_bullets("Process", [
                "Say EXACTLY: 'Thank you, I appreciate your patience. Now that I have all the necessary information, I will connect you with a senior underwriter who will go over your loan options in detail. Please hold for a moment while I transfer you.'",
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

                print(f"📞 Call ID: {call_id}")
                print(f"📞 From Number: {caller_number}")
                print(f"📞 Call started: {call_id} from {caller_number}")

                # TODO: When CRM is ready, lookup lead by phone and store in global_data
                # lead_info = crm_service.lookup_lead_by_phone(caller_number)
                # Initial global_data will be set up via _get_intake_state() in first SWAIG call

                print(f"✅ Call session started - state will be managed in global_data")
                print(f"✅ Call session started for {call_id}")

        except Exception as e:
            print(f"❌ Error in on_swml_request: {str(e)}")

        return super().on_swml_request(request_data, callback_path, request)


    # ============================================
    # SWAIG FUNCTIONS (Data Collection Tools)
    # ============================================

    @AgentBase.tool(
        name="collect_caller_name",
        description="Store the caller's name after they tell you their name in the greeting step. Call this immediately when the user provides their name.",
        parameters={
            "type":"object",
            "properties":{
                "caller_name":{
                    "type":"string",
                    "description":"The caller's first name or full name (e.g., 'John', 'Mary Smith')"
                }
            },
            "required":['caller_name']
        }
    )
    def collect_caller_name(self, args, raw_data):
        try:
            caller_name = args.get('caller_name')
            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state['lead_name'] = str(caller_name)
            intake_state['answered'].append('caller_name')

            print(f'👤 Collected Caller Name: {caller_name}')

            result = SwaigFunctionResult(
                response=f"Collected caller name: {caller_name}."
            )
            return self._save_intake_state(result, intake_state, global_data)
            
        except Exception as e:
            print(f"❌ Error in collect_caller_name: {str(e)}")
            return SwaigFunctionResult(response="Could not collect name.")

    @AgentBase.tool(
        name="collect_loan_amount",
        description="collect the loan amount in the caller data.",
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

            intake_state, global_data = self._get_intake_state(raw_data)

            intake_state["loan_amount"] = float(amount)
            intake_state["answered"].append("loan_amount")

            print(f"💰 Collected loan amount: ${amount:,.2f}")

            result = SwaigFunctionResult(
                response=f"Got it, ${amount:,.0f}."
            )

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            print(f"❌ Error in collect_loan_amount: {str(e)}")
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

            print(f"🎯 Collected purpose: {purpose}")

            result = SwaigFunctionResult(
                response=f"Understood, for {purpose}."
            )

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            print(f"❌ Error in collect_funds_purpose: {str(e)}")
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

            print(f"💼 Collected employment: {employment_status}")

            result = SwaigFunctionResult(
                response="Thank you."
            )

            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            print(f"❌ Error in collect_employment: {str(e)}")
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

            print(f"💳 Collected CC debt: ${amount:,.2f}")

            result = SwaigFunctionResult(
                response=f"Okay, ${amount:,.0f} in credit card debt."
            )

            # Save state to global_data
            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            print(f"❌ Error in collect_credit_card_debt: {str(e)}")
            return SwaigFunctionResult(response="Error collecting debt")

    @AgentBase.tool(
        name="collect_personal_loan_debt",
        description="collect personal loan debt of the caller in caller data.",
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

            # Get intake state from global_data
            intake_state, global_data = self._get_intake_state(raw_data)

            # Store in global_data
            intake_state["personal_loan_debt"] = float(amount)
            intake_state["answered"].append("personal_loan_debt")

            print(f"🏦 Collected personal loan debt: ${amount:,.2f}")

            result = SwaigFunctionResult(response=f"Got it, ${amount:,.0f} in personal loans.")

            # Save state to global_data
            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            print(f"❌ Error in collect_personal_loan_debt: {str(e)}")
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

            # Get intake state from global_data
            intake_state, global_data = self._get_intake_state(raw_data)

            # Store in global_data
            intake_state["other_debt"] = float(amount)
            intake_state["answered"].append("other_debt")

            # Calculate total debt
            total_debt = (
                (intake_state.get("credit_card_debt") or 0) +
                (intake_state.get("personal_loan_debt") or 0) +
                (intake_state.get("other_debt") or 0)
            )
            intake_state["total_debt"] = total_debt

            print(f"🏥 Collected other debt: ${amount:,.2f}")
            print(f"📊 Total unsecured debt: ${total_debt:,.2f}")

            result = SwaigFunctionResult(response=f"Thank you.")

            # Save state to global_data
            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            print(f"❌ Error in collect_other_debt: {str(e)}")
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

            # Get intake state from global_data
            intake_state, global_data = self._get_intake_state(raw_data)

            # Store in global_data
            intake_state["monthly_income"] = float(amount)
            intake_state["answered"].append("monthly_income")

            print(f"💵 Collected monthly income: ${amount:,.2f}")

            result = SwaigFunctionResult(response=f"Thank you.")

            # Save state to global_data
            return self._save_intake_state(result, intake_state, global_data)

        except Exception as e:
            print(f"❌ Error in collect_monthly_income: {str(e)}")
            return SwaigFunctionResult(response="Error collecting income")

    @AgentBase.tool(
        name="collect_ssn_last_four",
        description="collect the social security number (SSN) last four digits of the caller in caller data.",
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

            # Get intake state from global_data
            intake_state, global_data = self._get_intake_state(raw_data)

            # Store in global_data
            intake_state["ssn_last_four"] = digits
            intake_state["answered"].append("ssn_last_four")

            print(f"🔒 Collected SSN last 4: ***{digits}")
            self._print_collected_data(intake_state)

            result = SwaigFunctionResult(
                response="""Collected social security number."""
            )
            saved = self._save_intake_state(result, intake_state, global_data)
            return saved

        except Exception as e:
            print(f"❌ Error in collect_ssn_last_four: {str(e)}")
            return SwaigFunctionResult(response="Error collecting SSN").hangup()

    @AgentBase.tool(
        name='transfer_call',
        description='transfer the call.',
    )
    def transfer_call(self, args, raw_data):
        result = SwaigFunctionResult(
            "Thank you! I appreciate your patience. Now that I have all the necessary information, I will connect you with a senior underwriter who will go over your loan options in detail. Please hold for a moment while I transfer you."
        )
        return result.hangup()
    
    
    # ============================================
    # HELPER METHODS
    # ============================================

    def _print_collected_data(self, intake_state: dict):
        """
        Print all collected data to terminal for debugging/review.
        """
        print("\n" + "="*60)
        print("📋 CALL INTAKE DATA SUMMARY")
        print("="*60)
        print(f"Call ID: {intake_state.get('call_id')}")
        print(f"Phone Number: {intake_state.get('caller_number')}")
        print(f"Lead Name: {intake_state.get('lead_name') or 'Not in CRM'}")
        print("-"*60)

        print("LOAN REQUEST:")
        print(f"  Amount Requested: ${intake_state.get('loan_amount'):,.2f}" if intake_state.get('loan_amount') else "  Amount Requested: Not collected")
        print(f"  Purpose: {intake_state.get('funds_purpose')}" if intake_state.get('funds_purpose') else "  Purpose: Not collected")
        print(f"  Employment: {intake_state.get('employment_status')}" if intake_state.get('employment_status') else "  Employment: Not collected")

        print("\nDEBT INFORMATION:")
        print(f"  Credit Card Debt: ${intake_state.get('credit_card_debt'):,.2f}" if intake_state.get('credit_card_debt') is not None else "  Credit Card Debt: Not collected")
        print(f"  Personal Loan Debt: ${intake_state.get('personal_loan_debt'):,.2f}" if intake_state.get('personal_loan_debt') is not None else "  Personal Loan Debt: Not collected")
        print(f"  Other Debt: ${intake_state.get('other_debt'):,.2f}" if intake_state.get('other_debt') is not None else "  Other Debt: Not collected")
        print(f"  TOTAL UNSECURED DEBT: ${intake_state.get('total_debt', 0):,.2f}")

        print("\nINCOME:")
        print(f"  Monthly Income: ${intake_state.get('monthly_income'):,.2f}" if intake_state.get('monthly_income') else "  Monthly Income: Not collected")

        print("\nVERIFICATION:")
        print(f"  SSN Last 4: ***{intake_state.get('ssn_last_four')}" if intake_state.get('ssn_last_four') else "  SSN Last 4: Not collected")

        print("\nPROGRESS:")
        print(f"  Questions Answered: {len(intake_state.get('answered', []))}/8")
        print(f"  Current Step: {intake_state.get('current_step')}")

        print("="*60 + "\n")

    # ============================================
    # TRANSFER LOGIC
    # ============================================

    async def execute_transfer(self, queue_did: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute call transfer to 3CX queue.

        LEARNING: This is called after all data is collected.
        It transfers the call to the appropriate queue based on debt amount.
        """
        try:
            # Get transfer parameters from call router
            base_params = call_router.generate_transfer_params(queue_did)

            transfer_config = {
                **base_params,
                "announce": "Please hold while I connect you with a senior underwriter.",
                "bridge_type": "SIP",
                "call_data": call_data
            }

            print(f"📞 Executing transfer to {queue_did}")
            return transfer_config

        except Exception as e:
            print(f"❌ Error executing transfer: {str(e)}")
            raise
