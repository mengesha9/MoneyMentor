import asyncio
from app.core.auth import get_password_hash, update_user
from app.core.database import get_supabase

async def update_test_user_password():
    supabase = get_supabase()
    result = supabase.table('users').select('id').eq('email', 'test@example.com').execute()
    
    if result.data:
        user_id = result.data[0]['id']
        hashed_password = get_password_hash('password123')
        updated = await update_user(user_id, {'password_hash': hashed_password})
        print('Password updated successfully:', bool(updated))
    else:
        print('User not found')

if __name__ == "__main__":
    asyncio.run(update_test_user_password())
