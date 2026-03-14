"""Módulo de Personal (empleados, turnos y sueldos)."""
import re
from datetime import datetime, timezone, date

from flask import Blueprint, render_template, request, redirect, url_for, flash

from .. import db
from ..models import Empleado, Turno, PagoSueldo

personal_bp = Blueprint("personal", __name__)

# Tasas legales Chile (2024)
AFP_RATE = 0.115      # ~11.5% AFP (promedio)
SALUD_RATE = 0.07     # 7% salud (Fonasa/Isapre)
HORA_EXTRA_FACTOR = 1.5  # 50% recargo horas extra


def _validar_rut(rut: str) -> bool:
    """Valida un RUT chileno (formato: 12345678-9 o 12.345.678-9)."""
    rut = rut.replace(".", "").replace("-", "").strip().upper()
    if not re.match(r"^\d{7,8}[0-9K]$", rut):
        return False
    cuerpo, dv = rut[:-1], rut[-1]
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    resto = 11 - (suma % 11)
    if resto == 11:
        esperado = "0"
    elif resto == 10:
        esperado = "K"
    else:
        esperado = str(resto)
    return dv == esperado


def _calcular_sueldo_liquido(sueldo_base: float, horas_extra: int = 0) -> dict:
    """Calcula sueldo líquido con descuentos chilenos."""
    valor_hora = sueldo_base / 180  # ~180 horas mensuales
    monto_horas_extra = round(valor_hora * HORA_EXTRA_FACTOR * horas_extra, 0)
    sueldo_bruto = sueldo_base + monto_horas_extra

    descuento_afp = round(sueldo_bruto * AFP_RATE, 0)
    descuento_salud = round(sueldo_bruto * SALUD_RATE, 0)
    sueldo_liquido = sueldo_bruto - descuento_afp - descuento_salud

    return {
        "sueldo_base": sueldo_base,
        "horas_extra": horas_extra,
        "monto_horas_extra": monto_horas_extra,
        "sueldo_bruto": sueldo_bruto,
        "descuento_afp": descuento_afp,
        "descuento_salud": descuento_salud,
        "sueldo_liquido": sueldo_liquido,
    }


# ---------------------------------------------------------------------------
# Empleados
# ---------------------------------------------------------------------------

@personal_bp.route("/")
def lista_empleados():
    empleados = Empleado.query.filter_by(activo=True).order_by(Empleado.apellido).all()
    return render_template("personal/lista.html", empleados=empleados)


@personal_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo_empleado():
    if request.method == "POST":
        rut = request.form.get("rut", "").strip()
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        cargo = request.form.get("cargo", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip()
        sueldo_base = float(request.form.get("sueldo_base", 460000))
        fecha_ingreso_str = request.form.get("fecha_ingreso")

        if not all([rut, nombre, apellido, cargo]):
            flash("RUT, nombre, apellido y cargo son obligatorios.", "danger")
            return render_template("personal/form.html")

        if not _validar_rut(rut):
            flash(f"El RUT '{rut}' no es válido.", "danger")
            return render_template("personal/form.html")

        rut_normalizado = rut.replace(".", "").strip()
        if Empleado.query.filter_by(rut=rut_normalizado).first():
            flash(f"Ya existe un empleado con el RUT {rut}.", "danger")
            return render_template("personal/form.html")

        try:
            fecha_ingreso = (
                datetime.strptime(fecha_ingreso_str, "%Y-%m-%d").date()
                if fecha_ingreso_str else date.today()
            )
        except ValueError:
            fecha_ingreso = date.today()

        empleado = Empleado(
            rut=rut_normalizado,
            nombre=nombre,
            apellido=apellido,
            cargo=cargo,
            telefono=telefono,
            email=email,
            sueldo_base=sueldo_base,
            fecha_ingreso=fecha_ingreso,
        )
        db.session.add(empleado)
        db.session.commit()
        flash(f"Empleado '{empleado.nombre_completo}' registrado.", "success")
        return redirect(url_for("personal.lista_empleados"))

    return render_template("personal/form.html")


@personal_bp.route("/<int:empleado_id>/editar", methods=["GET", "POST"])
def editar_empleado(empleado_id):
    empleado = Empleado.query.get_or_404(empleado_id)

    if request.method == "POST":
        empleado.nombre = request.form.get("nombre", "").strip()
        empleado.apellido = request.form.get("apellido", "").strip()
        empleado.cargo = request.form.get("cargo", "").strip()
        empleado.telefono = request.form.get("telefono", "").strip()
        empleado.email = request.form.get("email", "").strip()
        empleado.sueldo_base = float(request.form.get("sueldo_base", empleado.sueldo_base))
        db.session.commit()
        flash(f"Empleado '{empleado.nombre_completo}' actualizado.", "success")
        return redirect(url_for("personal.lista_empleados"))

    return render_template("personal/form.html", empleado=empleado)


@personal_bp.route("/<int:empleado_id>/desactivar", methods=["POST"])
def desactivar_empleado(empleado_id):
    empleado = Empleado.query.get_or_404(empleado_id)
    empleado.activo = False
    db.session.commit()
    flash(f"Empleado '{empleado.nombre_completo}' desactivado.", "warning")
    return redirect(url_for("personal.lista_empleados"))


# ---------------------------------------------------------------------------
# Turnos
# ---------------------------------------------------------------------------

@personal_bp.route("/<int:empleado_id>/turnos")
def turnos_empleado(empleado_id):
    empleado = Empleado.query.get_or_404(empleado_id)
    turnos = (
        Turno.query.filter_by(empleado_id=empleado_id)
        .order_by(Turno.fecha.desc())
        .limit(60)
        .all()
    )
    return render_template("personal/turnos.html", empleado=empleado, turnos=turnos)


@personal_bp.route("/<int:empleado_id>/turnos/nuevo", methods=["POST"])
def nuevo_turno(empleado_id):
    empleado = Empleado.query.get_or_404(empleado_id)
    fecha_str = request.form.get("fecha")
    hora_entrada_str = request.form.get("hora_entrada")
    hora_salida_str = request.form.get("hora_salida")
    tipo = request.form.get("tipo", "normal")
    observacion = request.form.get("observacion", "").strip()

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        flash("Fecha inválida.", "danger")
        return redirect(url_for("personal.turnos_empleado", empleado_id=empleado_id))

    turno = Turno(
        empleado_id=empleado_id,
        fecha=fecha,
        hora_entrada=datetime.strptime(hora_entrada_str, "%H:%M").time() if hora_entrada_str else None,
        hora_salida=datetime.strptime(hora_salida_str, "%H:%M").time() if hora_salida_str else None,
        tipo=tipo,
        observacion=observacion,
    )
    db.session.add(turno)
    db.session.commit()
    flash("Turno registrado.", "success")
    return redirect(url_for("personal.turnos_empleado", empleado_id=empleado_id))


# ---------------------------------------------------------------------------
# Sueldos
# ---------------------------------------------------------------------------

@personal_bp.route("/sueldos")
def lista_sueldos():
    pagos = PagoSueldo.query.order_by(PagoSueldo.periodo.desc()).limit(100).all()
    empleados = Empleado.query.filter_by(activo=True).order_by(Empleado.apellido).all()
    return render_template("personal/sueldos.html", pagos=pagos, empleados=empleados)


@personal_bp.route("/sueldos/calcular", methods=["POST"])
def calcular_sueldo():
    empleado_id = int(request.form.get("empleado_id"))
    periodo = request.form.get("periodo")  # YYYY-MM
    horas_extra = int(request.form.get("horas_extra", 0))
    metodo_pago = request.form.get("metodo_pago", "transferencia")

    if not periodo or not re.match(r"^\d{4}-\d{2}$", periodo):
        flash("Período inválido (use YYYY-MM).", "danger")
        return redirect(url_for("personal.lista_sueldos"))

    empleado = Empleado.query.get_or_404(empleado_id)

    # Evitar duplicados
    existente = PagoSueldo.query.filter_by(
        empleado_id=empleado_id, periodo=periodo
    ).first()
    if existente:
        flash(f"Ya existe un pago para {empleado.nombre_completo} en {periodo}.", "warning")
        return redirect(url_for("personal.lista_sueldos"))

    calculo = _calcular_sueldo_liquido(empleado.sueldo_base, horas_extra)

    pago = PagoSueldo(
        empleado_id=empleado_id,
        periodo=periodo,
        sueldo_base=calculo["sueldo_base"],
        horas_extra=horas_extra,
        monto_horas_extra=calculo["monto_horas_extra"],
        descuento_afp=calculo["descuento_afp"],
        descuento_salud=calculo["descuento_salud"],
        sueldo_liquido=calculo["sueldo_liquido"],
        metodo_pago=metodo_pago,
        estado="pendiente",
    )
    db.session.add(pago)
    db.session.commit()
    flash(
        f"Sueldo calculado para {empleado.nombre_completo}: "
        f"${calculo['sueldo_liquido']:,.0f} líquido.",
        "success",
    )
    return redirect(url_for("personal.lista_sueldos"))


@personal_bp.route("/sueldos/<int:pago_id>/pagar", methods=["POST"])
def pagar_sueldo(pago_id):
    pago = PagoSueldo.query.get_or_404(pago_id)
    if pago.estado == "pagado":
        flash("Este sueldo ya fue pagado.", "warning")
    else:
        pago.estado = "pagado"
        pago.fecha_pago = datetime.now(timezone.utc)
        db.session.commit()
        flash(
            f"Sueldo de {pago.empleado.nombre_completo} ({pago.periodo}) "
            f"marcado como pagado.",
            "success",
        )
    return redirect(url_for("personal.lista_sueldos"))
