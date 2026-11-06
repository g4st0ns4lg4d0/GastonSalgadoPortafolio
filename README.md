# Plataforma profesional de Gastón Salgado

Sitio administrable con Django para Gastón Nicolás Salgado Jara. La portada reúne su presentación, servicios y accesos a su trayectoria y contenido educativo. La información profesional se mantiene en la base de datos y se edita desde Django Admin.

## Alcance de esta entrega

**Etapa 1: base funcional.** Incluye configuración por entorno, perfil y configuración general, organizaciones, tecnologías, categorías y servicios, administración privada, archivos con publicación explícita y portada responsive.

El catálogo de servicios representa áreas ofrecidas; **no acredita cursos impartidos**. No se crean cursos, proyectos, certificaciones ni estadísticas ficticias. Fotografía y currículum quedan vacíos hasta incorporar archivos reales revisados. Experiencia, formación, relatorías, proyectos, biblioteca, artículos y formulario de contacto se desarrollarán en las siguientes etapas, después de verificar esta base. Los botones de correo, LinkedIn y WhatsApp funcionan como enlaces.

Consultar [arquitectura y modelo de datos](docs/architecture.md), [criterios de aceptación](docs/acceptance.md) y [despliegue y respaldos](docs/deployment.md).

## Requisitos

- Python 3.12 o posterior compatible con Django 5.2 LTS y Git.
- SQLite para desarrollo, incluido con Python.
- PostgreSQL y un servidor Linux con Nginx para producción.

No se necesita Node.js ni compilación frontend. Las plantillas Django, CSS y JavaScript propios mantienen la página ligera y permiten un diseño a medida.

## Instalación en Windows

Desde la raíz del repositorio, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_initial_data
python manage.py createsuperuser
python manage.py runserver
```

Si PowerShell impide activar el entorno, usar su intérprete directamente, por ejemplo: `.\.venv\Scripts\python.exe manage.py runserver`.

Abrir la dirección local que indique `runserver`. El administrador está en `/admin/`. No existe una contraseña predeterminada: `createsuperuser` la solicita de forma interactiva.

## Instalación en Linux o macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_initial_data
python manage.py createsuperuser
python manage.py runserver
```

`seed_initial_data` incorpora la presentación y las áreas indicadas por el propietario. Es repetible y conserva registros existentes; no debe sobrescribir cambios editoriales. Los datos proceden de las instrucciones del proyecto: no se ha recibido ni importado un currículum o certificado adjunto.

## Configuración

Copiar `.env.example` a `.env` y mantener este último fuera de Git. `django-environ` lee el archivo sin reemplazar variables ya inyectadas en el proceso. La configuración predeterminada es `config.settings.development`.

- `SITE_URL` configura el dominio; no está fijado a `gastonsalgado.cl`.
- `DJANGO_DEBUG` es verdadero por defecto solo en desarrollo.
- SQLite se guarda en `var/db.sqlite3` si se omite `DATABASE_URL`.
- `PRIVATE_MEDIA_ROOT` usa `var/private-media` por defecto.
- `STATIC_ROOT` usa `var/static` por defecto.

Producción requiere `DJANGO_SETTINGS_MODULE=config.settings.production`, una clave propia, hosts explícitos, `SITE_URL` HTTPS y `DATABASE_URL` PostgreSQL. El servidor de desarrollo no debe utilizarse en producción.

## Administración

1. Crear la cuenta con `createsuperuser` e ingresar en `/admin/`.
2. Revisar perfil y configuración general.
3. Gestionar categorías, tecnologías, organizaciones y servicios. Su orden y publicación controlan la portada.
4. Subir únicamente archivos propios o autorizados. Revisar y preparar una copia pública sin información personal innecesaria antes de autorizar su acceso.
5. Asociar fotografía y currículum públicos al perfil cuando estén disponibles.

Las imágenes se ajustan a un máximo de 1600 píxeles por lado y se guardan sin metadatos EXIF/GPS. Eso no anonimiza lo que se ve dentro de una imagen o PDF: revisar siempre su contenido. Reemplazar un archivo publicado revoca su autorización y exige revisar la nueva versión antes de publicarla nuevamente.

## Verificación

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Iniciar también el servidor y seguir las comprobaciones manuales de [aceptación](docs/acceptance.md): edición desde Admin, navegación móvil y por teclado y permisos de archivos. `/health/` comprueba disponibilidad básica; no sustituye pruebas funcionales.

En el entorno en la nube, utilizar el checkout existente. No es necesario crear un worktree para ejecutar o desarrollar la aplicación.
