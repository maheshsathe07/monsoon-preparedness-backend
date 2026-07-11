-- Monsoon Preparedness Supabase schema.
-- RLS is intentionally not enabled for this hackathon demo.

create table if not exists users (
  id text primary key,
  email text,
  phone text,
  password_hash text,
  location_lat double precision,
  location_lng double precision,
  prep_level text not null default 'minimal',
  risk_score integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists user_profiles (
  id text primary key,
  user_id text not null,
  family_size integer not null,
  ages jsonb not null default '[]'::jsonb,
  disabilities jsonb not null default '[]'::jsonb,
  risks jsonb not null default '[]'::jsonb,
  pets jsonb not null default '[]'::jsonb,
  location_lat double precision not null,
  location_lng double precision not null,
  updated_at timestamptz not null default now()
);

create table if not exists checklists (
  id text primary key,
  user_id text not null unique,
  items jsonb not null,
  completion_pct integer not null default 0,
  last_regenerated_at timestamptz not null default now()
);

create table if not exists emergency_ids (
  id text primary key,
  user_id text not null,
  qr_code_url text not null,
  pdf_url text not null,
  encrypted_data jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists alerts (
  id text primary key,
  user_id text not null,
  alert_type text not null,
  location_lat double precision not null,
  location_lng double precision not null,
  title text not null,
  description text not null,
  photo_url text,
  validation_score double precision not null default 0.7,
  upvotes integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists supplies (
  id text primary key,
  user_id text not null,
  item_name text not null,
  quantity integer not null,
  expiry_date date,
  category text not null,
  reminder_date date,
  created_at timestamptz not null default now()
);

create table if not exists chat_history (
  id text primary key,
  user_id text not null,
  messages jsonb not null,
  context jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists recovery_reports (
  id text primary key,
  user_id text not null,
  incident_date date not null,
  damage_description text not null,
  photos jsonb not null default '[]'::jsonb,
  insurance_provider text,
  damage_category text,
  severity_level text,
  repair_estimate text,
  incident_summary text,
  pdf_url text,
  created_at timestamptz not null default now()
);

create index if not exists idx_user_profiles_user_id on user_profiles(user_id);
create index if not exists idx_checklists_user_id on checklists(user_id);
create index if not exists idx_alerts_created_at on alerts(created_at desc);
create index if not exists idx_alerts_location on alerts(location_lat, location_lng);
create index if not exists idx_supplies_user_expiry on supplies(user_id, expiry_date);
create index if not exists idx_chat_history_user_created on chat_history(user_id, created_at desc);
