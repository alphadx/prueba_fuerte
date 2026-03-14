"""
ERP Almacén de Barrio - Chile
Paquete principal de la aplicación
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_object=None):
    """Application factory."""
    app = Flask(__name__)

    if config_object is None:
        from .config import Config
        app.config.from_object(Config)
    else:
        app.config.from_object(config_object)

    db.init_app(app)

    # Registrar blueprints
    from .modules.inventario import inventario_bp
    from .modules.ventas import ventas_bp
    from .modules.personal import personal_bp
    from .modules.reportes import reportes_bp
    from .modules.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(inventario_bp, url_prefix="/inventario")
    app.register_blueprint(ventas_bp, url_prefix="/ventas")
    app.register_blueprint(personal_bp, url_prefix="/personal")
    app.register_blueprint(reportes_bp, url_prefix="/reportes")

    with app.app_context():
        db.create_all()
        _seed_datos_iniciales()

    return app


def _seed_datos_iniciales():
    """Crea datos de ejemplo si la base está vacía."""
    from .models import Categoria, Producto

    if Categoria.query.count() == 0:
        categorias = [
            Categoria(nombre="Abarrotes", descripcion="Productos básicos de almacén"),
            Categoria(nombre="Lácteos", descripcion="Leche, queso, yogurt"),
            Categoria(nombre="Bebidas", descripcion="Jugos, aguas, bebidas"),
            Categoria(nombre="Limpieza", descripcion="Artículos de aseo"),
            Categoria(nombre="Panadería", descripcion="Pan y productos de panadería"),
        ]
        db.session.add_all(categorias)
        db.session.flush()

        productos_demo = [
            Producto(
                codigo="ARR001", nombre="Arroz 1kg", categoria_id=categorias[0].id,
                precio_compra=900, precio_venta=1200, stock_actual=50, stock_minimo=10,
                unidad_medida="kg"
            ),
            Producto(
                codigo="AZU001", nombre="Azúcar 1kg", categoria_id=categorias[0].id,
                precio_compra=850, precio_venta=1100, stock_actual=40, stock_minimo=10,
                unidad_medida="kg"
            ),
            Producto(
                codigo="ACE001", nombre="Aceite 1L", categoria_id=categorias[0].id,
                precio_compra=1500, precio_venta=2200, stock_actual=25, stock_minimo=5,
                unidad_medida="litro"
            ),
            Producto(
                codigo="LEC001", nombre="Leche entera 1L", categoria_id=categorias[1].id,
                precio_compra=700, precio_venta=950, stock_actual=30, stock_minimo=10,
                unidad_medida="litro"
            ),
            Producto(
                codigo="BEB001", nombre="Coca-Cola 1.5L", categoria_id=categorias[2].id,
                precio_compra=900, precio_venta=1500, stock_actual=24, stock_minimo=6,
                unidad_medida="botella"
            ),
            Producto(
                codigo="PAN001", nombre="Pan marraqueta (unidad)", categoria_id=categorias[4].id,
                precio_compra=100, precio_venta=150, stock_actual=3, stock_minimo=10,
                unidad_medida="unidad"
            ),
        ]
        db.session.add_all(productos_demo)
        db.session.commit()
