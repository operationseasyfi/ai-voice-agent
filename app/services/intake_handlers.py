"""
Step handlers for loan intake conversation flow
"""
import logging
import re
from typing import Optional
from signalwire_agents import AgentBase, SwaigFunctionResult
from app.models.call_data import IntakeData
from app.services.crm_service import crm_service
from app.services.call_router import call_router

logger = logging.getLogger(__name__)


class IntakeStepHandlers:
    """Handles all intake conversation steps and data extraction"""
    
    def __init__(self, active_calls_store):
        """Initialize with reference to active calls storage"""
        self.active_calls = active_calls_store
    
    # Data extraction utilities
    def extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from user input"""
        text = text.lower().replace(",", "").replace("$", "")
        
        # Handle written numbers
        number_words = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
            "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
            "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
            "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000, "million": 1000000
        }
        
        # Look for direct numbers first
        amount_patterns = [
            r'(\d+(?:\.\d{2})?)\s*(?:thousand|k)',  # 50 thousand, 50k
            r'(\d+(?:\.\d{2})?)\s*(?:million|m)',   # 1 million, 1m
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)',        # 50,000 or 50000
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                amount = float(match.group(1).replace(",", ""))
                if "thousand" in text or "k" in text:
                    amount *= 1000
                elif "million" in text or "m" in text:
                    amount *= 1000000
                return amount
        
        # Handle written amounts like "fifty thousand"
        words = text.split()
        total = 0
        current = 0
        
        for word in words:
            if word in number_words:
                value = number_words[word]
                if value == 100:
                    # If current is 0, treat "hundred" as 100
                    if current == 0:
                        current = 100
                    else:
                        current *= 100  # "fifty hundred" = 50 * 100 = 5000
                elif value == 1000:
                    # Add accumulated value * 1000 to total
                    if current == 0:
                        current = 1  # Handle standalone "thousand"
                    total += current * 1000
                    current = 0
                elif value == 1000000:
                    # Add accumulated value * 1000000 to total
                    if current == 0:
                        current = 1  # Handle standalone "million"
                    total += current * 1000000
                    current = 0
                else:
                    current += value
        
        total += current
        return total if total >= 0 else None
    
    def extract_employment_status(self, text: str) -> Optional[str]:
        """Extract employment status from user input"""
        text = text.lower()
        
        if any(word in text for word in ["paycheck", "employed", "job", "work", "salary", "wage"]):
            return "employed"
        elif any(word in text for word in ["self employed", "self-employed", "business", "contractor", "freelance"]):
            return "self_employed"
        elif any(word in text for word in ["fixed income", "disability", "pension", "retirement", "social security"]):
            return "fixed_income"
        elif any(word in text for word in ["unemployed", "not working", "no job"]):
            return "unemployed"
        
        return None
    
    def extract_ssn_last_four(self, text: str) -> Optional[str]:
        """Extract last 4 digits of SSN"""
        # Look for 4 consecutive digits
        match = re.search(r'\b(\d{4})\b', text)
        if match:
            return match.group(1)
        return None

    # SWAIG Function Implementations
    def collect_loan_amount(self, args, raw_data):
        """SWAIG function to collect loan amount"""
        try:
            user_response = args.get("user_response", "")
            call_id = args.get("call_id", "")
            
            amount = self.extract_amount(user_response)
            if amount and call_id in self.active_calls:
                session = self.active_calls[call_id]
                if not session.intake_data:
                    session.intake_data = IntakeData()
                session.intake_data.loan_amount_requested = amount
                return SwaigFunctionResult(f"Loan amount ${amount:,.0f} collected successfully")
            return SwaigFunctionResult("Could not extract valid loan amount")
        except Exception as e:
            logger.error(f"Error in collect_loan_amount: {str(e)}")
            return SwaigFunctionResult(f"Error: {str(e)}")
    
    def collect_debt_amounts(self, args, raw_data):
        """SWAIG function to collect all debt amounts"""
        try:
            call_id = args.get("call_id", "")
            cc_debt = args.get("cc_debt", "")
            personal_debt = args.get("personal_debt", "")
            other_debt = args.get("other_debt", "")
            
            if call_id in self.active_calls:
                session = self.active_calls[call_id]
                if session.intake_data:
                    session.intake_data.credit_card_debt = self.extract_amount(cc_debt) or 0
                    session.intake_data.personal_loan_debt = self.extract_amount(personal_debt) or 0
                    session.intake_data.other_debt = self.extract_amount(other_debt) or 0
                    
                    # Determine queue based on total debt
                    queue_did = call_router.determine_queue(session.intake_data)
                    session.queue_assigned = queue_did
                    
                    total_debt = session.intake_data.total_unsecured_debt
                    return SwaigFunctionResult(f"Total debt ${total_debt:,.0f} collected. Routing to appropriate queue.")
            return SwaigFunctionResult("Call session not found")
        except Exception as e:
            logger.error(f"Error in collect_debt_amounts: {str(e)}")
            return SwaigFunctionResult(f"Error: {str(e)}")
    
    def finalize_intake(self, args, raw_data):
        """SWAIG function to finalize intake and prepare transfer"""
        try:
            call_id = args.get("call_id", "")
            monthly_income = args.get("monthly_income", "")
            ssn_last_four = args.get("ssn_last_four", "")
            
            if call_id in self.active_calls:
                session = self.active_calls[call_id]
                if session.intake_data:
                    session.intake_data.monthly_income = self.extract_amount(monthly_income)
                    session.intake_data.ssn_last_four = self.extract_ssn_last_four(ssn_last_four)
                    
                    return SwaigFunctionResult("Intake completed successfully. Ready for transfer to underwriter.")
            return SwaigFunctionResult("Call session not found")
        except Exception as e:
            logger.error(f"Error in finalize_intake: {str(e)}")
            return SwaigFunctionResult(f"Error: {str(e)}")