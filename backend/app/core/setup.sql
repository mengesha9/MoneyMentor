-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create user_progress table with all required columns
CREATE TABLE IF NOT EXISTS user_progress (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id text NOT NULL,
    quiz_scores jsonb DEFAULT '{}',
    topics_covered jsonb DEFAULT '{}',
    last_activity timestamp with time zone DEFAULT now(),
    last_quiz_type text,
    last_quiz_score numeric,
    last_quiz_date timestamp with time zone,
    strengths jsonb DEFAULT '[]',
    weaknesses jsonb DEFAULT '[]',
    recommendations jsonb DEFAULT '[]',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);

-- Create dedicated quiz_responses table for Google Sheets integration
CREATE TABLE IF NOT EXISTS quiz_responses (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id text NOT NULL,
    timestamp timestamp with time zone DEFAULT now(),
    quiz_id text NOT NULL,
    topic text,
    selected text,
    correct boolean,
    quiz_type text DEFAULT 'micro',
    score numeric,
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quiz_responses_user_id ON quiz_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_responses_timestamp ON quiz_responses(timestamp);

-- Create content_files table for file metadata
CREATE TABLE IF NOT EXISTS content_files (
    file_id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename text NOT NULL,
    content_type text NOT NULL,
    uploaded_at timestamp with time zone DEFAULT now(),
    status text DEFAULT 'processing',
    chunk_count integer DEFAULT 0,
    error text,
    processed_chunks integer DEFAULT 0,
    progress_percentage numeric(5, 2) DEFAULT 0,
    estimated_time_remaining numeric(10, 2),
    processing_time numeric(10, 2),
    file_size bigint,
    retry_count integer DEFAULT 0,
    failed_chunks integer[] DEFAULT '{}'::integer[]
);

CREATE INDEX IF NOT EXISTS idx_content_files_status ON content_files(status);
CREATE INDEX IF NOT EXISTS idx_content_files_progress ON content_files(progress_percentage);
CREATE INDEX IF NOT EXISTS idx_content_files_retry ON content_files(retry_count);

-- Create content_chunks table for vector storage
CREATE TABLE IF NOT EXISTS content_chunks (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id uuid REFERENCES content_files(file_id) ON DELETE CASCADE,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding vector(1536),
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_content_chunks_file_id ON content_chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_content_chunks_chunk_index ON content_chunks(chunk_index);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id text UNIQUE,  -- Custom session_id from frontend
    user_id text NOT NULL,
    chat_history jsonb DEFAULT '[]',
    progress jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);

-- Create chat_history table
CREATE TABLE IF NOT EXISTS chat_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id text NOT NULL,
    message text,
    role text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);