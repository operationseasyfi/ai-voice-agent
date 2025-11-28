from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.models.phone_number import PhoneNumber, PhoneNumberType
from app.auth.dependencies import get_current_active_user
from app.models.models import User
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


class PhoneNumberUpdate(BaseModel):
    friendly_name: Optional[str] = None
    description: Optional[str] = None
    number_type: Optional[str] = None


@router.get("/")
async def list_phone_numbers(
    number_type: Optional[str] = Query(None, description="Filter by type (ai_inbound, transfer_high, transfer_mid, transfer_low)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all phone numbers assigned to the current user's client.
    """
    try:
        filters = []
        
        # Client filtering
        if not current_user.is_admin() and current_user.client_id:
            filters.append(PhoneNumber.client_id == current_user.client_id)
        
        # Type filter
        if number_type:
            try:
                type_enum = PhoneNumberType(number_type)
                filters.append(PhoneNumber.number_type == type_enum)
            except ValueError:
                pass  # Invalid type, ignore filter
        
        # Execute query
        if filters:
            result = await db.execute(
                select(PhoneNumber)
                .where(and_(*filters))
                .order_by(PhoneNumber.number_type, PhoneNumber.number)
            )
        else:
            result = await db.execute(
                select(PhoneNumber).order_by(PhoneNumber.number_type, PhoneNumber.number)
            )
        
        numbers = result.scalars().all()
        
        # Group by type for easier frontend display
        grouped = {
            "ai_inbound": [],
            "transfer_high": [],
            "transfer_mid": [],
            "transfer_low": [],
            "outbound": []
        }
        
        all_numbers = []
        for n in numbers:
            try:
                # Safely access all attributes with null checks
                number_dict = {
                    "id": str(n.id) if n.id else None,
                    "number": n.number if n.number else "",
                    "formatted_number": n.formatted_number if n.number else "",
                    "friendly_name": n.friendly_name if n.friendly_name else None,
                    "description": n.description if n.description else None,
                    "number_type": n.number_type.value if n.number_type else "ai_inbound",
                    "type_label": _get_type_label(n.number_type) if n.number_type else "AI Inbound",
                    "is_active": n.is_active if n.is_active is not None else True,
                    "last_used_at": n.last_used_at.isoformat() if n.last_used_at else None,
                    "total_calls": n.total_calls if n.total_calls else "0"
                }
                all_numbers.append(number_dict)
                
                # Safely add to grouped dict
                num_type = n.number_type.value if n.number_type else "ai_inbound"
                if num_type in grouped:
                    grouped[num_type].append(number_dict)
                else:
                    # If type doesn't match expected values, add to ai_inbound as fallback
                    grouped["ai_inbound"].append(number_dict)
            except Exception as e:
                logger.error(f"Error processing phone number {n.id if hasattr(n, 'id') else 'unknown'}: {e}", exc_info=True)
                # Skip this number and continue with others
                continue
        
        return {
            "phone_numbers": all_numbers,
            "grouped": grouped,
            "counts": {
                type_name: len(nums) for type_name, nums in grouped.items()
            }
        }
    except Exception as e:
        logger.error(f"Error in list_phone_numbers: {e}", exc_info=True)
        # Re-raise as HTTPException so our global handler can add CORS headers
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve phone numbers: {str(e)}"
        )


@router.get("/{number_id}")
async def get_phone_number(
    number_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details for a specific phone number.
    """
    result = await db.execute(select(PhoneNumber).where(PhoneNumber.id == number_id))
    number = result.scalar_one_or_none()
    
    if not number:
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    # Check access
    if not current_user.is_admin() and number.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(number.id),
        "client_id": str(number.client_id),
        "agent_id": str(number.agent_id) if number.agent_id else None,
        "number": number.number,
        "formatted_number": number.formatted_number,
        "friendly_name": number.friendly_name,
        "description": number.description,
        "number_type": number.number_type.value,
        "type_label": _get_type_label(number.number_type),
        "signalwire_sid": number.signalwire_sid,
        "is_active": number.is_active,
        "last_used_at": number.last_used_at.isoformat() if number.last_used_at else None,
        "total_calls": number.total_calls,
        "created_at": number.created_at.isoformat() if number.created_at else None
    }


@router.put("/{number_id}")
async def update_phone_number(
    number_id: UUID,
    update_data: PhoneNumberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a phone number's description or friendly name.
    """
    result = await db.execute(select(PhoneNumber).where(PhoneNumber.id == number_id))
    number = result.scalar_one_or_none()
    
    if not number:
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    # Check access - only client admins or platform admins can update
    if not current_user.is_admin():
        if number.client_id != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if not current_user.is_client_admin():
            raise HTTPException(status_code=403, detail="Only admins can update phone numbers")
    
    # Update fields
    if update_data.friendly_name is not None:
        number.friendly_name = update_data.friendly_name
    
    if update_data.description is not None:
        number.description = update_data.description
    
    if update_data.number_type is not None:
        try:
            number.number_type = PhoneNumberType(update_data.number_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid number type")
    
    await db.commit()
    await db.refresh(number)
    
    return {
        "id": str(number.id),
        "number": number.number,
        "friendly_name": number.friendly_name,
        "description": number.description,
        "number_type": number.number_type.value,
        "message": "Phone number updated successfully"
    }


def _get_type_label(number_type: PhoneNumberType) -> str:
    """Get human-readable label for phone number type"""
    labels = {
        PhoneNumberType.AI_INBOUND: "AI Inbound",
        PhoneNumberType.TRANSFER_HIGH: "Transfer Queue ($35K+)",
        PhoneNumberType.TRANSFER_MID: "Transfer Queue ($10K-$35K)",
        PhoneNumberType.TRANSFER_LOW: "Transfer Queue (<$10K)",
        PhoneNumberType.OUTBOUND: "Outbound"
    }
    return labels.get(number_type, number_type.value)

