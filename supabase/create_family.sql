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
