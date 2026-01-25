-- Create table for chat feedback (ratings)
create table if not exists public.chat_feedback (
    id uuid not null default gen_random_uuid(),
    clinic_id uuid references public.clinics(id) on delete cascade,
    session_id uuid references public.chat_sessions(id) on delete set null,
    rating text not null, -- 'up', 'down', etc.
    comment text,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    
    constraint chat_feedback_pkey primary key (id)
);

-- Enable Row Level Security (RLS)
alter table public.chat_feedback enable row level security;

-- Allow the service role (backend API) to insert data
create policy "Service role can manage chat feedback"
    on public.chat_feedback
    using ( true )
    with check ( true );