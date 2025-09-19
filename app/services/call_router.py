from app.config import settings
from app.models.call_data import IntakeData
import logging

logger = logging.getLogger(__name__)

class CallRouter:
    """Handles call routing logic based on intake data"""
    
    DEBT_THRESHOLD = 35000  # $35k threshold for queue routing
    
    def determine_queue(self, intake_data: IntakeData) -> str:
        """
        Determine which 3CX queue to route the call to based on total unsecured debt
        
        Rules:
        - Total unsecured debt >= $35k → Queue A 
        - Total unsecured debt < $35k → Queue B
        """
        total_debt = intake_data.total_unsecured_debt
        
        if total_debt >= self.DEBT_THRESHOLD:
            queue_did = settings.QUEUE_A_DID
            logger.info(f"Routing to Queue A (high debt): ${total_debt:,.2f}")
        else:
            queue_did = settings.QUEUE_B_DID  
            logger.info(f"Routing to Queue B (low debt): ${total_debt:,.2f}")
            
        return queue_did
    
    def generate_transfer_params(self, queue_did: str) -> dict:
        """Generate SIP transfer parameters for 3CX"""
        return {
            "action": "transfer",
            "destination": queue_did,
            "trunk": settings.TWILIO_SIP_TRUNK,
            "method": "SIP"
        }

# Singleton instance  
call_router = CallRouter()