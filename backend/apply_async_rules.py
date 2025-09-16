#!/usr/bin/env python3
"""
Apply Non-Blocking Rules to Services
Updates all .execute() calls to be wrapped with await asyncio.to_thread(...)
"""
import os
import re

def apply_rules_to_file(file_path):
    """Apply non-blocking rules to a single file"""
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Simple Supabase execute() calls
    # Before: result = supabase.table('table').select().execute()
    # After: result = await asyncio.to_thread(lambda: supabase.table('table').select().execute())
    supabase_pattern = r'(\s+)(\w+)\s*=\s*(supabase\.table\([^)]+\)(?:\.[^.]+\([^)]*\))*\.execute\(\))'
    
    def replace_supabase(match):
        indent = match.group(1)
        var_name = match.group(2)
        supabase_call = match.group(3)
        return f'{indent}{var_name} = await asyncio.to_thread(lambda: {supabase_call})'
    
    content = re.sub(supabase_pattern, replace_supabase, content)
    
    # Pattern 2: Remove asyncio.wait_for wrappers around asyncio.to_thread for Google Sheets
    # Before: await asyncio.wait_for(asyncio.to_thread(...), timeout=120.0)
    # After: await asyncio.to_thread(...)
    wait_for_pattern = r'await\s+asyncio\.wait_for\(\s*(asyncio\.to_thread\([^)]+\)),\s*timeout=[\d.]+\s*\)'
    content = re.sub(wait_for_pattern, r'await \1', content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Updated {file_path}")
        return True
    else:
        print(f"ℹ️ No changes needed for {file_path}")
        return False

def main():
    """Main function to apply rules to all service files"""
    print("🔧 Applying Non-Blocking Rules to Services...")
    print("=" * 60)
    
    files_to_update = [
        'app/services/google_sheets_service.py',
        'comprehensive_sync.py',
        'app/services/background_sync_service.py'
    ]
    
    updated_count = 0
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            if apply_rules_to_file(file_path):
                updated_count += 1
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print("=" * 60)
    print(f"📊 Updated {updated_count} files")
    print("✅ Non-blocking rules applied successfully!")

if __name__ == "__main__":
    main()