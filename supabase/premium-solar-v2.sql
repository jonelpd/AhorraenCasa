-- AHORRAENCASAYA - SIMULADOR SOLAR PREMIUM V2
-- Amplía la tabla existente sin borrar análisis anteriores.

alter table public.solar_analyses
  add column if not exists orientation text not null default 'sur',
  add column if not exists tilt_deg numeric(6,2) not null default 30,
  add column if not exists shade_loss_pct numeric(6,2) not null default 0,
  add column if not exists degradation_pct numeric(6,3) not null default 0.4,
  add column if not exists battery_capacity_kwh numeric(8,2) not null default 0,
  add column if not exists battery_efficiency_pct numeric(6,2) not null default 90,
  add column if not exists battery_cost numeric(12,2) not null default 0,
  add column if not exists annual_saving_no_battery numeric(12,2) not null default 0,
  add column if not exists annual_saving_with_battery numeric(12,2) not null default 0,
  add column if not exists cumulative_saving_10y numeric(12,2) not null default 0,
  add column if not exists cumulative_saving_20y numeric(12,2) not null default 0,
  add column if not exists recommendation text not null default '';

alter table public.solar_analyses
  drop constraint if exists solar_orientation_check,
  drop constraint if exists solar_tilt_check,
  drop constraint if exists solar_shade_check,
  drop constraint if exists solar_degradation_check,
  drop constraint if exists solar_battery_capacity_check,
  drop constraint if exists solar_battery_efficiency_check,
  drop constraint if exists solar_battery_cost_check;

alter table public.solar_analyses
  add constraint solar_orientation_check
    check (orientation in ('sur','sureste','suroeste','este','oeste','norte')),
  add constraint solar_tilt_check
    check (tilt_deg between 0 and 90),
  add constraint solar_shade_check
    check (shade_loss_pct between 0 and 80),
  add constraint solar_degradation_check
    check (degradation_pct between 0 and 3),
  add constraint solar_battery_capacity_check
    check (battery_capacity_kwh >= 0),
  add constraint solar_battery_efficiency_check
    check (battery_efficiency_pct between 50 and 100),
  add constraint solar_battery_cost_check
    check (battery_cost >= 0);

-- Mantiene RLS y permisos de la versión anterior.
alter table public.solar_analyses enable row level security;
revoke all on table public.solar_analyses from anon;
revoke all on table public.solar_analyses from authenticated;
grant select, insert, update, delete on table public.solar_analyses to authenticated;
grant usage, select on sequence public.solar_analyses_id_seq to authenticated;

drop policy if exists "Premium users read own solar analyses" on public.solar_analyses;
create policy "Premium users read own solar analyses"
on public.solar_analyses for select to authenticated
using (
  user_id = auth.uid()
  and exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('premium','admin'))
);

drop policy if exists "Premium users insert own solar analyses" on public.solar_analyses;
create policy "Premium users insert own solar analyses"
on public.solar_analyses for insert to authenticated
with check (
  user_id = auth.uid()
  and exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('premium','admin'))
);

drop policy if exists "Premium users update own solar analyses" on public.solar_analyses;
create policy "Premium users update own solar analyses"
on public.solar_analyses for update to authenticated
using (
  user_id = auth.uid()
  and exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('premium','admin'))
)
with check (
  user_id = auth.uid()
  and exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('premium','admin'))
);

drop policy if exists "Premium users delete own solar analyses" on public.solar_analyses;
create policy "Premium users delete own solar analyses"
on public.solar_analyses for delete to authenticated
using (
  user_id = auth.uid()
  and exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('premium','admin'))
);

create index if not exists idx_solar_analyses_user_created
on public.solar_analyses(user_id, created_at desc);