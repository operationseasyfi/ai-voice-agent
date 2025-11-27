#!/usr/bin/env python3
"""Startup script that runs migrations before starting the app."""
import subprocess
import sys
import time
from sqlalchemy import create_engine, text
from app.config import settings

def wait_for_db(max_retries=30):
    """Wait for database to be ready."""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database is ready!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ Database not ready (attempt {i+1}/{max_retries}), waiting 2 seconds...")
                time.sleep(2)
            else:
                print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                return False
    return False

def cleanup_orphaned_types():
    """Drop orphaned enum types from previous failed migrations."""
    print("🧹 Cleaning up orphaned database types...")
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    try:
        with engine.begin() as conn:  # begin() auto-commits
            # Drop enum types if they exist (from previous failed migrations)
            types_to_drop = [
                'phonenumbertype',
                'transfertier',
                'disconnectionreason'
            ]
            for enum_type in types_to_drop:
                try:
                    conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
                    print(f"  ✓ Dropped {enum_type} if it existed")
                except Exception as e:
                    print(f"  ⚠ Could not drop {enum_type}: {e}")
        print("✅ Cleanup complete!")
        return True
    except Exception as e:
        print(f"⚠ Cleanup warning (continuing anyway): {e}")
        return True  # Continue even if cleanup fails

def run_migrations():
    """Run Alembic migrations."""
    print("🔄 Running database migrations...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Migrations completed successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        # Check if it's a "already exists" error - might be recoverable
        error_output = e.stderr.lower()
        if "already exists" in error_output or "duplicate" in error_output:
            print("⚠ Migration failed due to existing objects.")
            print("This might be recoverable. Attempting to continue...")
            print(f"Error details: {e.stderr}")
            # Try to continue anyway - tables might still be created
            return True
        print(f"❌ Migration failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def start_app():
    """Start the Uvicorn server."""
    print("🚀 Starting application...")
    subprocess.run([
        "uvicorn", "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--workers", "4"
    ])

if __name__ == "__main__":
    if not wait_for_db():
        print("❌ Failed to connect to database. Exiting.")
        sys.exit(1)
    
    cleanup_orphaned_types()
    
    if not run_migrations():
        print("❌ Migrations failed. Exiting.")
        sys.exit(1)
    
    start_app()

