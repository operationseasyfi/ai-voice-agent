from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import BaseModel
import uuid


class Preferences:
    """User preferences model."""
    theme: str = "light" 


class User(BaseModel):
    """
    User model - represents users who can access the dashboard.
    Multi-tenant: Each user belongs to a client (except super admins).
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    
    # Multi-tenant: Link user to a client
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True, index=True)
    
    # User details
    full_name = Column(String)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Roles and permissions
    # Roles: "admin" (platform admin), "client_admin" (client admin), "client_user" (read-only)
    roles = Column(Text, nullable=True)  # JSON string array
    permissions = Column(Text, nullable=True)  # JSON string array
    
    # User preferences
    preferences = Column(JSON, nullable=True, default=Preferences().__dict__)
    
    # Legacy Twilio fields (may not be needed)
    twilio_account_sid = Column(String, nullable=True)
    twilio_auth_token = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="users")
    
    def to_dict_safe(self):
        """Return a safe dictionary representation (excluding sensitive fields)."""
        exclude_fields = {'password', 'twilio_auth_token'}
        
        result = {
            column.name: self.parse(getattr(self, column.name)) 
            for column in self.__table__.columns 
            if column.name not in exclude_fields
        }
        
        # Add client info if available
        if self.client:
            result['client_name'] = self.client.name
            result['client_slug'] = self.client.slug
        
        return result
    
    def is_admin(self):
        """Check if the user has admin role (platform admin)."""
        roles = self.parse(self.roles) if self.roles else []
        return 'admin' in roles
    
    def is_client_admin(self):
        """Check if the user is a client admin."""
        roles = self.parse(self.roles) if self.roles else []
        return 'client_admin' in roles or 'admin' in roles
    
    def can_access_client(self, client_id) -> bool:
        """Check if user can access a specific client's data."""
        # Platform admins can access all clients
        if self.is_admin():
            return True
        # Users can only access their own client's data
        return str(self.client_id) == str(client_id)
