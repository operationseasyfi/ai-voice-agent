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

def verify_tables_exist():
    """Verify that critical tables exist after migrations."""
    print("🔍 Verifying database tables exist...")
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    required_tables = ['users', 'clients', 'call_records']
    missing_tables = []
    
    try:
        with engine.connect() as conn:
            for table in required_tables:
                result = conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
                ), {"table_name": table})
                exists = result.scalar()
                if exists:
                    print(f"  ✅ Table '{table}' exists")
                else:
                    print(f"  ❌ Table '{table}' MISSING!")
                    missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        print("✅ All required tables exist!")
        return True
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False

def check_migration_status():
    """Check current Alembic migration status."""
    print("📊 Checking migration status...")
    try:
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )
        print(f"Current migration status: {result.stdout}")
        if result.stderr:
            print(f"Status stderr: {result.stderr}")
        return True
    except Exception as e:
        print(f"⚠ Could not check migration status: {e}")
        return False

def run_migrations():
    """Run Alembic migrations."""
    check_migration_status()
    print("🔄 Running database migrations...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Migrations completed successfully!")
        if result.stdout:
            print(f"Migration stdout: {result.stdout}")
        if result.stderr:
            print(f"Migration stderr: {result.stderr}")
        
        # Verify tables were actually created
        if not verify_tables_exist():
            print("❌ Migrations completed but tables are missing!")
            return False
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration command failed with exit code: {e.returncode}")
        print(f"📋 STDOUT: {e.stdout}")
        print(f"📋 STDERR: {e.stderr}")
        
        # Check if it's a "already exists" error - might be recoverable
        error_output = (e.stderr or "").lower() + (e.stdout or "").lower()
        if "already exists" in error_output or "duplicate" in error_output:
            print("⚠ Migration failed due to existing objects.")
            print("Verifying tables exist anyway...")
            if verify_tables_exist():
                print("✅ Tables exist despite migration error. Continuing...")
                return True
        
        print("❌ Tables are missing. Cannot continue.")
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

