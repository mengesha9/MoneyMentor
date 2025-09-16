#!/usr/bin/env python3
"""
Check and create test user for authentication testing
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_test_user():
    """Check if test user exists and create if needed"""
    from app.core.database import get_supabase
    from app.core.auth import get_password_hash
    
    supabase = get_supabase()
    try:
        # Check if test user exists
        result = supabase.table('users').select('*').eq('email', 'test@example.com').execute()
        if result.data:
            user = result.data[0]
            print(f'✅ Test user exists: {user["email"]}')
            print(f'   - ID: {user["id"]}')
            print(f'   - Active: {user["is_active"]}')
            print(f'   - Has password hash: {bool(user.get("password_hash"))}')
            
            # Test password verification
            from app.core.auth import verify_password
            password_valid = verify_password('testpassword123', user['password_hash'])
            print(f'   - Password valid: {password_valid}')
            
            if not password_valid:
                print('🔧 Updating password...')
                new_hash = get_password_hash('testpassword123')
                update_result = supabase.table('users').update({
                    'password_hash': new_hash
                }).eq('id', user['id']).execute()
                
                if update_result.data:
                    print('✅ Password updated successfully')
                else:
                    print('❌ Failed to update password')
        else:
            print('❌ Test user does not exist - creating...')
            
            # Create test user
            password_hash = get_password_hash('testpassword123')
            
            create_result = supabase.table('users').insert({
                'email': 'test@example.com',
                'password_hash': password_hash,
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
                'is_verified': True
            }).execute()
            
            if create_result.data:
                print('✅ Test user created successfully')
                print(f'   - ID: {create_result.data[0]["id"]}')
            else:
                print('❌ Failed to create test user')
                
    except Exception as e:
        print(f'❌ Error checking test user: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_test_user())