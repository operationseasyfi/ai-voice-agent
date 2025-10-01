"""
Base seeder class for database seeders
"""

import asyncio
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal


class BaseSeeder(ABC):
    """Base class for all seeders."""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def seed(self, db: AsyncSession) -> None:
        """Implement the seeding logic."""
        pass
    
    async def run(self) -> None:
        """Run the seeder."""
        print(f"🌱 Running seeder: {self.name}")
        
        async with AsyncSessionLocal() as db:
            try:
                await self.seed(db)
                await db.commit()
                print(f"✅ Seeder {self.name} completed successfully!")
            except Exception as e:
                await db.rollback()
                print(f"❌ Seeder {self.name} failed: {e}")
                raise
    
    def log(self, message: str) -> None:
        """Log a message with seeder name."""
        print(f"   {self.name}: {message}")


class SeederRunner:
    """Runner for multiple seeders."""
    
    def __init__(self):
        self.seeders = []
    
    def add_seeder(self, seeder: BaseSeeder) -> None:
        """Add a seeder to the runner."""
        self.seeders.append(seeder)
    
    async def run_all(self) -> None:
        """Run all seeders."""
        print("🚀 Starting database seeding...\n")
        
        for seeder in self.seeders:
            await seeder.run()
            print()  # Add spacing between seeders
        
        print("🎉 All seeders completed successfully!")


def run_seeders(*seeders: BaseSeeder) -> None:
    """Convenience function to run seeders."""
    async def _run():
        runner = SeederRunner()
        for seeder in seeders:
            runner.add_seeder(seeder)
        await runner.run_all()
    
    asyncio.run(_run())