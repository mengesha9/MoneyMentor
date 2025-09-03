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
    user_id text NOT NULL,
    chat_history jsonb DEFAULT '[]',
    quiz_history jsonb DEFAULT '[]',
    progress jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

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

-- Create chat_history table
CREATE TABLE IF NOT EXISTS chat_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id text NOT NULL,
    message text,
    role text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);

-- Create courses table
CREATE TABLE IF NOT EXISTS courses (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    title text NOT NULL,
    module text NOT NULL,
    track text NOT NULL,
    estimated_length text,
    lesson_overview text,
    learning_objectives jsonb DEFAULT '[]',
    core_concepts jsonb DEFAULT '[]',
    key_terms jsonb DEFAULT '[]',
    real_life_scenarios jsonb DEFAULT '[]',
    mistakes_to_avoid jsonb DEFAULT '[]',
    action_steps jsonb DEFAULT '[]',
    summary text,
    reflection_prompt text,
    course_level text DEFAULT 'beginner',
    why_recommended text,
    has_quiz boolean DEFAULT true,
    topic text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_courses_topic ON courses(topic);
CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(course_level);

-- Create course_pages table
CREATE TABLE IF NOT EXISTS course_pages (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id uuid REFERENCES courses(id) ON DELETE CASCADE,
    page_index integer NOT NULL,
    title text NOT NULL,
    content text NOT NULL,
    page_type text DEFAULT 'content', -- 'content', 'quiz', 'summary'
    quiz_data jsonb DEFAULT NULL, -- For quiz pages
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    UNIQUE(course_id, page_index)
);

CREATE INDEX IF NOT EXISTS idx_course_pages_course_id ON course_pages(course_id);
CREATE INDEX IF NOT EXISTS idx_course_pages_page_index ON course_pages(page_index);

-- Create user_course_sessions table
CREATE TABLE IF NOT EXISTS user_course_sessions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id text NOT NULL,
    course_id uuid REFERENCES courses(id) ON DELETE CASCADE,
    current_page_index integer DEFAULT 0,
    completed boolean DEFAULT false,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    quiz_answers jsonb DEFAULT '{}', -- Store quiz answers for the course
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    UNIQUE(user_id, course_id)
);

CREATE INDEX IF NOT EXISTS idx_user_course_sessions_user_id ON user_course_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_course_sessions_course_id ON user_course_sessions(course_id);

-- Create vector search indexes for content_chunks
CREATE INDEX IF NOT EXISTS content_chunks_embedding_hnsw_idx ON content_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS content_chunks_file_chunk_idx ON content_chunks (file_id, chunk_index); 