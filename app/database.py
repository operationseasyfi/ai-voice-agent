from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
)

# Create async session
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    def to_dict(self):
        """Return a dictionary representation of the user."""
        return {column.name: self.parse(getattr(self, column.name)) for column in self.__table__.columns}

    def parse(self, value):
        import json
        try:
            if isinstance(value, str):
                return json.loads(value)
            else:
                return value
        except (TypeError, ValueError):
            return value



# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()