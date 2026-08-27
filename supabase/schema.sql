-- Supabase schema for aai-share-chat (ADR-0008, roadmap Next-v2).
-- Run once in the Supabase SQL editor. The backend connects with the
-- service-role key and enforces access in application code (RBAC visibility
-- filter), so no RLS policies are defined here on purpose.

create table if not exists app_users (
    user_id      text primary key,
    display_name text not null,
    role         text not null
                 check (role in ('employee', 'hr', 'manager', 'executive')),
    created_at   timestamptz not null default now()
);

create table if not exists sessions (
    session_id text primary key,
    created_at timestamptz not null default now()
);

create table if not exists session_messages (
    id             uuid primary key default gen_random_uuid(),
    session_id     text not null references sessions (session_id) on delete cascade,
    sender_user_id text not null,
    sender_role    text not null
                   check (sender_role in ('employee', 'hr', 'manager', 'executive')),
    question       text not null,
    answer         text not null,
    sources        jsonb not null default '[]'::jsonb,
    access_levels  text[] not null default '{}',
    created_at     timestamptz not null default now()
);

create index if not exists session_messages_by_session
    on session_messages (session_id, created_at);

-- Seed the demo registry (mirrors the in-memory default; guest included).
insert into app_users (user_id, display_name, role) values
    ('alice',  'Alice (Employee)',  'employee'),
    ('priya',  'Priya (HR)',        'hr'),
    ('carlos', 'Carlos (Manager)',  'manager'),
    ('dana',   'Dana (Executive)',  'executive'),
    ('guest',  'Guest (Employee)',  'employee')
on conflict (user_id) do nothing;
