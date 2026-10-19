-- ONE-TIME SETUP. Keep the returned family_connection_code private.
-- If no row is returned, a family already exists. Do not delete its data.

-- Supabase Free: no frontend signup, password, email delivery, or anonymous auth setup.
-- A 256-bit family link is the access credential. Only its SHA-256 hash is stored here.
begin;
create schema if not exists private;
revoke all on schema private from public, anon, authenticated;
create extension if not exists pgcrypto with schema extensions;

create table if not exists private.family_kitchens (
  id uuid primary key default gen_random_uuid(),
  name text not null default '我的家',
  access_key_hash bytea not null unique,
  revision bigint not null default 0 check (revision >= 0),
  state jsonb check (state is null or (jsonb_typeof(state) = 'object' and state->>'version' = '1')),
  updated_at timestamptz not null default now()
);
alter table private.family_kitchens enable row level security;
revoke all on private.family_kitchens from public, anon, authenticated;

create or replace function public.read_family_kitchen(access_key text, known_revision bigint default -1)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  kitchen private.family_kitchens%rowtype;
  result jsonb;
begin
  if access_key is null or access_key !~ '^[a-f0-9]{64}$' then
    raise sqlstate 'PT403' using message = 'INVALID_FAMILY_LINK';
  end if;
  select * into kitchen from private.family_kitchens
    where access_key_hash = extensions.digest(access_key, 'sha256');
  if not found then
    raise sqlstate 'PT403' using message = 'INVALID_FAMILY_LINK';
  end if;
  result := pg_catalog.jsonb_build_object(
    'family_id', kitchen.id, 'revision', kitchen.revision,
    'updated_at', kitchen.updated_at, 'has_state', kitchen.state is not null
  );
  -- Steady-state polls return only a small revision record, not the full history.
  if known_revision is distinct from kitchen.revision then
    result := result || pg_catalog.jsonb_build_object('state', kitchen.state);
  end if;
  return result;
end;
$$;

create or replace function public.sync_family_kitchen(access_key text, expected_revision bigint, new_state jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  key_hash bytea;
  saved private.family_kitchens%rowtype;
begin
  if access_key is null or access_key !~ '^[a-f0-9]{64}$' then
    raise sqlstate 'PT403' using message = 'INVALID_FAMILY_LINK';
  end if;
  key_hash := extensions.digest(access_key, 'sha256');
  if not exists (select 1 from private.family_kitchens where access_key_hash = key_hash) then
    raise sqlstate 'PT403' using message = 'INVALID_FAMILY_LINK';
  end if;
  if expected_revision is null or expected_revision < 0
     or jsonb_typeof(new_state) is distinct from 'object'
     or new_state->>'version' is distinct from '1'
     or pg_catalog.octet_length(new_state::text) > 4000000 then
    raise sqlstate 'PT400' using message = 'INVALID_KITCHEN';
  end if;
  update private.family_kitchens
    set state = new_state, revision = revision + 1, updated_at = now()
    where access_key_hash = key_hash and revision = expected_revision
    returning * into saved;
  if not found then
    raise sqlstate 'PT409' using message = 'SYNC_CONFLICT';
  end if;
  return pg_catalog.jsonb_build_object(
    'family_id', saved.id, 'revision', saved.revision, 'updated_at', saved.updated_at
  );
end;
$$;

revoke all on function public.read_family_kitchen(text, bigint) from public;
revoke all on function public.sync_family_kitchen(text, bigint, jsonb) from public;
grant execute on function public.read_family_kitchen(text, bigint) to anon, authenticated;
grant execute on function public.sync_family_kitchen(text, bigint, jsonb) to anon, authenticated;
commit;

-- Run in the Supabase SQL editor AFTER the migration, once for your family.
-- Copy the returned connection code privately; never commit it or put it in a chat.
-- This uses a fresh, cryptographically random 256-bit code. No human-chosen password.
with token as materialized (
  select encode(extensions.gen_random_bytes(32), 'hex') as code
), created as (
  insert into private.family_kitchens (name, access_key_hash)
  select '我的家', extensions.digest(code, 'sha256') from token
  where not exists (select 1 from private.family_kitchens)
  returning id, name
)
select created.id as family_id, created.name, token.code as family_connection_code
from created cross join token;
