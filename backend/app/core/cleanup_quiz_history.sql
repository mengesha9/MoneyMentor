-- Optional cleanup script to remove the old quiz_history column from user_sessions
-- This script should be run AFTER confirming that all quiz data has been migrated to quiz_responses

-- Step 1: Verify that all quiz data has been migrated
SELECT 
    'Quiz Migration Verification:' as info,
    COUNT(*) as total_user_sessions,
    COUNT(CASE WHEN quiz_history != '[]' AND quiz_history IS NOT NULL THEN 1 END) as sessions_with_quiz_history,
    COUNT(CASE WHEN quiz_history = '[]' OR quiz_history IS NULL THEN 1 END) as sessions_without_quiz_history
FROM user_sessions;

-- Step 2: Show sample of sessions that still have quiz_history (if any)
SELECT 
    id,
    user_id,
    jsonb_array_length(quiz_history) as quiz_count,
    quiz_history
FROM user_sessions 
WHERE quiz_history != '[]' 
  AND quiz_history IS NOT NULL
LIMIT 5;

-- Step 3: Verify that quiz_responses table has the migrated data
SELECT 
    'Centralized Quiz Data:' as info,
    COUNT(*) as total_quiz_responses,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(CASE WHEN quiz_type = 'session' THEN 1 END) as session_quizzes,
    COUNT(CASE WHEN quiz_type = 'course' THEN 1 END) as course_quizzes,
    COUNT(CASE WHEN quiz_type = 'diagnostic' THEN 1 END) as diagnostic_quizzes,
    COUNT(CASE WHEN quiz_type = 'micro' THEN 1 END) as micro_quizzes
FROM quiz_responses;

-- Step 4: If you're satisfied with the migration, uncomment the following lines to remove the old column
-- WARNING: This will permanently delete the quiz_history column and all its data
-- Only run this if you're absolutely sure the migration is complete and successful

-- ALTER TABLE user_sessions DROP COLUMN IF EXISTS quiz_history;

-- Step 5: Verify the column has been removed (if you ran the DROP command)
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'user_sessions' 
-- ORDER BY ordinal_position; 