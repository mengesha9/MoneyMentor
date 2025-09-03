-- Migration script to update user_sessions table from old to new schema
-- This migrates from session_data JSONB to separate chat_history, quiz_history, and progress fields

-- Step 1: Add new columns
ALTER TABLE user_sessions 
ADD COLUMN IF NOT EXISTS chat_history jsonb DEFAULT '[]',
ADD COLUMN IF NOT EXISTS quiz_history jsonb DEFAULT '[]',
ADD COLUMN IF NOT EXISTS progress jsonb DEFAULT '{}';

-- Step 2: Migrate data from session_data to new columns
-- Extract chat_history from session_data if it exists
UPDATE user_sessions 
SET chat_history = COALESCE(session_data->>'chat_history', '[]')::jsonb
WHERE session_data IS NOT NULL AND session_data ? 'chat_history';

-- Extract quiz_history from session_data if it exists  
UPDATE user_sessions 
SET quiz_history = COALESCE(session_data->>'quiz_history', '[]')::jsonb
WHERE session_data IS NOT NULL AND session_data ? 'quiz_history';

-- Extract progress from session_data if it exists
UPDATE user_sessions 
SET progress = COALESCE(session_data->>'progress', '{}')::jsonb
WHERE session_data IS NOT NULL AND session_data ? 'progress';

-- Step 3: Drop the old session_data column (optional - uncomment if you want to remove it)
-- ALTER TABLE user_sessions DROP COLUMN IF EXISTS session_data;

-- Step 4: Create indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_user_sessions_chat_history ON user_sessions USING gin (chat_history);
CREATE INDEX IF NOT EXISTS idx_user_sessions_quiz_history ON user_sessions USING gin (quiz_history);
CREATE INDEX IF NOT EXISTS idx_user_sessions_progress ON user_sessions USING gin (progress);

-- Step 5: Verify migration
SELECT 
    'user_sessions table schema after migration:' as info,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'user_sessions' 
ORDER BY ordinal_position; 