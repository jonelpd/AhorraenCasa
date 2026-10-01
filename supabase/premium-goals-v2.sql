-- AhorraEnCasaYa - CORRECCIÓN RLS DE OBJETIVOS PREMIUM
-- Ejecutar una sola vez en Supabase SQL Editor.
-- No elimina los objetivos existentes; solo corrige quién puede acceder.

alter table public.premium_goals enable row level security;

drop policy if exists "Users can read own premium goal" on public.premium_goals;
drop policy if exists "Users can insert own premium goal" on public.premium_goals;
drop policy if exists "Users can update own premium goal" on public.premium_goals;
drop policy if exists "Users can delete own premium goal" on public.premium_goals;
drop policy if exists "Premium users can read own premium goal" on public.premium_goals;
drop policy if exists "Premium users can insert own premium goal" on public.premium_goals;
drop policy if exists "Premium users can update own premium goal" on public.premium_goals;
drop policy if exists "Premium users can delete own premium goal" on public.premium_goals;

create policy "Premium users can read own premium goal"
on public.premium_goals for select to authenticated
using (
  user_id = auth.uid()
  and exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role in ('premium','admin')
  )
);

create policy "Premium users can insert own premium goal"
on public.premium_goals for insert to authenticated
with check (
  user_id = auth.uid()
  and exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role in ('premium','admin')
  )
);

create policy "Premium users can update own premium goal"
on public.premium_goals for update to authenticated
using (
  user_id = auth.uid()
  and exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role in ('premium','admin')
  )
)
with check (
  user_id = auth.uid()
  and exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role in ('premium','admin')
  )
);

create policy "Premium users can delete own premium goal"
on public.premium_goals for delete to authenticated
using (
  user_id = auth.uid()
  and exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role in ('premium','admin')
  )
);

create index if not exists idx_premium_goals_user_id
on public.premium_goals(user_id);