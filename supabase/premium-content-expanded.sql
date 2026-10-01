-- Contenido Premium inicial ampliado
insert into public.premium_content (slug,title,excerpt,body,published)
values
('diagnostico-premium','Diagnóstico Premium: dónde empezar a ahorrar','Un método para decidir qué cambios merece la pena probar primero, sin comprar nada innecesario.',
'1. Mide antes de cambiar: registra consumo, hábitos y horarios durante varios días.

2. Prioriza por impacto: empieza por los equipos con muchas horas de uso o alta potencia.

3. Separa ahorro estimado de ahorro real: una calculadora orienta; tu factura y tus registros confirman.

4. Haz un cambio cada vez: así podrás saber qué medida produjo el resultado.

5. Revisa cada 30 días: conserva las medidas que funcionan y descarta las que no aportan un ahorro apreciable.

Objetivo Premium: convertir pequeñas mejoras repetibles en un sistema de ahorro sostenible.',
true),
('auditoria-factura','Auditoría Premium de tu factura eléctrica','Checklist para revisar potencia, consumo, periodos y hábitos antes de contratar o cambiar nada.',
'Checklist mensual:

□ Compara kWh con el mes anterior y con el mismo periodo del año anterior.

□ Comprueba si el aumento procede de más consumo o de un cambio de precio.

□ Revisa la potencia contratada frente a tus picos habituales.

□ Identifica los principales consumidores de tu vivienda.

□ Comprueba si las medidas de ahorro aplicadas están produciendo un cambio medible.

Importante: no cambies una tarifa o potencia únicamente por una estimación. Compara las condiciones concretas de tu contrato.',
true),
('electrodomesticos-prioridad','Qué electrodomésticos atacar primero','Una guía Premium para decidir dónde concentrar tiempo y presupuesto.',
'Prioridad 1: equipos de alta potencia usados muchas horas.

Prioridad 2: equipos que funcionan durante largos periodos aunque su potencia individual sea moderada.

Prioridad 3: consumos en espera cuando el número de dispositivos sea elevado.

Antes de comprar un aparato nuevo, compara el coste inicial con el ahorro anual razonablemente esperable. Una compra más eficiente no siempre recupera su diferencia de precio rápidamente.',
true),
('solar-premium','Guía Premium: cuándo estudiar la energía solar','Un marco sencillo para saber qué datos conviene reunir antes de pedir presupuestos.',
'Prepara estos datos:

• Consumo anual en kWh.
• Distribución aproximada del consumo durante el día.
• Superficie y orientación disponible.
• Posibles sombras.
• Tipo de vivienda y situación de la instalación.
• Presupuesto disponible y horizonte de permanencia.

Después compara varias propuestas con la misma base: potencia instalada, producción estimada, garantías, mantenimiento, compensación de excedentes y coste total.

No tomes una decisión solo por el número de paneles o por el ahorro anunciado.',
true),
('plan-90-dias','Plan Premium de 90 días','Un recorrido trimestral para pasar de la estimación a un ahorro medido.',
'Días 1–30: mide y registra. Identifica tus tres principales oportunidades.

Días 31–60: aplica dos o tres cambios de bajo coste y registra el efecto de cada uno.

Días 61–90: compara resultados, elimina medidas poco útiles y consolida las que sí funcionan.

Al terminar el trimestre, calcula tu ahorro mensual medio real y fija el siguiente objetivo. El sistema Premium está pensado para que puedas repetir este ciclo y mejorar progresivamente.',
true)
on conflict (slug) do update
set title=excluded.title,
    excerpt=excluded.excerpt,
    body=excluded.body,
    published=excluded.published,
    updated_at=now();
