# Adquisición y recuperación

`signalclima.acquisition.Client` admite consultas HTTPS explícitas y conserva originales válidos por hash. Los límites acumulados son 4 GiB y 2,700 segundos de trabajo activo de adquisición, incluyendo esperas de reintento; máximo tres intentos por solicitud. El tiempo de edición, pruebas y entrenamiento no consume ese presupuesto. Catálogo, archivo descargado y admisión predictiva son estados distintos.

Los fallos deterministas y de autenticación no se repiten; fallos transitorios tienen espera progresiva. Un archivo existente sin recibo/hash compatible bloquea su reutilización. Las respuestas parciales se conservan como rechazadas y nunca se publican como originales admitidos. Se solicita transferencia sin compresión HTTP; si el servidor comprime igualmente, se registra ese hecho y no se confunde el Content-Length comprimido con el cuerpo decodificado. El presupuesto cuenta bytes de cuerpo recibidos por la aplicación y valida su formato; la longitud se comprueba cuando corresponde al mismo cuerpo. Rásteres requieren georreferencia y NoData comprobados; cada proveedor añade sus comprobaciones específicas. Las credenciales solo pueden enviarse en encabezados y no aparecen en manifiestos.

Desde la raíz del proyecto:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:PROJ_NETWORK='OFF'
.venv/Scripts/python.exe experiments/senal-clima-20261013/scripts/probe_public.py
```

Las consultas del catálogo usan un rectángulo regional generalizado, sin IDs ni rendimientos. Las pruebas locales cubren HTML en lugar de ráster, descarga truncada, límite de tiempo/bytes, alteración de caché y recuperación sin una solicitud adicional.
