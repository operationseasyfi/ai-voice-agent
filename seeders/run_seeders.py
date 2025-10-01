#!/usr/bin/env python3
"""
Main seeder runner script
Runs all database seeders
"""

import sys
import os
import asyncio

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from admin_user_seeder import AdminUserSeeder


async def run_all_seeders():
    """Run all seeders in order."""
    
    seeders = [
        AdminUserSeeder(),
        # Add more seeders here as you create them
    ]
    
    async with AsyncSessionLocal() as db:
        print("🌱 Starting database seeding...")
        
        for seeder in seeders:
            try:
                print(f"  Running {seeder.name}...")
                await seeder.seed(db)
                await db.commit()
                print(f"  ✅ {seeder.name} completed successfully")
            except Exception as e:
                print(f"  ❌ {seeder.name} failed: {e}")
                await db.rollback()
                raise
        
        print("🎉 All seeders completed successfully!")


async def run_specific_seeder(seeder_name: str):
    """Run a specific seeder by name."""
    
    seeder_map = {
        "admin": AdminUserSeeder(),
    }
    
    if seeder_name not in seeder_map:
        print(f"❌ Seeder '{seeder_name}' not found")
        print(f"Available seeders: {', '.join(seeder_map.keys())}")
        return
    
    seeder = seeder_map[seeder_name]
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"🌱 Running {seeder.name}...")
            await seeder.seed(db)
            await db.commit()
            print(f"✅ {seeder.name} completed successfully!")
        except Exception as e:
            print(f"❌ {seeder.name} failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific seeder
        seeder_name = sys.argv[1]
        asyncio.run(run_specific_seeder(seeder_name))
    else:
        # Run all seeders
        asyncio.run(run_all_seeders())