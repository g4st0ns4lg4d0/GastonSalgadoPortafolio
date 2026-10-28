# Despliegue y mantenimiento

Procedimiento previsto para Linux. **No acredita un despliegue productivo.** La primera etapa se valida en desarrollo; PostgreSQL, dominio, TLS, SMTP y restauración se verificarán en la etapa 6 con infraestructura real.

## Configuración

Usar `config.settings.production` en el servidor. Mantener secretos en un archivo o servicio seguro accesible solo al usuario de la aplicación, nunca en Git. Las variables del proceso tienen prioridad sobre `.env`.

| Variable | Valor de producción |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_SECRET_KEY` | Clave aleatoria exclusiva, sin reutilizar el ejemplo local |
| `DJANGO_ALLOWED_HOSTS` | Hosts exactos separados por comas, nunca `*` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes HTTPS autorizados separados por comas |
| `SITE_URL` | URL canónica HTTPS; el dominio no se presupone adquirido |
| `DATABASE_URL` | Conexión PostgreSQL del usuario de aplicación |
| `PRIVATE_MEDIA_ROOT` | Directorio privado persistente absoluto |
| `STATIC_ROOT` | Directorio de estáticos recolectados absoluto |
| `DJANGO_TRUST_PROXY` | `True` solo con un proxy de confianza que reemplace `X-Forwarded-Proto` |

La producción deshabilita depuración. El envío SMTP se añadirá junto con el módulo de contacto. El modo de desarrollo usa `var/db.sqlite3`, `var/private-media` y `var/static` si no se personalizan las rutas.

## Instalación

1. Crear usuario de sistema sin privilegios administrativos.
2. Instalar Python compatible, PostgreSQL y Nginx desde fuentes oficiales.
3. Crear base PostgreSQL y usuario específico con permisos para migrar; no usar el superusuario PostgreSQL.
4. Separar código, estáticos, archivos privados y respaldos, con permisos mínimos.
5. Configurar secretos, DNS y TLS por los mecanismos seguros del servidor.

Con variables ya cargadas, desde la raíz del checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_initial_data
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy
.venv/bin/python manage.py createsuperuser
```

Crear la cuenta solo al instalar. No guardar contraseñas en scripts. Respaldar y comprobar recuperabilidad antes de migrar una instalación existente.

## Gunicorn y Nginx

Supervisar Gunicorn como servicio con usuario, entorno virtual y directorio correctos. Punto de partida para una máquina pequeña, a ajustar tras medir memoria y carga:

```bash
.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8001 --workers 2 --access-logfile - --error-logfile -
```

Solo Nginx debe alcanzar Gunicorn. Configurar reinicio y arranque con el sistema y suministrar secretos por un mecanismo seguro, sin argumentos visibles del proceso.

Ejemplo Nginx; adaptar rutas y dominio y configurar emisión y renovación del certificado:

```nginx
server {
    listen 443 ssl;
    server_name gastonsalgado.cl;
    ssl_certificate /etc/letsencrypt/live/gastonsalgado.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gastonsalgado.cl/privkey.pem;
    client_max_body_size 12m;

    location /static/ {
        alias /srv/gaston/staticfiles/;
        expires 7d;
        add_header X-Content-Type-Options nosniff always;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name gastonsalgado.cl;
    return 301 https://$host$request_uri;
}
```

El alias debe coincidir con `STATIC_ROOT`. **No crear un alias público para archivos privados ni `/media/`.** Django atiende `/archivos/<uuid>/` y comprueba publicación en cada petición.

Para el ejemplo Nginx, configurar `DJANGO_TRUST_PROXY=True` de modo que Django reconozca el HTTPS terminado por ese proxy y no entre en un bucle de redirecciones. Solo el proxy autorizado debe alcanzar Gunicorn y debe sobrescribir `X-Forwarded-Proto`. No activar esta confianza si los clientes pueden llegar directamente a Gunicorn. Comprobar cookies seguras y redirección HTTPS. Revisar HSTS antes de aplicar políticas estrictas a subdominios. Validar la configuración Nginx antes de recargarla.

## Comprobaciones

- Resolver las advertencias aplicables de `check --deploy`.
- Confirmar migraciones PostgreSQL, estáticos, login Admin y CSRF a través de HTTPS.
- Probar que un archivo privado no se entrega y uno público sí, con cabeceras correctas.
- Revisar los datos y enlaces de la portada.
- Restaurar un respaldo en una instalación separada.
- Evitar secretos, cookies o datos privados en los registros de errores.

## Respaldos y restauración

Respaldar base y archivos privados, conservando versión del código y migraciones. Los secretos requieren un almacén seguro independiente. Para PostgreSQL, utilizar autenticación segura sin contraseñas en argumentos:

```bash
pg_dump --format=custom --file=/ruta/segura/portfolio.dump nombre_base
```

Para SQLite de desarrollo, detener escrituras o usar una copia consistente con la API oficial:

```python
import sqlite3

with sqlite3.connect("var/db.sqlite3") as source:
    with sqlite3.connect("/ruta/segura/portfolio.sqlite3") as destination:
        source.backup(destination)
```

Copiar también `PRIVATE_MEDIA_ROOT` a almacenamiento protegido, con política de cifrado, acceso y retención. No publicar respaldos bajo el directorio de estáticos.

Probar restauración fuera de producción: crear base vacía, recuperar con `pg_restore`, restaurar archivos a un directorio separado y verificar referencias y permisos. Un archivo de respaldo creado no demuestra recuperabilidad.

## Mantenimiento

- Actualizar dependencias de seguridad, ejecutar pruebas y revisar migraciones antes de desplegar.
- Revisar cuentas administrativas y documentos públicos periódicamente.
- Rotar credenciales y mantenerlas fuera de Git.
- Supervisar errores, disco, TLS y tareas de respaldo.
- Conservar código y respaldo compatibles para recuperar una actualización.
- En la etapa de contacto, establecer retención de mensajes y aviso de privacidad.
