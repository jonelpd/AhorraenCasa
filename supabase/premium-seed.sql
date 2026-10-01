-- Primer contenido Premium de AhorraEnCasaYa
-- Ejecutar después de haber creado public.premium_content.

insert into public.premium_content (slug,title,excerpt,body,published)
values (
  'plan-ahorro-30-dias',
  'Plan Premium: 30 días para reducir tu factura',
  'Un recorrido práctico para detectar consumos, priorizar cambios y medir el ahorro real.',
  'Semana 1: registra tu consumo y localiza los aparatos que más utilizas.

Semana 2: aplica cambios de bajo coste y mide su impacto.

Semana 3: revisa horarios, potencia y hábitos de consumo.

Semana 4: compara el ahorro estimado con el ahorro real y decide qué medidas mantener.

Consejo Premium: no cambies muchas variables a la vez. Si mides cada cambio por separado, podrás identificar qué medidas realmente funcionan en tu vivienda.',
  true
)
on conflict (slug) do update
set title=excluded.title,
    excerpt=excluded.excerpt,
    body=excluded.body,
    published=excluded.published,
    updated_at=now();