-- Create a function to execute SQL statements
CREATE OR REPLACE FUNCTION exec_sql(sql text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE sql;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION exec_sql(text) TO authenticated;

-- Create match_chunks function for vector similarity search
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.3,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    file_id uuid,
    chunk_index integer,
    content text,
    similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cc.id,
        cc.file_id,
        cc.chunk_index,
        cc.content,
        1 - (cc.embedding <=> query_embedding) as similarity
    FROM content_chunks cc
    WHERE cc.embedding IS NOT NULL
    AND 1 - (cc.embedding <=> query_embedding) > match_threshold
    ORDER BY cc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION match_chunks(vector, float, int) TO authenticated;

-- Create find_duplicate_chunks function for storage optimization
CREATE OR REPLACE FUNCTION find_duplicate_chunks(similarity_threshold float DEFAULT 0.95)
RETURNS TABLE (
    chunk_ids uuid[],
    content_preview text,
    similarity_score float
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    WITH duplicates AS (
        SELECT 
            array_agg(cc.id ORDER BY cc.created_at) as chunk_ids,
            cc.content,
            1 - (cc.embedding <=> cc.embedding) as similarity_score
        FROM content_chunks cc
        GROUP BY cc.content, cc.embedding
        HAVING COUNT(*) > 1
    )
    SELECT 
        d.chunk_ids,
        LEFT(d.content, 100) as content_preview,
        d.similarity_score
    FROM duplicates d
    WHERE d.similarity_score >= similarity_threshold;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION find_duplicate_chunks(float) TO authenticated; 