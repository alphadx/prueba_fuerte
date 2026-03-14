"""Módulo de Ventas y Pagos automáticos."""
import uuid
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from .. import db
from ..models import Venta, DetalleVenta, Producto, Empleado, MovimientoInventario

ventas_bp = Blueprint("ventas", __name__)

IVA_RATE = 0.19
METODOS_PAGO = ["efectivo", "debito", "credito", "transferencia", "mercadopago"]


def _generar_numero_boleta() -> str:
    """Genera un número de boleta único con prefijo chileno."""
    ultimo = Venta.query.order_by(Venta.id.desc()).first()
    siguiente = (ultimo.id + 1) if ultimo else 1
    return f"B{siguiente:06d}"


def _procesar_pago(metodo: str, monto: float, referencia: str | None = None) -> dict:
    """
    Simula el procesamiento de un pago automático.

    En producción se integraría con:
    - Transbank WebPay (débito/crédito en Chile)
    - MercadoPago API
    - Transferencia bancaria (validación manual)

    Retorna dict con estado y referencia.
    """
    if metodo == "efectivo":
        return {"estado": "aprobado", "referencia": f"EFE-{uuid.uuid4().hex[:8].upper()}"}
    elif metodo in ("debito", "credito"):
        # Integración Transbank WebPay (simulada)
        return {"estado": "aprobado", "referencia": f"TBK-{uuid.uuid4().hex[:10].upper()}"}
    elif metodo == "mercadopago":
        return {"estado": "aprobado", "referencia": f"MP-{uuid.uuid4().hex[:10].upper()}"}
    elif metodo == "transferencia":
        ref = referencia or f"TRF-{uuid.uuid4().hex[:8].upper()}"
        return {"estado": "aprobado", "referencia": ref}
    return {"estado": "rechazado", "referencia": None}


# ---------------------------------------------------------------------------
# POS (Punto de Venta)
# ---------------------------------------------------------------------------

@ventas_bp.route("/pos")
def pos():
    empleados = Empleado.query.filter_by(activo=True).order_by(Empleado.nombre).all()
    return render_template("ventas/pos.html", empleados=empleados, metodos_pago=METODOS_PAGO)


@ventas_bp.route("/pos/procesar", methods=["POST"])
def procesar_venta():
    """Procesa una venta completa desde el POS."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos inválidos"}), 400

    items = data.get("items", [])
    metodo_pago = data.get("metodo_pago", "efectivo")
    empleado_id = data.get("empleado_id")
    referencia_externa = data.get("referencia")

    if not items:
        return jsonify({"error": "El carrito está vacío"}), 400

    if metodo_pago not in METODOS_PAGO:
        return jsonify({"error": "Método de pago no válido"}), 400

    # Verificar stock y calcular totales
    subtotal = 0.0
    detalles_preparados = []

    for item in items:
        producto = Producto.query.get(item.get("producto_id"))
        if not producto or not producto.activo:
            return jsonify({"error": f"Producto ID {item.get('producto_id')} no encontrado"}), 400

        cantidad = int(item.get("cantidad", 1))
        if cantidad <= 0:
            return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400

        if producto.stock_actual < cantidad:
            return jsonify({
                "error": f"Stock insuficiente para '{producto.nombre}'. "
                         f"Disponible: {producto.stock_actual}"
            }), 400

        precio = producto.precio_venta
        sub = precio * cantidad
        subtotal += sub
        detalles_preparados.append((producto, cantidad, precio, sub))

    # Calcular IVA (precios incluyen IVA en Chile para consumidores finales)
    iva = round(subtotal * IVA_RATE / (1 + IVA_RATE), 0)
    total = round(subtotal, 0)

    # Procesar pago automático
    resultado_pago = _procesar_pago(metodo_pago, total, referencia_externa)
    if resultado_pago["estado"] != "aprobado":
        return jsonify({"error": "Pago rechazado. Intente nuevamente."}), 402

    # Crear la venta
    numero_boleta = _generar_numero_boleta()
    venta = Venta(
        numero_boleta=numero_boleta,
        empleado_id=int(empleado_id) if empleado_id else None,
        subtotal=subtotal - iva,
        iva=iva,
        total=total,
        metodo_pago=metodo_pago,
        estado="completada",
        referencia_pago=resultado_pago["referencia"],
    )
    db.session.add(venta)
    db.session.flush()

    # Agregar detalles y descontar stock
    for producto, cantidad, precio, sub in detalles_preparados:
        detalle = DetalleVenta(
            venta_id=venta.id,
            producto_id=producto.id,
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=sub,
        )
        db.session.add(detalle)

        # Movimiento de inventario automático
        ant = producto.stock_actual
        producto.stock_actual -= cantidad
        mov = MovimientoInventario(
            producto_id=producto.id,
            tipo="salida",
            cantidad=cantidad,
            cantidad_anterior=ant,
            cantidad_posterior=producto.stock_actual,
            motivo=f"Venta {numero_boleta}",
        )
        db.session.add(mov)

    db.session.commit()

    return jsonify({
        "estado": "ok",
        "numero_boleta": numero_boleta,
        "total": total,
        "iva": iva,
        "referencia_pago": resultado_pago["referencia"],
        "metodo_pago": metodo_pago,
    })


# ---------------------------------------------------------------------------
# Historial de ventas
# ---------------------------------------------------------------------------

@ventas_bp.route("/")
def lista_ventas():
    fecha_desde = request.args.get("desde")
    fecha_hasta = request.args.get("hasta")
    metodo = request.args.get("metodo")

    query = Venta.query

    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.filter(Venta.fecha >= d)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            h = datetime.strptime(fecha_hasta, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
            query = query.filter(Venta.fecha <= h)
        except ValueError:
            pass

    if metodo:
        query = query.filter_by(metodo_pago=metodo)

    ventas = query.order_by(Venta.fecha.desc()).limit(200).all()
    total_filtrado = sum(v.total for v in ventas)

    return render_template(
        "ventas/lista.html",
        ventas=ventas,
        total_filtrado=total_filtrado,
        metodos_pago=METODOS_PAGO,
        filtros={"desde": fecha_desde, "hasta": fecha_hasta, "metodo": metodo},
    )


@ventas_bp.route("/pos/boleta_redirect")
def boleta_redirect():
    """Redirige a la boleta por número de boleta (usado desde el POS)."""
    numero = request.args.get("boleta", "").strip()
    if not numero:
        return redirect(url_for("ventas.lista_ventas"))
    venta = Venta.query.filter_by(numero_boleta=numero).first_or_404()
    return redirect(url_for("ventas.boleta", venta_id=venta.id))


@ventas_bp.route("/<int:venta_id>")
def detalle_venta(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    return render_template("ventas/detalle.html", venta=venta)


@ventas_bp.route("/<int:venta_id>/boleta")
def boleta(venta_id):
    """Imprime una boleta de venta."""
    venta = Venta.query.get_or_404(venta_id)
    return render_template("ventas/boleta.html", venta=venta)
