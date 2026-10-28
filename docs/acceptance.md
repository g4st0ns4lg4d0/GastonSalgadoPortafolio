# Verificación por etapas

La entrega actual corresponde a la **etapa 1**. Los criterios posteriores son un plan, no evidencia de funciones terminadas. No avanzar sin ejecutar y verificar la etapa anterior.

## Etapa 1 — Base funcional

Desde la raíz, con el entorno virtual activado:

```bash
python manage.py migrate
python manage.py seed_initial_data
python manage.py seed_initial_data
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py runserver
```

La segunda importación no debe duplicar registros ni sobrescribir ediciones. Las pruebas utilizan una base independiente.

### Criterios funcionales

- La portada responde, muestra información de la base de datos y no necesita un proceso frontend externo.
- Admin exige autenticación y permite gestionar perfil, configuración, organizaciones, tecnologías, categorías y servicios.
- Una edición se refleja al recargar; orden y publicación controlan los servicios visibles.
- Los enlaces internos alcanzan su sección sin quedar bajo el encabezado fijo.
- Correo, LinkedIn y WhatsApp utilizan los datos del perfil. WhatsApp incluye mensaje precargado.
- El botón de CV aparece solo cuando hay un documento público autorizado.
- Un archivo privado no se obtiene desde la URL pública. Formatos y tamaños no permitidos se rechazan.
- Publicar exige revisar expresamente una copia apta para difusión; la carga no publica automáticamente el original.
- Los datos opcionales vacíos no rompen la página. No aparecen cursos, proyectos ni estadísticas ficticias.
- `/health/` solo indica disponibilidad básica, no certifica todas las funciones.

### Revisión visual y de accesibilidad

1. Probar anchos de 360, 768 y 1440 píxeles: sin desplazamiento horizontal, con textos legibles y tarjetas ordenadas.
2. Recorrer con teclado: salto al contenido, menú, controles y foco visible.
3. Abrir y cerrar menú móvil, incluyendo Escape, y comprobar su estado accesible.
4. Activar movimiento reducido y comprobar que se eliminan animaciones innecesarias.
5. Revisar contraste, legibilidad y texto alternativo de las fotografías publicadas.
6. Desactivar JavaScript: el contenido y los enlaces principales siguen disponibles.

Esta etapa no acredita formulario y entrega de correo, filtros de cursos, cronologías, blog, sitemap completo ni despliegue real.

### Evidencia de esta entrega — 28 de octubre de 2026

- Instalación desde `requirements.txt`, comprobación de dependencias, migraciones y dos o más ejecuciones de `seed_initial_data`: correctas.
- `check`: sin incidencias. `makemigrations --check --dry-run`: sin cambios pendientes.
- `manage.py test`: **30 pruebas ejecutadas y aprobadas** sobre una base aislada. Incluyen publicación y ocultamiento, edición Admin, CSRF, permisos de solo lectura, carga idempotente, archivos privados, revocación al reemplazar y validación/optimización de imágenes.
- Servidor real: portada, `/health/` y CSS respondieron HTTP 200. `/health/` devolvió `status: ok` con acceso a SQLite.
- Chromium: sin desbordamiento horizontal en 320, 390, 760, 768, 1024 y 1440 píxeles; menú operable con teclado, Escape y retorno del foco; movimiento reducido respetado; navegación disponible sin JavaScript; sin errores JavaScript observados.
- Capturas locales generadas en `var/screenshots/` (archivos de verificación no versionados).

Validado en Linux, Python 3.12 y SQLite. Las instrucciones Windows no se han ejecutado en una máquina Windows. No se ha desplegado en producción ni validado PostgreSQL, DNS, TLS o SMTP. El titular debe crear su cuenta con `createsuperuser`; no se ha generado una contraseña predeterminada.

## Etapa 2 — Currículum dinámico

Admin gestionará experiencia, títulos y credenciales independientes; la portada los ordenará correctamente; las fechas desconocidas seguirán vacías y los archivos privados estarán protegidos. Probar periodos inválidos, cargos vigentes y ausencia de acreditaciones públicas.

## Etapa 3 — Catálogo de relatorías

Probar relaciones entre cursos, instituciones, beneficiarios, recursos y fotografías, búsqueda, filtros combinados y carga progresiva. Los cursos programados o cancelados no se mostrarán como finalizados. Los indicadores solo usarán datos documentados.

## Etapa 4 — Contenido educativo

Verificar proyectos, recursos y artículos con administración, borradores, URLs individuales y publicación. Probar sanitización, exclusión de borradores y que galerías y descargas no eludan permisos.

## Etapa 5 — Contacto y posicionamiento

El formulario validará entradas, aplicará CSRF y antispam y guardará el mensaje aunque falle SMTP. Con SMTP disponible se verificará entrega real a la cuenta autorizada. Revisar privacidad, sitemap, robots, metadatos sociales, datos estructurados, canonical, teclado y rendimiento. No prometer posiciones en buscadores.

## Etapa 6 — Producción

Probar sobre PostgreSQL, ejecutar `check --deploy` con settings reales, desplegar detrás de Nginx con HTTPS, revisar estáticos, archivos y logs y restaurar un respaldo en un entorno separado. La documentación escrita o las pruebas con SQLite no acreditan despliegue ni restauración PostgreSQL.

Dominio, servidor y credenciales se proporcionarán por canales seguros. Definir responsable, periodicidad y evidencia de respaldos y restauraciones.
