-- Run in the Supabase SQL editor. No private holdings or provider secrets here.
create table if not exists public.quantforge_private_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  version bigint not null check (version > 0),
  payload jsonb not null check (jsonb_typeof(payload) = 'object'),
  updated_at timestamptz not null default now()
);

alter table public.quantforge_private_state enable row level security;
revoke all on public.quantforge_private_state from anon, authenticated;
grant select, insert, update on public.quantforge_private_state to authenticated;

drop policy if exists "owner_select" on public.quantforge_private_state;
create policy "owner_select" on public.quantforge_private_state
for select to authenticated using ((select auth.uid()) = user_id and (select auth.jwt()->>'aal') = 'aal2');

drop policy if exists "owner_insert" on public.quantforge_private_state;
create policy "owner_insert" on public.quantforge_private_state
for insert to authenticated with check ((select auth.uid()) = user_id and (select auth.jwt()->>'aal') = 'aal2');

drop policy if exists "owner_update" on public.quantforge_private_state;
create policy "owner_update" on public.quantforge_private_state
for update to authenticated using ((select auth.uid()) = user_id and (select auth.jwt()->>'aal') = 'aal2')
with check ((select auth.uid()) = user_id and (select auth.jwt()->>'aal') = 'aal2');

-- Disable self-registration in Supabase Auth > Providers > Email.
-- Create your one authorized user in Auth > Users, then use their UUID as OWNER_USER_ID.

-- Critical: the SQL editor executes as admin. After running, ensure the
-- authenticated role cannot read or write at AAL1; review policies in UI.
-- This preserves existing portfolio rows while upgrading authorization.
