"""Módulo principal - Dashboard."""
from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    from .. import db
    from ..models import Producto, Venta, Empleado

    # Estadísticas rápidas
    total_productos = Producto.query.filter_by(activo=True).count()
    productos_bajo_stock = Producto.query.filter(
        Producto.activo == True,
        Producto.stock_actual <= Producto.stock_minimo
    ).count()

    total_empleados = Empleado.query.filter_by(activo=True).count()

    # Ventas del día
    hoy = datetime.now(timezone.utc).date()
    inicio_dia = datetime.combine(hoy, datetime.min.time()).replace(tzinfo=timezone.utc)
    ventas_hoy = Venta.query.filter(Venta.fecha >= inicio_dia).all()
    monto_hoy = sum(v.total for v in ventas_hoy)

    # Ventas del mes
    inicio_mes = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ventas_mes = Venta.query.filter(Venta.fecha >= inicio_mes).all()
    monto_mes = sum(v.total for v in ventas_mes)

    # Últimas 5 ventas
    ultimas_ventas = (
        Venta.query.order_by(Venta.fecha.desc()).limit(5).all()
    )

    return render_template(
        "index.html",
        total_productos=total_productos,
        productos_bajo_stock=productos_bajo_stock,
        total_empleados=total_empleados,
        ventas_hoy=len(ventas_hoy),
        monto_hoy=monto_hoy,
        ventas_mes=len(ventas_mes),
        monto_mes=monto_mes,
        ultimas_ventas=ultimas_ventas,
    )
