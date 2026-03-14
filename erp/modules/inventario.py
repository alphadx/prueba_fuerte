"""Módulo de Inventario."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from .. import db
from ..models import Producto, Categoria, MovimientoInventario

inventario_bp = Blueprint("inventario", __name__)


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------

@inventario_bp.route("/")
def lista_productos():
    categoria_id = request.args.get("categoria_id", type=int)
    busqueda = request.args.get("q", "").strip()
    solo_bajo_stock = request.args.get("bajo_stock") == "1"

    query = Producto.query.filter_by(activo=True)

    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    if busqueda:
        query = query.filter(
            db.or_(
                Producto.nombre.ilike(f"%{busqueda}%"),
                Producto.codigo.ilike(f"%{busqueda}%"),
            )
        )
    if solo_bajo_stock:
        query = query.filter(Producto.stock_actual <= Producto.stock_minimo)

    productos = query.order_by(Producto.nombre).all()
    categorias = Categoria.query.order_by(Categoria.nombre).all()

    return render_template(
        "inventario/lista.html",
        productos=productos,
        categorias=categorias,
        categoria_id=categoria_id,
        busqueda=busqueda,
        solo_bajo_stock=solo_bajo_stock,
    )


@inventario_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo_producto():
    categorias = Categoria.query.order_by(Categoria.nombre).all()

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip().upper()
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio_compra = float(request.form.get("precio_compra", 0))
        precio_venta = float(request.form.get("precio_venta", 0))
        stock_actual = int(request.form.get("stock_actual", 0))
        stock_minimo = int(request.form.get("stock_minimo", 5))
        unidad_medida = request.form.get("unidad_medida", "unidad")
        categoria_id = request.form.get("categoria_id") or None

        if not codigo or not nombre:
            flash("El código y el nombre son obligatorios.", "danger")
            return render_template("inventario/form.html", categorias=categorias)

        if Producto.query.filter_by(codigo=codigo).first():
            flash(f"Ya existe un producto con el código {codigo}.", "danger")
            return render_template("inventario/form.html", categorias=categorias)

        producto = Producto(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            unidad_medida=unidad_medida,
            categoria_id=int(categoria_id) if categoria_id else None,
        )
        db.session.add(producto)
        db.session.commit()
        flash(f"Producto '{nombre}' creado exitosamente.", "success")
        return redirect(url_for("inventario.lista_productos"))

    return render_template("inventario/form.html", categorias=categorias)


@inventario_bp.route("/<int:producto_id>/editar", methods=["GET", "POST"])
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()

    if request.method == "POST":
        producto.nombre = request.form.get("nombre", "").strip()
        producto.descripcion = request.form.get("descripcion", "").strip()
        producto.precio_compra = float(request.form.get("precio_compra", 0))
        producto.precio_venta = float(request.form.get("precio_venta", 0))
        producto.stock_minimo = int(request.form.get("stock_minimo", 5))
        producto.unidad_medida = request.form.get("unidad_medida", "unidad")
        cat_id = request.form.get("categoria_id")
        producto.categoria_id = int(cat_id) if cat_id else None

        db.session.commit()
        flash(f"Producto '{producto.nombre}' actualizado.", "success")
        return redirect(url_for("inventario.lista_productos"))

    return render_template("inventario/form.html", producto=producto, categorias=categorias)


@inventario_bp.route("/<int:producto_id>/eliminar", methods=["POST"])
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    producto.activo = False
    db.session.commit()
    flash(f"Producto '{producto.nombre}' desactivado.", "warning")
    return redirect(url_for("inventario.lista_productos"))


# ---------------------------------------------------------------------------
# Movimientos de stock
# ---------------------------------------------------------------------------

@inventario_bp.route("/<int:producto_id>/ajuste", methods=["GET", "POST"])
def ajuste_stock(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    if request.method == "POST":
        tipo = request.form.get("tipo", "entrada")
        cantidad = int(request.form.get("cantidad", 0))
        motivo = request.form.get("motivo", "").strip()

        if cantidad <= 0:
            flash("La cantidad debe ser mayor a 0.", "danger")
            return render_template("inventario/ajuste.html", producto=producto)

        cantidad_anterior = producto.stock_actual

        if tipo == "entrada":
            producto.stock_actual += cantidad
        elif tipo == "salida":
            if cantidad > producto.stock_actual:
                flash("Stock insuficiente para realizar la salida.", "danger")
                return render_template("inventario/ajuste.html", producto=producto)
            producto.stock_actual -= cantidad
        else:  # ajuste directo
            producto.stock_actual = cantidad

        movimiento = MovimientoInventario(
            producto_id=producto.id,
            tipo=tipo,
            cantidad=cantidad,
            cantidad_anterior=cantidad_anterior,
            cantidad_posterior=producto.stock_actual,
            motivo=motivo,
        )
        db.session.add(movimiento)
        db.session.commit()
        flash(f"Ajuste de stock aplicado. Stock actual: {producto.stock_actual}.", "success")
        return redirect(url_for("inventario.lista_productos"))

    return render_template("inventario/ajuste.html", producto=producto)


@inventario_bp.route("/movimientos")
def movimientos():
    movs = (
        MovimientoInventario.query
        .order_by(MovimientoInventario.fecha.desc())
        .limit(100)
        .all()
    )
    return render_template("inventario/movimientos.html", movimientos=movs)


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------

@inventario_bp.route("/categorias")
def lista_categorias():
    cats = Categoria.query.order_by(Categoria.nombre).all()
    return render_template("inventario/categorias.html", categorias=cats)


@inventario_bp.route("/categorias/nueva", methods=["POST"])
def nueva_categoria():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    if not nombre:
        flash("El nombre de la categoría es obligatorio.", "danger")
    elif Categoria.query.filter_by(nombre=nombre).first():
        flash(f"La categoría '{nombre}' ya existe.", "danger")
    else:
        db.session.add(Categoria(nombre=nombre, descripcion=descripcion))
        db.session.commit()
        flash(f"Categoría '{nombre}' creada.", "success")
    return redirect(url_for("inventario.lista_categorias"))


# ---------------------------------------------------------------------------
# API JSON (para el POS)
# ---------------------------------------------------------------------------

@inventario_bp.route("/api/buscar")
def api_buscar_producto():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    productos = Producto.query.filter(
        Producto.activo == True,
        db.or_(
            Producto.nombre.ilike(f"%{q}%"),
            Producto.codigo.ilike(f"%{q}%"),
        )
    ).limit(10).all()
    return jsonify([
        {
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "precio_venta": p.precio_venta,
            "stock_actual": p.stock_actual,
            "unidad_medida": p.unidad_medida,
        }
        for p in productos
    ])
