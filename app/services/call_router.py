from app.config import settings
from app.models.call_data import IntakeData
from app.models.call_records import TransferTier
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CallRouter:
    """
    Handles 3-tier call routing logic based on total unsecured debt.
    
    Tiers:
    - HIGH: Total unsecured debt >= $35,000
    - MID: Total unsecured debt >= $10,000 and < $35,000
    - LOW: Total unsecured debt < $10,000
    """
    
    # Default thresholds (can be overridden per-client via config)
    HIGH_THRESHOLD = 35000  # >= $35k
    MID_THRESHOLD = 10000   # >= $10k and < $35k
    
    def determine_tier(self, total_debt: float, routing_config: Optional[Dict] = None) -> TransferTier:
        """
        Determine which tier a call should be routed to based on total unsecured debt.
        
        Args:
            total_debt: Total unsecured debt amount in dollars
            routing_config: Optional per-client/agent routing configuration
            
        Returns:
            TransferTier enum value
        """
        # Use custom thresholds if provided, otherwise use defaults
        high_threshold = self.HIGH_THRESHOLD
        mid_threshold = self.MID_THRESHOLD
        
        if routing_config:
            high_threshold = routing_config.get("high_threshold", self.HIGH_THRESHOLD)
            mid_threshold = routing_config.get("mid_threshold", self.MID_THRESHOLD)
        
        if total_debt >= high_threshold:
            logger.info(f"Routing to HIGH tier: ${total_debt:,.2f} >= ${high_threshold:,.2f}")
            return TransferTier.HIGH
        elif total_debt >= mid_threshold:
            logger.info(f"Routing to MID tier: ${mid_threshold:,.2f} <= ${total_debt:,.2f} < ${high_threshold:,.2f}")
            return TransferTier.MID
        else:
            logger.info(f"Routing to LOW tier: ${total_debt:,.2f} < ${mid_threshold:,.2f}")
            return TransferTier.LOW
    
    def determine_queue(self, intake_data: IntakeData, routing_config: Optional[Dict] = None) -> str:
        """
        Determine which queue DID to route the call to based on intake data.
        
        Args:
            intake_data: Collected intake data with debt information
            routing_config: Optional per-client routing configuration with DIDs
            
        Returns:
            Queue DID phone number
        """
        total_debt = intake_data.total_unsecured_debt
        tier = self.determine_tier(total_debt, routing_config)
        
        return self.get_did_for_tier(tier, routing_config)
    
    def get_did_for_tier(self, tier: TransferTier, routing_config: Optional[Dict] = None) -> str:
        """
        Get the DID phone number for a specific tier.
        
        Args:
            tier: The transfer tier
            routing_config: Optional per-client routing configuration
            
        Returns:
            DID phone number for the tier
        """
        # Check per-client config first
        if routing_config:
            if tier == TransferTier.HIGH and routing_config.get("high_did"):
                return routing_config["high_did"]
            elif tier == TransferTier.MID and routing_config.get("mid_did"):
                return routing_config["mid_did"]
            elif tier == TransferTier.LOW and routing_config.get("low_did"):
                return routing_config["low_did"]
        
        # Fall back to environment variables
        if tier == TransferTier.HIGH:
            return settings.QUEUE_HIGH_DID or settings.QUEUE_A_DID or ""
        elif tier == TransferTier.MID:
            return settings.QUEUE_MID_DID or settings.QUEUE_B_DID or ""
        elif tier == TransferTier.LOW:
            return settings.QUEUE_LOW_DID or settings.QUEUE_B_DID or ""
        else:
            return ""
    
    def generate_transfer_params(self, queue_did: str, tier: Optional[TransferTier] = None) -> dict:
        """
        Generate SIP transfer parameters for 3CX.
        
        Args:
            queue_did: The destination DID
            tier: Optional tier for logging/metadata
            
        Returns:
            Transfer parameters dictionary
        """
        params = {
            "action": "transfer",
            "destination": queue_did,
            "trunk": settings.TWILIO_SIP_TRUNK or "",
            "method": "SIP"
        }
        
        if tier:
            params["tier"] = tier.value
        
        return params
    
    def get_transfer_info(self, total_debt: float, routing_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get complete transfer information including tier, DID, and params.
        
        Args:
            total_debt: Total unsecured debt
            routing_config: Optional per-client routing configuration
            
        Returns:
            Dictionary with tier, did, and transfer_params
        """
        tier = self.determine_tier(total_debt, routing_config)
        did = self.get_did_for_tier(tier, routing_config)
        params = self.generate_transfer_params(did, tier)
        
        return {
            "tier": tier,
            "tier_name": tier.value,
            "did": did,
            "transfer_params": params,
            "total_debt": total_debt,
            "threshold_high": routing_config.get("high_threshold", self.HIGH_THRESHOLD) if routing_config else self.HIGH_THRESHOLD,
            "threshold_mid": routing_config.get("mid_threshold", self.MID_THRESHOLD) if routing_config else self.MID_THRESHOLD
        }


# Singleton instance  
call_router = CallRouter()
