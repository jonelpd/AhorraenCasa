# Actualización automática de precios Amazon

AhorraEnCasa utiliza Amazon Creators API para consultar precios y disponibilidad del marketplace español.

## Secretos necesarios en GitHub

En **Settings → Secrets and variables → Actions** crea estos secretos:

- `AMAZON_CLIENT_ID`
- `AMAZON_CLIENT_SECRET`
- `AMAZON_PARTNER_TAG` = `jonelpd-21`

No publiques nunca el Client Secret en HTML, JavaScript, GitHub ni en el repositorio.

## Activación

Después de crear los secretos, ejecuta manualmente el workflow **Actualizar precios Amazon** una primera vez. Después se ejecutará diariamente.

El sitio no debe inventar ni mantener precios manuales: los datos publicados proceden de Amazon y llevan fecha/hora de actualización. Amazon exige que los precios y disponibilidad procedentes de la API se actualicen según sus reglas y que se muestre la exención correspondiente.
