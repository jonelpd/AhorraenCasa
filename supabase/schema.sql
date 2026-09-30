-- Esquema de usuarios y administración de AhorraEnCasaYa
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role text not null default 'user' check (role in ('user','premium','admin')),
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- El cliente público no debe poder leer perfiles ajenos ni modificar roles.
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

-- =========================================================
-- Administración protegida
-- Estas funciones comprueban el rol del usuario autenticado
-- dentro de la base de datos. No dependen de ocultar botones
-- ni de una clave secreta en el navegador.
-- =========================================================

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.profiles
    where id = auth.uid()
      and role = 'admin'
  );
$$;

revoke execute on function public.is_admin() from public, anon;
grant execute on function public.is_admin() to authenticated;

create or replace function public.admin_list_profiles()
returns table (
  id uuid,
  full_name text,
  role text,
  created_at timestamptz
)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if not public.is_admin() then
    raise exception 'Acceso restringido: se requiere rol admin';
  end if;

  return query
  select p.id, p.full_name, p.role, p.created_at
  from public.profiles p
  order by p.created_at desc;
end;
$$;

revoke execute on function public.admin_list_profiles() from public, anon;
grant execute on function public.admin_list_profiles() to authenticated;

create or replace function public.admin_set_role(
  target_user_id uuid,
  new_role text
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not public.is_admin() then
    raise exception 'Acceso restringido: se requiere rol admin';
  end if;

  if new_role not in ('user', 'premium', 'admin') then
    raise exception 'Rol no válido';
  end if;

  update public.profiles
  set role = new_role
  where id = target_user_id;

  return found;
end;
$$;

revoke execute on function public.admin_set_role(uuid, text) from public, anon;
grant execute on function public.admin_set_role(uuid, text) to authenticated;

-- El primer administrador se asigna exclusivamente desde SQL Editor:
-- update public.profiles
-- set role = 'admin'
-- where id = (
--   select id from auth.users where email = 'TU_EMAIL'
-- );
