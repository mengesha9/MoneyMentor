//1

create table public.content_chunks (
  id bigserial not null,
  file_id uuid null,
  chunk_index integer not null,
  content text not null,
  embedding public.vector null,
  user_id text not null,
  constraint content_chunks_pkey primary key (id),
  constraint content_chunks_file_id_fkey foreign KEY (file_id) references content_files (file_id)
) TABLESPACE pg_default;

create index IF not exists content_chunks_file_id_idx on public.content_chunks using btree (file_id) TABLESPACE pg_default;

create index IF not exists content_chunks_embedding_idx on public.content_chunks using ivfflat (embedding vector_cosine_ops) TABLESPACE pg_default;

create index IF not exists content_chunks_user_id_idx on public.content_chunks using btree (user_id) TABLESPACE pg_default;




// 2 
create table public.content_files (
  file_id uuid not null,
  filename text not null,
  content_type text not null,
  uploaded_at timestamp with time zone null default CURRENT_TIMESTAMP,
  status text not null default 'processing'::text,
  chunk_count integer null,
  error text null,
  processed_chunks integer null default 0,
  progress_percentage numeric(5, 2) null default 0,
  estimated_time_remaining numeric(10, 2) null,
  processing_time numeric(10, 2) null,
  file_size bigint null,
  retry_count integer null default 0,
  failed_chunks integer[] null default '{}'::integer[],
  constraint content_files_pkey primary key (file_id)
) TABLESPACE pg_default;

create index IF not exists idx_content_files_status on public.content_files using btree (status) TABLESPACE pg_default;

create index IF not exists idx_content_files_progress on public.content_files using btree (progress_percentage) TABLESPACE pg_default;

create index IF not exists idx_content_files_retry on public.content_files using btree (retry_count) TABLESPACE pg_default;


// 3


create table public.course_pages (
  id uuid not null default extensions.uuid_generate_v4 (),
  course_id uuid null,
  page_index integer not null,
  title text not null,
  content text not null,
  page_type text null default 'content'::text,
  quiz_data jsonb null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint course_pages_pkey primary key (id),
  constraint course_pages_course_id_page_index_key unique (course_id, page_index),
  constraint course_pages_course_id_fkey foreign KEY (course_id) references courses (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_course_pages_course_id on public.course_pages using btree (course_id) TABLESPACE pg_default;

create index IF not exists idx_course_pages_page_index on public.course_pages using btree (page_index) TABLESPACE pg_default;


//4

create table public.courses (
  id uuid not null default extensions.uuid_generate_v4 (),
  title text not null,
  module text not null,
  track text not null,
  estimated_length text null,
  lesson_overview text null,
  learning_objectives jsonb null default '[]'::jsonb,
  core_concepts jsonb null default '[]'::jsonb,
  key_terms jsonb null default '[]'::jsonb,
  real_life_scenarios jsonb null default '[]'::jsonb,
  mistakes_to_avoid jsonb null default '[]'::jsonb,
  action_steps jsonb null default '[]'::jsonb,
  summary text null,
  reflection_prompt text null,
  course_level text null default 'beginner'::text,
  why_recommended text null,
  has_quiz boolean null default true,
  topic text null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint courses_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_courses_topic on public.courses using btree (topic) TABLESPACE pg_default;

create index IF not exists idx_courses_level on public.courses using btree (course_level) TABLESPACE pg_default;

//5 
create table public.courses (
  id uuid not null default extensions.uuid_generate_v4 (),
  title text not null,
  module text not null,
  track text not null,
  estimated_length text null,
  lesson_overview text null,
  learning_objectives jsonb null default '[]'::jsonb,
  core_concepts jsonb null default '[]'::jsonb,
  key_terms jsonb null default '[]'::jsonb,
  real_life_scenarios jsonb null default '[]'::jsonb,
  mistakes_to_avoid jsonb null default '[]'::jsonb,
  action_steps jsonb null default '[]'::jsonb,
  summary text null,
  reflection_prompt text null,
  course_level text null default 'beginner'::text,
  why_recommended text null,
  has_quiz boolean null default true,
  topic text null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint courses_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_courses_topic on public.courses using btree (topic) TABLESPACE pg_default;

create index IF not exists idx_courses_level on public.courses using btree (course_level) TABLESPACE pg_default;


//6


create table public.quiz_responses (
  id uuid not null default extensions.uuid_generate_v4 (),
  user_id text not null,
  timestamp timestamp with time zone null default now(),
  quiz_id text not null,
  topic text null,
  selected text null,
  correct boolean null,
  quiz_type text null default 'micro'::text,
  score numeric null,
  created_at timestamp with time zone null default now(),
  -- Add missing fields for quiz details
  explanation text null,
  correct_answer text null,
  question_data jsonb null,
  session_id text null,
  course_id uuid null,
  page_index integer null,
  constraint quiz_responses_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_quiz_responses_user_id on public.quiz_responses using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_quiz_responses_timestamp on public.quiz_responses using btree ("timestamp") TABLESPACE pg_default;

create index IF not exists idx_quiz_responses_quiz_id on public.quiz_responses using btree (quiz_id) TABLESPACE pg_default;

create trigger update_user_activity_quiz_trigger
after INSERT on quiz_responses for EACH row
execute FUNCTION trigger_update_user_activity_and_counters();


//7


create table public.user_course_sessions (
  id uuid not null default extensions.uuid_generate_v4 (),
  user_id text not null,
  course_id uuid null,
  current_page_index integer null default 0,
  completed boolean null default false,
  started_at timestamp with time zone null default now(),
  completed_at timestamp with time zone null,
  quiz_answers jsonb null default '{}'::jsonb,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint user_course_sessions_pkey primary key (id),
  constraint user_course_sessions_user_id_course_id_key unique (user_id, course_id),
  constraint user_course_sessions_course_id_fkey foreign KEY (course_id) references courses (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_user_course_sessions_user_id on public.user_course_sessions using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_user_course_sessions_course_id on public.user_course_sessions using btree (course_id) TABLESPACE pg_default;

//8
create table public.user_profiles (
  id uuid not null default extensions.uuid_generate_v4 (),
  user_id uuid null,
  total_chats integer null default 0,
  quizzes_taken integer null default 0,
  day_streak integer null default 0,
  days_active integer null default 0,
  last_activity_date date null default CURRENT_DATE,
  streak_start_date date null default CURRENT_DATE,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint user_profiles_pkey primary key (id),
  constraint user_profiles_user_id_key unique (user_id),
  constraint user_profiles_user_id_fkey foreign KEY (user_id) references users (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_user_profiles_user_id on public.user_profiles using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_user_profiles_last_activity on public.user_profiles using btree (last_activity_date) TABLESPACE pg_default;

//9

create table public.user_progress (
  id uuid not null default extensions.uuid_generate_v4 (),
  user_id text not null,
  quiz_scores jsonb null default '{}'::jsonb,
  topics_covered jsonb null default '{}'::jsonb,
  last_activity timestamp with time zone null default now(),
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  last_quiz_type text null,
  last_quiz_score numeric null,
  last_quiz_date timestamp with time zone null,
  strengths jsonb null default '[]'::jsonb,
  weaknesses jsonb null default '[]'::jsonb,
  recommendations jsonb null default '[]'::jsonb,
  constraint user_progress_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_user_progress_user_id on public.user_progress using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_user_progress_user on public.user_progress using btree (user_id) TABLESPACE pg_default;


//10

create table public.user_progress (
  id uuid not null default extensions.uuid_generate_v4 (),
  user_id text not null,
  quiz_scores jsonb null default '{}'::jsonb,
  topics_covered jsonb null default '{}'::jsonb,
  last_activity timestamp with time zone null default now(),
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  last_quiz_type text null,
  last_quiz_score numeric null,
  last_quiz_date timestamp with time zone null,
  strengths jsonb null default '[]'::jsonb,
  weaknesses jsonb null default '[]'::jsonb,
  recommendations jsonb null default '[]'::jsonb,
  constraint user_progress_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_user_progress_user_id on public.user_progress using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_user_progress_user on public.user_progress using btree (user_id) TABLESPACE pg_default;

//11
create table public.users (
  id uuid not null default extensions.uuid_generate_v4 (),
  email character varying(255) not null,
  password_hash character varying(255) not null,
  first_name character varying(100) null,
  last_name character varying(100) null,
  is_active boolean null default true,
  is_verified boolean null default false,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint users_pkey primary key (id),
  constraint users_email_key unique (email)
) TABLESPACE pg_default;

create index IF not exists idx_users_email on public.users using btree (email) TABLESPACE pg_default;

create index IF not exists idx_users_created_at on public.users using btree (created_at) TABLESPACE pg_default;

//12

create table public.vector_memory (
  id text not null,
  user_id text not null,
  session_id text not null,
  content text not null,
  role text not null,
  timestamp timestamp with time zone not null default now(),
  embedding public.vector null,
  metadata jsonb null default '{}'::jsonb,
  created_at timestamp with time zone null default now(),
  constraint vector_memory_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_vector_memory_user_id on public.vector_memory using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_vector_memory_session_id on public.vector_memory using btree (session_id) TABLESPACE pg_default;

create index IF not exists idx_vector_memory_timestamp on public.vector_memory using btree ("timestamp" desc) TABLESPACE pg_default;

create index IF not exists idx_vector_memory_embedding on public.vector_memory using ivfflat (embedding vector_cosine_ops) TABLESPACE pg_default;

create index IF not exists idx_vector_memory_user_timestamp on public.vector_memory using btree (user_id, "timestamp" desc) TABLESPACE pg_default;

create index IF not exists idx_vector_memory_role on public.vector_memory using btree (role) TABLESPACE pg_default;

create index IF not exists idx_vector_memory_embedding_hnsw on public.vector_memory using hnsw (embedding vector_cosine_ops)
with
  (m = '16', ef_construction = '64') TABLESPACE pg_default;

create index IF not exists idx_vector_memory_user_session on public.vector_memory using btree (user_id, session_id) TABLESPACE pg_default;

create index IF not exists idx_vector_memory_metadata on public.vector_memory using gin (metadata) TABLESPACE pg_default;


//13

create table public.user_sessions (
  id uuid not null default extensions.uuid_generate_v4 (),
  user_id text not null,
  chat_history jsonb null default '[]'::jsonb,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  quiz_history jsonb null default '[]'::jsonb,
  progress jsonb null default '{}'::jsonb,
  last_active timestamp with time zone null default CURRENT_TIMESTAMP,
  session_id uuid null default gen_random_uuid (),
  constraint user_sessions_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_user_sessions_user_id on public.user_sessions using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_user_sessions_user on public.user_sessions using btree (user_id) TABLESPACE pg_default;

-- Create trigger for chat activity (user_sessions table)
CREATE TRIGGER update_chat_activity_trigger
    AFTER UPDATE ON user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_chat_activity();

-- Create the chat trigger function
CREATE OR REPLACE FUNCTION trigger_update_chat_activity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Only trigger if chat_history was updated and has new messages
    IF OLD.chat_history IS DISTINCT FROM NEW.chat_history THEN
        -- Count new messages (simple approach: if length increased, it's a new message)
        IF jsonb_array_length(NEW.chat_history) > jsonb_array_length(OLD.chat_history) THEN
            PERFORM update_user_activity_and_counters(NEW.user_id, 'chat');
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

-- Create the new trigger function that handles text→UUID conversion properly
CREATE OR REPLACE FUNCTION trigger_update_user_activity_and_counters()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Call the function that expects text and handles conversion internally
    PERFORM update_user_activity_and_counters(NEW.user_id, 'quiz');
    RETURN NEW;
END;
$$;

-- Create the main function that handles both activity and counters
CREATE OR REPLACE FUNCTION update_user_activity_and_counters(user_uuid text, action_type text DEFAULT NULL)
RETURNS void AS $$
DECLARE
    current_date DATE := CURRENT_DATE;
    last_activity DATE;
    current_streak INTEGER;
    streak_start DATE;
    user_uuid_parsed uuid;
BEGIN
    -- Try to parse the user_uuid as uuid, if it fails, return early
    BEGIN
        user_uuid_parsed := user_uuid::uuid;
    EXCEPTION WHEN OTHERS THEN
        -- If user_uuid is not a valid uuid, return early
        RETURN;
    END;
    
    -- Get current profile data
    SELECT last_activity_date, day_streak, streak_start_date 
    INTO last_activity, current_streak, streak_start
    FROM user_profiles 
    WHERE user_id = user_uuid_parsed;
    
    -- If no profile exists, create one
    IF last_activity IS NULL THEN
        INSERT INTO user_profiles (
            user_id, 
            last_activity_date, 
            day_streak, 
            streak_start_date, 
            days_active,
            total_chats,
            quizzes_taken
        )
        VALUES (
            user_uuid_parsed, 
            current_date, 
            1, 
            current_date, 
            1,
            CASE WHEN action_type = 'chat' THEN 1 ELSE 0 END,
            CASE WHEN action_type = 'quiz' THEN 1 ELSE 0 END
        );
        
        -- Notify application about profile creation
        PERFORM pg_notify('user_profile_updated', json_build_object(
            'user_id', user_uuid_parsed,
            'action', 'created',
            'timestamp', now()
        )::text);
        
        RETURN;
    END IF;
    
    -- Update activity AND counters
    IF last_activity < current_date THEN
        -- New day - update streak and counters
        IF last_activity = current_date - INTERVAL '1 day' THEN
            -- Consecutive day, increment streak
            UPDATE user_profiles 
            SET 
                day_streak = current_streak + 1,
                days_active = days_active + 1,
                last_activity_date = current_date,
                total_chats = total_chats + CASE WHEN action_type = 'chat' THEN 1 ELSE 0 END,
                quizzes_taken = quizzes_taken + CASE WHEN action_type = 'quiz' THEN 1 ELSE 0 END,
                updated_at = now()
            WHERE user_id = user_uuid_parsed;
        ELSE
            -- Break in streak, reset to 1
            UPDATE user_profiles 
            SET 
                day_streak = 1,
                days_active = days_active + 1,
                last_activity_date = current_date,
                streak_start_date = current_date,
                total_chats = total_chats + CASE WHEN action_type = 'chat' THEN 1 ELSE 0 END,
                quizzes_taken = quizzes_taken + CASE WHEN action_type = 'quiz' THEN 1 ELSE 0 END,
                updated_at = now()
            WHERE user_id = user_uuid_parsed;
        END IF;
    ELSE
        -- Same day - only update counters
        UPDATE user_profiles 
        SET 
            total_chats = total_chats + CASE WHEN action_type = 'chat' THEN 1 ELSE 0 END,
            quizzes_taken = quizzes_taken + CASE WHEN action_type = 'quiz' THEN 1 ELSE 0 END,
            updated_at = now()
        WHERE user_id = user_uuid_parsed;
    END IF;
    
    -- Notify application about profile update
    PERFORM pg_notify('user_profile_updated', json_build_object(
        'user_id', user_uuid_parsed,
        'action', 'updated',
        'action_type', action_type,
        'timestamp', now()
    )::text);
END;
$$;