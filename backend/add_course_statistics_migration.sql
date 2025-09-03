-- Migration: Add course_statistics column to user_profiles table
-- This column will store an array of course statistics objects

-- Add the course_statistics column as JSONB
ALTER TABLE public.user_profiles 
ADD COLUMN course_statistics JSONB DEFAULT '[]'::jsonb;

-- Add an index for better query performance on the JSONB column
CREATE INDEX IF NOT EXISTS idx_user_profiles_course_statistics 
ON public.user_profiles USING GIN (course_statistics);

-- Add a comment to document the structure
COMMENT ON COLUMN public.user_profiles.course_statistics IS 
'Array of course statistics objects. Each object contains: {
  "course_name": "string",
  "total_questions_taken": number,
  "score": number,
  "tabs_completed": number,
  "level": "easy" | "medium" | "hard"
}';

-- Example of how the data will look:
-- [
--   {
--     "course_name": "Budgeting and Saving",
--     "total_questions_taken": 15,
--     "score": 85,
--     "tabs_completed": 3,
--     "level": "medium"
--   },
--   {
--     "course_name": "Money, Goals and Mindset",
--     "total_questions_taken": 10,
--     "score": 92,
--     "tabs_completed": 2,
--     "level": "easy"
--   }
-- ]
