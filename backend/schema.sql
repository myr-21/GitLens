-- 1. Enable the pgvector extension
create extension if not exists vector;

-- 2. Create the repositories table
create table if not exists repositories (
  id uuid primary key default gen_random_uuid(),
  github_id bigint unique not null,
  full_name text not null,
  description text,
  topics text[] default '{}',
  language text,
  stars integer default 0,
  homepage text,
  embedding vector(768),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Create HNSW index for vector similarity search
-- Note: We use cosine similarity (vector_cosine_ops)
create index if not exists repositories_embedding_cosine_idx 
  on repositories using hnsw (embedding vector_cosine_ops);

-- 4. Create GIN index for full-text search on description and topics
create index if not exists repositories_fts_idx 
  on repositories using gin (
    to_tsvector('english', coalesce(description, '') || ' ' || array_to_string(topics, ' '))
  );

-- 5. Create RPC function for pgvector similarity search
create or replace function match_repositories (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  github_id bigint,
  full_name text,
  description text,
  topics text[],
  language text,
  stars int,
  homepage text,
  similarity float,
  created_at timestamp with time zone,
  updated_at timestamp with time zone
)
language sql stable
as $$
  select
    id,
    github_id,
    full_name,
    description,
    topics,
    language,
    stars,
    homepage,
    1 - (embedding <=> query_embedding) as similarity,
    created_at,
    updated_at
  from repositories
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- 6. Create RPC function for full-text search ranking
create or replace function keyword_search_repositories (
  query_text text,
  match_count int
)
returns table (
  id uuid,
  github_id bigint,
  full_name text,
  description text,
  topics text[],
  language text,
  stars int,
  homepage text,
  keyword_score float,
  created_at timestamp with time zone,
  updated_at timestamp with time zone
)
language sql stable
as $$
  select
    id,
    github_id,
    full_name,
    description,
    topics,
    language,
    stars,
    homepage,
    ts_rank(
      to_tsvector('english', coalesce(description, '') || ' ' || array_to_string(topics, ' ')),
      websearch_to_tsquery('english', query_text)
    ) as keyword_score,
    created_at,
    updated_at
  from repositories
  where to_tsvector('english', coalesce(description, '') || ' ' || array_to_string(topics, ' ')) @@ websearch_to_tsquery('english', query_text)
  order by keyword_score desc
  limit match_count;
$$;
