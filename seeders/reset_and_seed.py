#!/usr/bin/env python3
"""
Database reset and seed script
WARNING: This will drop all tables and recreate them with seed data
"""

import sys
import os
import asyncio

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from seeders.run_seeders import main as run_all_seeders


async def reset_database():
    """Drop and recreate all tables."""
    print("⚠️  WARNING: This will drop all existing tables!")
    response = input("Are you sure you want to continue? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Operation cancelled.")
        return False
    
    print("🗑️  Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("🔨 Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database reset completed!")
    return True


async def main():
    """Main function to reset database and run seeders."""
    print("🔄 Database Reset and Seed Tool")
    print("=" * 40)
    
    try:
        # Reset database
        if await reset_database():
            print("\n🌱 Running seeders...")
            # Run seeders
            run_all_seeders()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())