# Task Manager API

API REST para gestión de listas de tareas desarrollada con FastAPI, diseñada con arquitectura limpia por capas.

## Descripción del Proyecto

Este proyecto implementa una API completa para la gestión de listas de tareas que permite:

### Funcionalidades Básicas
- ✅ CRUD de listas de tareas
- ✅ CRUD de tareas dentro de una lista
- ✅ Cambio de estado de tareas
- ✅ Listado de tareas con filtros por estado/prioridad y porcentaje de completitud

### Funcionalidades Bonus
- ✅ Autenticación JWT
- ✅ Asignación de usuarios a tareas
- ✅ Simulación de notificaciones por email

## Arquitectura

El proyecto sigue una arquitectura limpia por capas:

```
src/
├── domain/          # Entidades y reglas de negocio
├── application/     # Casos de uso y servicios
├── infrastructure/  # Implementaciones concretas (DB, APIs externas)
└── presentation/    # Controllers y endpoints FastAPI
```

## Tecnologías Utilizadas

- **Python 3.11+**
- **FastAPI** - Framework web moderno
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos principal
- **Pydantic** - Validación y serialización de datos
- **JWT** - Autenticación
- **pytest** - Testing
- **Docker** - Containerización

## Configuración del Entorno Local

### Prerrequisitos
- Python 3.11+
- Docker y Docker Compose
- Git

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd task-manager-api
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Ejecutar migraciones**
```bash
alembic upgrade head
```

6. **Ejecutar la aplicación**
```bash
uvicorn src.main:app --reload
```

La API estará disponible en: `http://localhost:8000`
Documentación interactiva: `http://localhost:8000/docs`

## Ejecución con Docker

### Opción 1: Docker Compose (Recomendado)
```bash
docker-compose up -d
```

### Opción 2: Docker manual
```bash
# Construir imagen
docker build -t task-manager-api .

# Ejecutar contenedor
docker run -p 8000:8000 --env-file .env task-manager-api
```

## Ejecutar Pruebas

### Todas las pruebas
```bash
pytest
```

### Con cobertura
```bash
pytest --cov=src --cov-report=html
```

### Solo pruebas unitarias
```bash
pytest tests/unit/
```

### Solo pruebas de integración
```bash
pytest tests/integration/
```

## Linting y Formateo

### Ejecutar linter
```bash
flake8 src/
```

### Formatear código
```bash
black src/
isort src/
```

### Ejecutar todos los checks
```bash
make lint  # Si tienes Makefile configurado
```

## Endpoints Principales

### Autenticación
- `POST /auth/register` - Registro de usuario
- `POST /auth/login` - Login y obtención de token

### Listas de Tareas
- `GET /task-lists/` - Obtener todas las listas
- `POST /task-lists/` - Crear nueva lista
- `GET /task-lists/{id}` - Obtener lista específica
- `PUT /task-lists/{id}` - Actualizar lista
- `DELETE /task-lists/{id}` - Eliminar lista

### Tareas
- `GET /task-lists/{list_id}/tasks/` - Obtener tareas de una lista
- `POST /task-lists/{list_id}/tasks/` - Crear nueva tarea
- `PUT /tasks/{id}` - Actualizar tarea
- `PATCH /tasks/{id}/status` - Cambiar estado de tarea
- `DELETE /tasks/{id}` - Eliminar tarea

## Estructura de Datos

### Lista de Tareas
```json
{
  "id": 1,
  "name": "Mi Lista",
  "description": "Descripción de la lista",
  "owner_id": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "completion_percentage": 75.0
}
```

### Tarea
```json
{
  "id": 1,
  "title": "Mi Tarea",
  "description": "Descripción de la tarea",
  "status": "pending",
  "priority": "high",
  "assigned_to": 2,
  "task_list_id": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "due_date": "2024-01-02T00:00:00Z"
}
```

## Variables de Entorno

```env
# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/taskmanager

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (simulación)
EMAIL_ENABLED=true
SMTP_SERVER=localhost
SMTP_PORT=587
```

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. 