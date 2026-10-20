# Desplegar la interfaz oficial en Cloudflare

Web oficial: [AgroCebada · Explorar parcelas](https://agrocebada-2026.leonforce033.workers.dev/).

La interfaz usa React, TypeScript y Vite y se publica mediante Workers Static Assets. Cloudflare sirve la exportación estática; no ejecuta Python ni reentrena el modelo.

## Preparar y verificar

Desde la raíz, con Python 3.12 y Node.js 24:

```sh
python -m pip install -r requirements.txt
python -m agrocebada.cli verify
python scripts/export_react_dashboard.py
npm --prefix frontend ci
npm run dashboard:build
npm --prefix frontend run deploy:check
```

El exportador conserva las estimaciones e intervalos del modelo guardado y actualiza la trazabilidad de los archivos estáticos. El resultado publicable está en `frontend/dist/`. Los modelos, originales y documentos de auditoría no se publican como archivos de la web.

## Publicar

Autenticar Wrangler con la cuenta autorizada desde `frontend/` mediante `npx wrangler login`. Revisar la cuenta y el nombre del servicio configurado en `frontend/wrangler.jsonc` antes de ejecutar desde la raíz:

```sh
npm run dashboard:deploy
```

La cuenta se selecciona con la sesión de Wrangler. Esta rama no incluye tokens de acceso ni una cuenta fijada en su configuración. GitHub Actions valida la entrega, pero no publica automáticamente.

Conservar `frontend/public/_headers`: los contornos requieren `Content-Type: application/geo+json`. Las rutas usan fragmentos de URL y los archivos de datos ausentes deben devolver 404.

Después de publicar, comprobar el mapa, búsqueda de `71`, ficha de AGC_071, cambio de sensor, métricas y descargas. La vista actual no reproduce los videos archivados, aunque la compilación conserva los 16 clips.
