-- OPTIONAL: revoke a leaked/lost family link without losing shopping or inventory data.
-- Replace ONLY the UUID below with your family's ID from the Supabase dashboard.
-- The new connection code is returned once. Share the new link with your family.
with token as materialized (
  select encode(extensions.gen_random_bytes(32), 'hex') as code
), changed as (
  update private.family_kitchens
    set access_key_hash = extensions.digest(token.code, 'sha256')
    from token
    where id = '00000000-0000-0000-0000-000000000000'::uuid
    returning private.family_kitchens.id
)
select changed.id as family_id, token.code as family_connection_code
from changed cross join token;
