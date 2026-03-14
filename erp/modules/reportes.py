"""Módulo de Reportes."""
from datetime import datetime, timezone

from flask import Blueprint, render_template, request

from .. import db
from ..models import Venta, Producto, Empleado, PagoSueldo

reportes_bp = Blueprint("reportes", __name__)


@reportes_bp.route("/")
def index():
    return render_template("reportes/index.html")


@reportes_bp.route("/ventas")
def reporte_ventas():
    mes = request.args.get("mes", datetime.now(timezone.utc).strftime("%Y-%m"))
    try:
        inicio = datetime.strptime(mes, "%Y-%m").replace(tzinfo=timezone.utc)
        # Último día del mes
        if inicio.month == 12:
            fin = inicio.replace(year=inicio.year + 1, month=1, day=1)
        else:
            fin = inicio.replace(month=inicio.month + 1, day=1)
    except ValueError:
        inicio = datetime.now(timezone.utc).replace(day=1)
        fin = inicio.replace(month=inicio.month + 1) if inicio.month < 12 else inicio.replace(year=inicio.year + 1, month=1, day=1)

    ventas = Venta.query.filter(
        Venta.fecha >= inicio, Venta.fecha < fin
    ).order_by(Venta.fecha).all()

    total = sum(v.total for v in ventas)
    total_iva = sum(v.iva for v in ventas)

    # Ventas por método de pago
    por_metodo: dict = {}
    for v in ventas:
        por_metodo[v.metodo_pago] = por_metodo.get(v.metodo_pago, 0) + v.total

    return render_template(
        "reportes/ventas.html",
        ventas=ventas,
        total=total,
        total_iva=total_iva,
        por_metodo=por_metodo,
        mes=mes,
    )


@reportes_bp.route("/inventario")
def reporte_inventario():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    bajo_stock = [p for p in productos if p.stock_bajo]
    valor_inventario = sum(p.precio_compra * p.stock_actual for p in productos)

    return render_template(
        "reportes/inventario.html",
        productos=productos,
        bajo_stock=bajo_stock,
        valor_inventario=valor_inventario,
    )


@reportes_bp.route("/personal")
def reporte_personal():
    mes = request.args.get("mes", datetime.now(timezone.utc).strftime("%Y-%m"))
    pagos = PagoSueldo.query.filter_by(periodo=mes).all()
    total_sueldos = sum(p.sueldo_liquido for p in pagos)
    empleados = Empleado.query.filter_by(activo=True).all()

    return render_template(
        "reportes/personal.html",
        pagos=pagos,
        total_sueldos=total_sueldos,
        empleados=empleados,
        mes=mes,
    )
