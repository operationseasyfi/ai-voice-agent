"""
Conversation flow configuration for loan intake
"""

class IntakeConversationConfig:
    """Configuration for the loan intake conversation flow"""
    
    @staticmethod
    def get_intake_script():
        """Get the structured intake script"""
        return {
            "intro": "This is our secured automated intake system. It's built to make our process quick, private, and fully personalized. I'll ask a few short questions to confirm eligibility and then connect you to a senior underwriting specialist to review your actual loan options.",
            "questions": {
                "loan_amount": "What is the exact amount you are looking to borrow today?",
                "funds_purpose": "Just so I know how to help best, what are you planning to use the funds for?", 
                "employment": "And are you currently earning a paycheck, self-employed, or on a fixed income?",
                "credit_card_debt": "About how much total unsecured credit card debt are you carrying right now?",
                "personal_loan_debt": "And do you have any balances on unsecured personal loans?",
                "other_debt": "How about medical bills or any other balances you're aware of?",
                "debt_summary": "So just to summarize, you have $X in credit card debt, $Y in personal loans, and $Z in other debt.",
                "monthly_income": "Now, can you please provide your monthly income amount?",
                "ssn_last_four": "Now I will need your last 4 digits of your Social Security number to securely match your file and verify your identity. This will not impact your credit and does not count as an inquiry because it's a soft credit pull. Can you provide those last 4 digits?"
            },
            "transfer": "Thank you, I appreciate your patience. Now that I have all the necessary information, I will connect you with a senior underwriter who will go over your loan options in detail. Please hold for a moment while I transfer you.",
            "greeting_placeholder": "Personalizing greeting based on CRM lookup..."
        }
    
    @staticmethod
    def get_conversation_steps():
        """Get the conversation step definitions"""
        return [
            {
                "name": "greeting",
                "text": "greeting_placeholder",  # Will be set dynamically
                "next_steps": ["introduction"]
            },
            {
                "name": "introduction", 
                "text": "intro",  # References script key
                "next_steps": ["loan_amount"]
            },
            {
                "name": "loan_amount",
                "text": "questions.loan_amount",  # References script path
                "criteria": "Amount collected and confirmed",
                "next_steps": ["funds_purpose"],
                "swaig_function": "collect_loan_amount"
            },
            {
                "name": "funds_purpose",
                "text": "questions.funds_purpose",
                "criteria": "Purpose collected", 
                "next_steps": ["employment"]
            },
            {
                "name": "employment",
                "text": "questions.employment",
                "criteria": "Employment status collected",
                "next_steps": ["credit_card_debt"]
            },
            {
                "name": "credit_card_debt",
                "text": "questions.credit_card_debt",
                "criteria": "Credit card debt amount collected",
                "next_steps": ["personal_loan_debt"]
            },
            {
                "name": "personal_loan_debt", 
                "text": "questions.personal_loan_debt",
                "criteria": "Personal loan debt collected",
                "next_steps": ["other_debt"]
            },
            {
                "name": "other_debt",
                "text": "questions.other_debt", 
                "criteria": "Other debt collected",
                "next_steps": ["debt_summary"]
            },
            {
                "name": "debt_summary",
                "text": "questions.debt_summary",
                "criteria": "Debt summary confirmed",
                "next_steps": ["monthly_income"],
                "swaig_function": "collect_debt_amounts"
            },
            {
                "name": "monthly_income",
                "text": "questions.monthly_income",
                "criteria": "Monthly income collected and confirmed", 
                "next_steps": ["ssn_last_four"]
            },
            {
                "name": "ssn_last_four",
                "text": "questions.ssn_last_four",
                "criteria": "SSN last 4 digits collected",
                "next_steps": ["transfer"],
                "swaig_function": "finalize_intake"
            },
            {
                "name": "transfer",
                "text": "transfer",  # References script key
                "criteria": "Transfer initiated",
                "next_steps": []
            }
        ]
    
    @staticmethod
    def get_swaig_function_definitions():
        """Get SWAIG function parameter definitions"""
        return {
            "collect_loan_amount": {
                "name": "collect_loan_amount",
                "description": "Collect and validate the loan amount from user response",
                "parameters": {
                    "user_response": {
                        "type": "string",
                        "description": "The user's response containing the loan amount"
                    },
                    "call_id": {
                        "type": "string", 
                        "description": "The unique call identifier"
                    }
                }
            },
            "collect_debt_amounts": {
                "name": "collect_debt_amounts",
                "description": "Collect credit card, personal loan, and other debt amounts",
                "parameters": {
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
            },
            "finalize_intake": {
                "name": "finalize_intake",
                "description": "Collect final information and prepare for transfer",
                "parameters": {
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
            }
        }