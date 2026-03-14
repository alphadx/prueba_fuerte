"""
ERP Almacén de Barrio - Chile
Modelos de base de datos
"""
from datetime import datetime, timezone

from . import db


# ---------------------------------------------------------------------------
# Inventario
# ---------------------------------------------------------------------------

class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(255))
    productos = db.relationship("Producto", back_populates="categoria", lazy=True)

    def __repr__(self):
        return f"<Categoria {self.nombre}>"


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(255))
    precio_compra = db.Column(db.Float, nullable=False, default=0.0)
    precio_venta = db.Column(db.Float, nullable=False, default=0.0)
    stock_actual = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)
    unidad_medida = db.Column(db.String(30), default="unidad")
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    categoria = db.relationship("Categoria", back_populates="productos")
    movimientos = db.relationship("MovimientoInventario", back_populates="producto", lazy=True)
    detalle_ventas = db.relationship("DetalleVenta", back_populates="producto", lazy=True)

    @property
    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo

    def __repr__(self):
        return f"<Producto {self.codigo} - {self.nombre}>"


class MovimientoInventario(db.Model):
    __tablename__ = "movimientos_inventario"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # entrada / salida / ajuste
    cantidad = db.Column(db.Integer, nullable=False)
    cantidad_anterior = db.Column(db.Integer, nullable=False)
    cantidad_posterior = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255))
    fecha = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=True)

    producto = db.relationship("Producto", back_populates="movimientos")
    empleado = db.relationship("Empleado", back_populates="movimientos")

    def __repr__(self):
        return f"<Movimiento {self.tipo} {self.cantidad} - {self.producto_id}>"


# ---------------------------------------------------------------------------
# Personal
# ---------------------------------------------------------------------------

class Empleado(db.Model):
    __tablename__ = "empleados"

    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(12), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(150))
    sueldo_base = db.Column(db.Float, nullable=False, default=460000.0)  # Sueldo mínimo Chile 2024
    fecha_ingreso = db.Column(db.Date, nullable=False, default=datetime.today)
    activo = db.Column(db.Boolean, default=True)

    turnos = db.relationship("Turno", back_populates="empleado", lazy=True)
    ventas = db.relationship("Venta", back_populates="empleado", lazy=True)
    movimientos = db.relationship("MovimientoInventario", back_populates="empleado", lazy=True)
    pagos_sueldo = db.relationship("PagoSueldo", back_populates="empleado", lazy=True)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        return f"<Empleado {self.rut} - {self.nombre_completo}>"


class Turno(db.Model):
    __tablename__ = "turnos"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.Time, nullable=True)
    hora_salida = db.Column(db.Time, nullable=True)
    tipo = db.Column(db.String(30), default="normal")  # normal / extra / feriado
    observacion = db.Column(db.String(255))

    empleado = db.relationship("Empleado", back_populates="turnos")

    def __repr__(self):
        return f"<Turno {self.empleado_id} - {self.fecha}>"


class PagoSueldo(db.Model):
    __tablename__ = "pagos_sueldo"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    periodo = db.Column(db.String(7), nullable=False)  # YYYY-MM
    sueldo_base = db.Column(db.Float, nullable=False)
    horas_extra = db.Column(db.Integer, default=0)
    monto_horas_extra = db.Column(db.Float, default=0.0)
    descuento_afp = db.Column(db.Float, default=0.0)   # ~11.5% AFP
    descuento_salud = db.Column(db.Float, default=0.0)  # 7% salud
    sueldo_liquido = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(30), default="transferencia")
    estado = db.Column(db.String(20), default="pendiente")  # pendiente / pagado
    fecha_pago = db.Column(db.DateTime, nullable=True)

    empleado = db.relationship("Empleado", back_populates="pagos_sueldo")

    def __repr__(self):
        return f"<PagoSueldo {self.empleado_id} - {self.periodo}>"


# ---------------------------------------------------------------------------
# Ventas y Pagos
# ---------------------------------------------------------------------------

class Venta(db.Model):
    __tablename__ = "ventas"

    id = db.Column(db.Integer, primary_key=True)
    numero_boleta = db.Column(db.String(20), unique=True, nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    iva = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    metodo_pago = db.Column(db.String(30), nullable=False, default="efectivo")
    estado = db.Column(db.String(20), nullable=False, default="completada")
    # Para pagos electrónicos
    referencia_pago = db.Column(db.String(100), nullable=True)
    fecha = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notas = db.Column(db.String(255))

    empleado = db.relationship("Empleado", back_populates="ventas")
    detalles = db.relationship(
        "DetalleVenta", back_populates="venta", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Venta {self.numero_boleta} - ${self.total}>"


class DetalleVenta(db.Model):
    __tablename__ = "detalle_ventas"

    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    venta = db.relationship("Venta", back_populates="detalles")
    producto = db.relationship("Producto", back_populates="detalle_ventas")

    def __repr__(self):
        return f"<DetalleVenta venta={self.venta_id} prod={self.producto_id} x{self.cantidad}>"
