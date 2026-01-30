# LogincoSeguimientoV2

Sistema de seguimiento y gestión de embarques para operaciones logísticas, desarrollado con Django 6.0.

## 📋 Descripción

LogincoSeguimientoV2 es una aplicación web completa para el seguimiento de embarques a través de múltiples etapas del proceso logístico. El sistema permite gestionar clientes, embarques, trackings y generar analíticas en tiempo real. Incluye funcionalidades de personalización por cliente, dashboards personalizados y sistema de notificaciones.

## 🚀 Características Principales

- **Gestión de Embarques**: CRUD completo con timeline visual de progreso
- **Seguimiento por Etapas**: Sistema configurable de steps con estados (pendiente, en proceso, completado)
- **Personalización por Cliente**: Cada cliente puede tener su propio flujo de proceso
- **Dashboards Interactivos**: 
  - Dashboard general con estadísticas globales
  - Dashboard personal con embarques asignados al usuario
  - Analytics con gráficas y métricas
- **Sistema de Revisiones**: Historial de auditoría con comentarios y archivos adjuntos
- **Autenticación JWT**: Sistema de autenticación seguro
- **Notificaciones**: Sistema de notificaciones en tiempo real (en desarrollo)

## 🛠️ Stack Tecnológico

### Backend
- **Framework**: Django 6.0
- **API REST**: Django REST Framework 3.16.1
- **Base de Datos**: SQLite3 (desarrollo) / PostgreSQL (producción)
- **Autenticación**: Custom User model + JWT (djangorestframework_simplejwt 5.5.1)
- **Tareas Asíncronas**: Celery 5.6.2 con Redis
- **WebSockets**: Django Channels 4.3.2

### Frontend
- **CSS Framework**: Tailwind CSS (django-tailwind 4.4.2)
- **Gráficas**: Chart.js
- **Interactividad**: JavaScript vanilla + AJAX

### Infraestructura
- **Servidor**: Gunicorn 23.0.0
- **Archivos Estáticos**: WhiteNoise 6.11.0
- **Almacenamiento**: Django Storages 1.14.6 (AWS S3 compatible)
- **Email**: SendGrid 6.12.5

## 📦 Instalación

### Prerrequisitos

- Python 3.11+
- Redis (para Celery)
- Virtual environment

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone git@github.com:xoyoc/SeguimientoLogincoV2.git
   cd LogincoSeguimientoV2
   ```

2. **Crear y activar entorno virtual**
   ```bash
   python -m venv .venvLogincoSeguimiento
   source .venvLogincoSeguimiento/bin/activate  # En Windows: .venvLogincoSeguimiento\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   
   Crear archivo `.env` en la raíz del proyecto:
   ```env
   SECRET_KEY=tu_secret_key_aqui
   SENDGRID_API_KEY=tu_sendgrid_api_key
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

5. **Ejecutar migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Cargar datos iniciales (fixtures)**
   ```bash
   python manage.py loaddata django_fixtures/users_fixture.json
   python manage.py loaddata django_fixtures/clients_fixture.json
   python manage.py loaddata django_fixtures/terminals_fixture.json
   python manage.py loaddata django_fixtures/lines_fixture.json
   python manage.py loaddata django_fixtures/steps_fixture.json
   ```

7. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

8. **Iniciar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

9. **Iniciar Celery (en otra terminal)**
   ```bash
   celery -A seguimiento worker -l info
   celery -A seguimiento beat -l info
   ```

## 📁 Estructura del Proyecto

```
LogincoSeguimientoV2/
├── seguimiento/              # Configuración principal del proyecto
│   ├── settings.py          # Configuración de Django
│   ├── urls.py              # URLs principales
│   ├── views.py             # Vistas de dashboard y analytics
│   └── admin/               # Configuración personalizada del admin
├── users/                   # Gestión de usuarios (Custom User model)
├── shipments/               # Gestión de embarques
├── trackings/               # Sistema de tracking
├── revisions/               # Historial de revisiones
├── clients/                 # Gestión de clientes
├── terminals/               # Catálogo de terminales portuarias
├── lines/                   # Catálogo de líneas navieras
├── steps/                   # Definición de etapas del proceso
├── departments/             # Departamentos (opcional)
├── regimens/                # Regímenes aduanales
├── notifications/           # Sistema de notificaciones
├── templates/               # Templates globales
├── django_fixtures/         # Fixtures para carga de datos
├── db_exports/              # Utilidades de migración (no en Git)
├── manage.py
├── requirements.txt
└── README.md
```

## 🔑 Apps de Django

| App | Propósito |
|-----|-----------|
| `users` | Modelo de usuario personalizado extendiendo AbstractUser |
| `shipments` | Gestión central de embarques con vistas CRUD |
| `trackings` | Gestión de estados de seguimiento por etapas |
| `revisions` | Historial de auditoría y revisiones |
| `clients` | Gestión de clientes con configuración personalizada |
| `terminals` | Catálogo de terminales portuarias |
| `lines` | Catálogo de líneas navieras |
| `steps` | Definición de etapas del proceso (IMP/EXP) |
| `departments` | Gestión de departamentos |
| `regimens` | Regímenes aduanales |
| `notifications` | Sistema de notificaciones |

## 🌐 Rutas Principales

| URL | Descripción |
|-----|-------------|
| `/` | Dashboard general con estadísticas |
| `/mi-dashboard/` | Dashboard personal del usuario logueado |
| `/analytics/` | Vista de analytics con gráficas |
| `/shipments/` | CRUD de embarques |
| `/shipments/<id>/` | Detalle de embarque con timeline |
| `/trackings/` | CRUD de trackings |
| `/revisions/` | Gestión de revisiones |
| `/clients/` | Gestión de clientes (admin/staff) |
| `/clients/<id>/steps/` | Configuración de steps por cliente |
| `/login/` | Página de login |
| `/admin/` | Panel de administración Django |

## 🔐 Autenticación

El sistema utiliza un modelo de usuario personalizado (`users.User`) que extiende `AbstractUser` de Django. La autenticación se maneja mediante:

- **Session-based**: Para el panel de administración y vistas web
- **JWT**: Para API REST (djangorestframework_simplejwt)

## 📊 Modelos Principales

### Relaciones Clave

```
User ─────────────────────┐
  │                       │
  ↓                       ↓
Client ← Shipment ────→ User (assigned_to)
           │
           ├── Terminal (FK)
           ├── Line (FK)
           ↓
        Tracking ────────→ Step
           │
           ↓
        Revision ────────→ attachments (JSONField)
```

### Shipment
- Campo central del sistema
- Relaciones: User (assigned_to), Client, Terminal, Line
- Campos: número, contenedor, bl, fecha arribo, etc.

### Tracking
- Vincula Shipment con Step
- Estados: "not_started", "pending", "in_progress", "completed"
- Permite seguimiento del progreso

### Revision
- Historial de cambios y comentarios
- Archivos adjuntos en JSONField
- Vinculado a Tracking y User

## 🎨 Personalización por Cliente

Cada cliente puede tener su propio flujo de trabajo configurado mediante `ClientStep`:

1. Ir a `/clients/<id>/steps/`
2. Activar/desactivar steps según el proceso del cliente
3. Definir orden personalizado
4. El timeline del embarque mostrará solo los steps configurados

## 📈 Dashboard y Analytics

### Dashboard General (`/`)
- Total de embarques
- Embarques activos/completados
- Estadísticas por terminal
- Embarques por línea naviera

### Mi Dashboard (`/mi-dashboard/`)
- Solo embarques asignados al usuario logueado
- Quick comments vía modal
- Estadísticas personales

### Analytics (`/analytics/`)
- Gráficas interactivas (Chart.js)
- Métricas de rendimiento
- Análisis de tiempo por etapa

## 🔧 Comandos Útiles

```bash
# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Shell interactivo
python manage.py shell

# Crear superusuario
python manage.py createsuperuser

# Cargar fixtures
python manage.py loaddata django_fixtures/<fixture_name>.json

# Ejecutar tests
python manage.py test

# Recolectar archivos estáticos
python manage.py collectstatic

# Celery worker
celery -A seguimiento worker -l info

# Celery beat (tareas programadas)
celery -A seguimiento beat -l info
```

## 🌍 Configuración Regional

- **Idioma**: Español (es-mx)
- **Zona Horaria**: America/Mexico_City
- **Formato de Fecha**: Según localización mexicana

## 📧 Configuración de Email

### Desarrollo
Por defecto usa `console.EmailBackend` (muestra emails en consola)

### Producción
Configurar SendGrid en `.env`:
```env
SENDGRID_API_KEY=tu_api_key_aqui
```

Descomentar en `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

## 🔄 Migración desde MongoDB

El proyecto fue migrado desde MongoDB/Mongoose. Los scripts de migración están en `db_exports/`:

- `transform_to_django.py` - Convierte exports de MongoDB a fixtures de Django
- `mongoose_exports/` - Exports originales (excluidos de Git)

## 🚀 Deployment

### Producción con Gunicorn

```bash
gunicorn seguimiento.wsgi:application --bind 0.0.0.0:8000
```

### Variables de Entorno Requeridas

- `SECRET_KEY`: Clave secreta de Django
- `DEBUG`: False en producción
- `ALLOWED_HOSTS`: Dominio(s) permitido(s)
- `DATABASE_URL`: URL de PostgreSQL (si se usa)
- `CELERY_BROKER_URL`: URL de Redis
- `SENDGRID_API_KEY`: API key de SendGrid

## 📝 Licencia

Este proyecto es privado y propietario de Loginco.

## 👥 Contribución

Para contribuir al proyecto:

1. Crear una rama desde `main`
2. Hacer cambios y commit
3. Incluir co-autoría: `Co-Authored-By: Warp <agent@warp.dev>` en mensajes de commit
4. Push y crear Pull Request

## 📞 Soporte

Para soporte y consultas, contactar al equipo de desarrollo de Loginco.

---

**Nota**: Este README fue generado para el proyecto LogincoSeguimientoV2. Mantener actualizado conforme evolucione el proyecto.
