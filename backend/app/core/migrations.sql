-- Enable vector extension
CREATE OR REPLACE FUNCTION enable_vector_extension()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
END;
$$;

-- Enable UUID extension
CREATE OR REPLACE FUNCTION enable_uuid_extension()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
END;
$$;

-- Create table function
CREATE OR REPLACE FUNCTION create_table(table_name text, table_sql text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE table_sql;
END;
$$;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION enable_vector_extension() TO authenticated;
GRANT EXECUTE ON FUNCTION enable_uuid_extension() TO authenticated;
GRANT EXECUTE ON FUNCTION create_table(text, text) TO authenticated;

-- User Authentication and Profile Tables
-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Refresh tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    is_revoked BOOLEAN DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    UNIQUE(token_hash)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- User profiles table for additional data
CREATE TABLE IF NOT EXISTS user_profiles (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    total_chats INTEGER DEFAULT 0,
    quizzes_taken INTEGER DEFAULT 0,
    day_streak INTEGER DEFAULT 0,
    days_active INTEGER DEFAULT 0,
    last_activity_date DATE DEFAULT CURRENT_DATE,
    streak_start_date DATE DEFAULT CURRENT_DATE,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    UNIQUE(user_id)
);

-- User sessions table (already exists, but adding indexes)
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_created_at ON user_sessions(created_at);

-- Chat history table (already exists, but adding indexes)
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at);

-- Quiz responses table (already exists, but adding indexes)
CREATE INDEX IF NOT EXISTS idx_quiz_responses_user_id ON quiz_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_responses_created_at ON quiz_responses(created_at);

-- Create indexes for user tables
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_activity ON user_profiles(last_activity_date);

-- Function to update user activity and streak
CREATE OR REPLACE FUNCTION update_user_activity(user_uuid uuid)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    current_date DATE := CURRENT_DATE;
    last_activity DATE;
    current_streak INTEGER;
    streak_start DATE;
BEGIN
    -- Get current profile data
    SELECT last_activity_date, day_streak, streak_start_date 
    INTO last_activity, current_streak, streak_start
    FROM user_profiles 
    WHERE user_id = user_uuid;
    
    -- If no profile exists, create one
    IF last_activity IS NULL THEN
        INSERT INTO user_profiles (user_id, last_activity_date, day_streak, streak_start_date, days_active)
        VALUES (user_uuid, current_date, 1, current_date, 1);
        RETURN;
    END IF;
    
    -- Update activity
    IF last_activity < current_date THEN
        -- New day
        IF last_activity = current_date - INTERVAL '1 day' THEN
            -- Consecutive day, increment streak
            UPDATE user_profiles 
            SET 
                day_streak = current_streak + 1,
                days_active = days_active + 1,
                last_activity_date = current_date,
                updated_at = now()
            WHERE user_id = user_uuid;
        ELSE
            -- Break in streak, reset to 1
            UPDATE user_profiles 
            SET 
                day_streak = 1,
                days_active = days_active + 1,
                last_activity_date = current_date,
                streak_start_date = current_date,
                updated_at = now()
            WHERE user_id = user_uuid;
        END IF;
    END IF;
END;
$$;

-- Trigger to automatically update user activity
CREATE OR REPLACE FUNCTION trigger_update_user_activity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM update_user_activity(NEW.user_id);
    RETURN NEW;
END;
$$;

-- Create trigger on chat_history table
DROP TRIGGER IF EXISTS update_user_activity_trigger ON chat_history;
CREATE TRIGGER update_user_activity_trigger
    AFTER INSERT ON chat_history
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_user_activity();

-- Create trigger on quiz_responses table
DROP TRIGGER IF EXISTS update_user_activity_quiz_trigger ON quiz_responses;
CREATE TRIGGER update_user_activity_quiz_trigger
    AFTER INSERT ON quiz_responses
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_user_activity(); 

-- Migration to add missing columns to quiz_responses table
-- Add explanation, correct_answer, question_data, session_id, course_id, page_index columns

-- Add explanation column
ALTER TABLE public.quiz_responses 
ADD COLUMN IF NOT EXISTS explanation text null;

-- Add correct_answer column  
ALTER TABLE public.quiz_responses 
ADD COLUMN IF NOT EXISTS correct_answer text null;

-- Add question_data column
ALTER TABLE public.quiz_responses 
ADD COLUMN IF NOT EXISTS question_data jsonb null;

-- Add session_id column
ALTER TABLE public.quiz_responses 
ADD COLUMN IF NOT EXISTS session_id text null;

-- Add course_id column
ALTER TABLE public.quiz_responses 
ADD COLUMN IF NOT EXISTS course_id uuid null;

-- Add page_index column
ALTER TABLE public.quiz_responses 
ADD COLUMN IF NOT EXISTS page_index integer null; 

-- Migration to fix the foreign key constraint issue
-- The current constraint references the wrong column (id instead of session_id)

-- First, drop the incorrect foreign key constraint if it exists
ALTER TABLE public.quiz_responses 
DROP CONSTRAINT IF EXISTS quiz_responses_session_id_fkey;

-- Option 1: Remove the foreign key constraint entirely (allow NULL session_id)
-- This allows quiz responses to exist without requiring a session

-- Option 2: Add a correct foreign key constraint (uncomment if you want to enforce the relationship)
-- ALTER TABLE public.quiz_responses 
-- ADD CONSTRAINT quiz_responses_session_id_fkey 
-- FOREIGN KEY (session_id) REFERENCES user_sessions(session_id);

-- For now, we'll go with Option 1 (no foreign key constraint) to allow flexibility 