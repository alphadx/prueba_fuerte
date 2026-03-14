# prueba_fuerte — ERP Modular para Negocio de Barrio (Chile)

ERP construido íntegramente por Copilot. Backend asíncrono en Python/FastAPI con módulos para inventario, ventas, facturación electrónica SII, e-commerce con retiro en tienda, RRHH documental con alertas configurables y logística de despachos.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend API | Python 3.11 + FastAPI (async) |
| Base de datos | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Cache / colas | Redis 7 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Migraciones | Alembic |
| Contenedores | Docker + docker-compose |

---

## Módulos implementados

| # | Módulo | Entidades principales |
|---|---|---|
| 1 | **Core** | Company, Branch, Role, User, AuditLog |
| 2 | **Inventario** | Category, Product, StockItem, StockMovement |
| 3 | **Ventas / POS** | CashSession, Sale, SaleLine, Payment |
| 4 | **Facturación SII** | TaxDocument, TaxDocumentEvent |
| 5 | **E-commerce** | OnlineOrder, OrderLine, PickupSlot |
| 6 | **RRHH documental** | Employee, DocumentType, EmployeeDocument, DocumentAttachment |
| 7 | **Alertas** | AlarmRule, AlarmEvent, Notification |
| 8 | **Logística** | DeliveryTask (con links WhatsApp / Instagram) |

---

## Inicio rápido (Docker)

```bash
# 1. Clonar y configurar variables de entorno
cp backend/.env.example backend/.env
# Editar backend/.env y establecer SECRET_KEY fuerte

# 2. Levantar servicios
docker-compose up --build

# 3. La API estará disponible en http://localhost:8000
# Documentación interactiva: http://localhost:8000/docs
```

## Desarrollo local (sin Docker)

```bash
cd backend

# Instalar dependencias
pip install -r requirements.txt -r requirements-dev.txt

# Configurar .env
cp .env.example .env
# Editar DATABASE_URL y SECRET_KEY

# Ejecutar tests
pytest tests/ -v

# Levantar servidor de desarrollo
uvicorn app.main:app --reload
```

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py              # Entry point FastAPI
│   ├── core/                # Config, DB, seguridad JWT
│   ├── models/              # Modelos SQLAlchemy 2.0
│   ├── schemas/             # Schemas Pydantic v2
│   ├── routers/             # Endpoints REST por módulo
│   └── workers/             # Job diario de alertas
├── tests/                   # 19 tests con pytest-asyncio
├── alembic/                 # Migraciones de BD
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Endpoints principales

| Módulo | Prefijo | Descripción |
|---|---|---|
| Auth | `/auth` | Login, registro, perfil |
| Core | `/companies`, `/branches`, `/users` | Empresas y sucursales |
| Inventario | `/products`, `/stock`, `/categories` | Productos y stock |
| Ventas | `/sales`, `/cash-sessions` | POS y sesiones de caja |
| Facturación | `/tax-documents` | Boletas electrónicas SII |
| E-commerce | `/orders`, `/pickup-slots` | Pedidos online y ventanas de retiro |
| RRHH | `/employees`, `/document-types` | Empleados y documentos con campos dinámicos |
| Alertas | `/alarm-rules`, `/alarm-events`, `/notifications` | Vencimientos configurables |
| Logística | `/delivery-tasks` | Despachos con link WhatsApp/Instagram |

Documentación interactiva completa en `/docs` (Swagger UI) y `/redoc`.

---

## Medios de pago soportados (campo `method` en Payment)

- `cash` — efectivo (siempre habilitado)
- `transbank` — Webpay Plus
- `mercadopago` — Mercado Pago Chile
- `getnet` — Getnet
- `khipu` — Khipu
- `flow` — Flow
- `stripe` — Stripe (escalamiento global)
- `paypal` — PayPal (escalamiento global)

---

## Motor de alertas documentales

El worker `backend/app/workers/alerts.py` implementa un job asíncrono que:

1. Recorre todos los `EmployeeDocument` activos con fecha de vencimiento.
2. Para cada documento, evalúa las `AlarmRule` configuradas para su tipo.
3. Si `hoy >= fecha_fin − days_before` y no existe `AlarmEvent` previo para esa regla+documento, crea el evento.
4. Genera `Notification` para los usuarios con los roles destinatarios.

El job puede ejecutarse diariamente vía cron, Celery Beat o APScheduler.

---

## Documentos con atributos dinámicos (RRHH)

`DocumentType.fields_schema` define los campos personalizados en JSON:

```json
[
  {"name": "license_type", "type": "select", "options": ["A", "B", "C", "D"], "required": true},
  {"name": "restriction", "type": "text", "required": false},
  {"name": "photo_url", "type": "url", "required": false}
]
```

Tipos de campo soportados: `file`, `text`, `select`, `number`, `boolean`, `url`.

Esto permite crear plantillas de control distintas (licencia de conducir, permiso sanitario, contrato, revisión técnica, etc.) sin modificar código.

---

## Roadmap

- **Fase 1 (MVP)**: POS + inventario + boleta electrónica + e-commerce básico + RRHH con alertas ✅
- **Fase 2**: Panel logístico avanzado + más plantillas documentales + conciliación de pagos
- **Fase 3**: BI/reporting + automatizaciones + multi-sucursal extendido

