#!/usr/bin/env python3
"""
Script to run database migrations for the MoneyMentor backend
This will create the necessary tables for user authentication and profiles
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_supabase
from app.core.config import settings

async def run_migrations():
    """Run database migrations"""
    print("🚀 Starting database migrations...")
    
    try:
        supabase = get_supabase()
        
        # Read the main migrations file
        migrations_file = backend_dir / "app" / "core" / "migrations.sql"
        
        if not migrations_file.exists():
            print(f"❌ Migrations file not found: {migrations_file}")
            return False
        
        with open(migrations_file, 'r') as f:
            migrations_sql = f.read()
        
        # Read the session schema migration file
        session_migration_file = backend_dir / "app" / "core" / "migrate_session_schema.sql"
        
        if session_migration_file.exists():
            with open(session_migration_file, 'r') as f:
                session_migrations_sql = f.read()
            migrations_sql += "\n" + session_migrations_sql
            print("📋 Session schema migration included")
        else:
            print("⚠️  Session schema migration file not found, skipping")
        
        print("📋 Executing migrations...")
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in migrations_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    print(f"   Executing statement {i}/{len(statements)}...")
                    supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"   ✅ Statement {i} executed successfully")
                except Exception as e:
                    print(f"   ⚠️  Statement {i} failed (this might be expected if objects already exist): {e}")
                    # Continue with other statements
        
        print("✅ Database migrations completed!")
        
        # Verify tables were created
        print("\n🔍 Verifying tables...")
        
        tables_to_check = [
            'users',
            'user_profiles',
            'user_sessions',
            'chat_history',
            'quiz_responses'
        ]
        
        for table in tables_to_check:
            try:
                result = supabase.table(table).select('count').limit(1).execute()
                print(f"   ✅ Table '{table}' exists and is accessible")
            except Exception as e:
                print(f"   ❌ Table '{table}' not accessible: {e}")
        
        print("\n🎉 Migration verification completed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

async def create_test_user():
    """Create a test user for development"""
    print("\n👤 Creating test user...")
    
    try:
        from app.core.auth import create_user
        from app.services.user_service import UserService
        
        # Create test user
        test_user = await create_user(
            email="test@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User"
        )
        
        if test_user:
            print(f"   ✅ Test user created: {test_user['email']}")
            
            # Create user profile
            user_service = UserService()
            profile = await user_service.get_user_profile(test_user['id'])
            
            if profile:
                print(f"   ✅ User profile created for: {test_user['email']}")
            else:
                print(f"   ⚠️  User profile creation failed for: {test_user['email']}")
        else:
            print("   ⚠️  Test user creation failed (might already exist)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test user creation failed: {e}")
        return False

async def main():
    """Main function"""
    print("=" * 60)
    print("MoneyMentor Database Migration Tool")
    print("=" * 60)
    
    # Check environment
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("❌ Missing Supabase configuration")
        print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file")
        return
    
    print(f"📊 Supabase URL: {settings.SUPABASE_URL}")
    print(f"🔑 Using service key: {'*' * 20}{settings.SUPABASE_KEY[-4:]}")
    print()
    
    # Run migrations
    success = await run_migrations()
    
    if success:
        # Create test user in development
        if settings.ENVIRONMENT == "development":
            await create_test_user()
        
        print("\n" + "=" * 60)
        print("🎉 Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start the API server: uvicorn app.main:app --reload")
        print("2. Visit http://localhost:8000/docs to see the API documentation")
        print("3. Test the user endpoints:")
        print("   - POST /api/user/register")
        print("   - POST /api/user/login")
        print("   - GET /api/user/profile")
        print("\nFor development, you can use the test user:")
        print("   Email: test@example.com")
        print("   Password: testpassword123")
    else:
        print("\n" + "=" * 60)
        print("❌ Migration failed!")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 