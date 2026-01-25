-- Create table for logging competitor queries
create table if not exists public.competitor_queries (
    id uuid not null default gen_random_uuid(),
    clinic_id uuid references public.clinics(id) on delete cascade,
    session_id uuid references public.chat_sessions(id) on delete set null,
    query text not null,
    detected_keyword text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    
    constraint competitor_queries_pkey primary key (id)
);

-- Enable Row Level Security (RLS)
alter table public.competitor_queries enable row level security;

-- Allow the service role (backend API) to insert and select data
create policy "Service role can manage competitor queries"
    on public.competitor_queries
    using ( true )
    with check ( true );