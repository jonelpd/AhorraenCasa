# AhorraEnCasaYa — integración Stripe Premium

## Modelo comercial

- Premium mensual: **2,99 €/mes**
- Premium anual: **35,88 €/año**
- Moneda: EUR
- Tipo: suscripción recurrente
- Checkout: Stripe-hosted Checkout
- Gestión posterior: Stripe Customer Portal
- Fuente de verdad de acceso: `public.subscriptions` en Supabase.

## Arquitectura

`GitHub Pages → Supabase Edge Function → Stripe Checkout`

El navegador **nunca** recibe `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` ni `SUPABASE_SERVICE_ROLE_KEY`.

### Edge Functions

- `stripe-checkout`: valida al usuario Supabase y crea una Checkout Session.
- `stripe-portal`: crea el Customer Portal para el usuario autenticado.
- `stripe-webhook`: verifica la firma de Stripe y sincroniza la suscripción en Supabase.

## Variables privadas de Supabase

Configurar en el proyecto Supabase:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_MONTHLY_PRICE_ID`
- `STRIPE_ANNUAL_PRICE_ID`
- `SUPABASE_SERVICE_ROLE_KEY` (normalmente ya disponible en Edge Functions)
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

## Eventos Stripe

Registrar el endpoint:

`https://ntwavzropybpbpsltmag.supabase.co/functions/v1/stripe-webhook`

Eventos mínimos:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

Los eventos de suscripción son la referencia para activar, mantener o retirar el acceso Premium.

## Precios

Crear en Stripe un producto `AhorraEnCasaYa Premium` y dos Prices:

- recurring / month / 299 EUR cents
- recurring / year / 3588 EUR cents

Guardar los IDs en las variables privadas anteriores.

## Seguridad

- RLS continúa bloqueando escrituras del navegador sobre `subscriptions`.
- Las funciones validan el JWT de Supabase.
- El webhook exige firma válida y limita la antigüedad de la firma a 5 minutos.
- El frontend solo recibe URLs de Checkout/Portal.
- No guardar claves secretas en GitHub.

## Estado actual

La estructura de código está preparada, pero el despliegue de las Edge Functions, la creación de los Prices y la configuración del webhook deben hacerse en los servicios correspondientes antes de activar cobros reales.
