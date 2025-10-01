"""
Admin user seeder
Creates the initial admin user for the system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from base_seeder import BaseSeeder
from app.models.models import User
from app.auth.utils import get_password_hash
import uuid


class AdminUserSeeder(BaseSeeder):
    """Seeder for creating the admin user."""
    
    async def seed(self, db: AsyncSession) -> None:
        """Create the admin user if it doesn't exist."""
        
        # Check if admin user already exists
        admin_email = "admin@example.com"
        result = await db.execute(select(User).where(User.email == admin_email))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            self.log(f"Admin user already exists: {admin_email}")
            return
        
        # Create admin user
        admin_user = User(
            id=uuid.uuid4(),
            full_name="System Administrator",
            username="admin",
            email=admin_email,
            password=get_password_hash("password"),  # Hash the password
            phone_number="+1234567890",
            is_active=True,
            roles='["admin", "superuser"]',  # JSON string for roles
            permissions='["all"]',  # JSON string for permissions
            preferences={
                "theme": "light",
                "notifications": True,
                "language": "en"
            }
        )
        
        db.add(admin_user)
        
        self.log(f"Created admin user: {admin_email}")
        self.log("Default credentials:")
        self.log("  Email: admin@example.com")
        self.log("  Password: password")


# Convenience function to run just this seeder
async def seed_admin_user():
    """Run the admin user seeder."""
    seeder = AdminUserSeeder()
    await seeder.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_admin_user())