-- Esquema inicial de usuarios de AhorraEnCasaYa
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role text not null default 'user' check (role in ('user','premium','admin')),
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- El cliente público no debe poder leer perfiles ajenos ni modificar su propio rol.
revoke all on public.profiles from anon;
revoke insert, update, delete on public.profiles from authenticated;
grant select on public.profiles to authenticated;

drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile"
on public.profiles
for select
to authenticated
using (auth.uid() = id);

-- El perfil se crea automáticamente al registrarse.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', ''));
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- El rol admin se asigna exclusivamente desde el SQL Editor de Supabase.
-- Ejemplo:
-- update public.profiles
-- set role = 'admin'
-- where id = (select id from auth.users where email = 'TU_EMAIL');

