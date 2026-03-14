"""Tests para el módulo de Inventario."""
import pytest
from erp.models import Producto, Categoria, MovimientoInventario


class TestProducto:
    def test_crear_producto(self, client):
        resp = client.post("/inventario/nuevo", data={
            "codigo": "TST001",
            "nombre": "Producto Test",
            "precio_compra": "500",
            "precio_venta": "800",
            "stock_actual": "10",
            "stock_minimo": "3",
            "unidad_medida": "unidad",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Producto" in resp.data

    def test_lista_productos(self, client):
        resp = client.get("/inventario/")
        assert resp.status_code == 200
        assert b"Inventario" in resp.data

    def test_codigo_duplicado(self, client):
        client.post("/inventario/nuevo", data={
            "codigo": "DUP001",
            "nombre": "Primero",
            "precio_compra": "500",
            "precio_venta": "800",
            "stock_actual": "5",
            "stock_minimo": "2",
            "unidad_medida": "unidad",
        })
        resp = client.post("/inventario/nuevo", data={
            "codigo": "DUP001",
            "nombre": "Segundo",
            "precio_compra": "500",
            "precio_venta": "800",
            "stock_actual": "5",
            "stock_minimo": "2",
            "unidad_medida": "unidad",
        }, follow_redirects=True)
        assert b"DUP001" in resp.data  # mensaje de error contiene el código

    def test_stock_bajo_property(self, app):
        with app.app_context():
            p = Producto(
                codigo="STOCK001",
                nombre="Test Stock",
                precio_compra=100,
                precio_venta=150,
                stock_actual=2,
                stock_minimo=5,
            )
            assert p.stock_bajo is True

            p.stock_actual = 10
            assert p.stock_bajo is False

    def test_ajuste_stock_entrada(self, client, app, db):
        # Crear producto primero
        with app.app_context():
            cat = Categoria.query.first()
            p = Producto(
                codigo="AJST001",
                nombre="Ajuste Test",
                precio_compra=200,
                precio_venta=300,
                stock_actual=5,
                stock_minimo=2,
                categoria_id=cat.id if cat else None,
            )
            db.session.add(p)
            db.session.commit()
            pid = p.id

        resp = client.post(f"/inventario/{pid}/ajuste", data={
            "tipo": "entrada",
            "cantidad": "10",
            "motivo": "Compra proveedor test",
        }, follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            p = Producto.query.get(pid)
            assert p.stock_actual == 15

    def test_ajuste_stock_salida_insuficiente(self, client, app, db):
        with app.app_context():
            p = Producto(
                codigo="AJST002",
                nombre="Salida Test",
                precio_compra=200,
                precio_venta=300,
                stock_actual=3,
                stock_minimo=2,
            )
            db.session.add(p)
            db.session.commit()
            pid = p.id

        resp = client.post(f"/inventario/{pid}/ajuste", data={
            "tipo": "salida",
            "cantidad": "100",
            "motivo": "Test",
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Stock no debe cambiar
        with app.app_context():
            p = Producto.query.get(pid)
            assert p.stock_actual == 3

    def test_api_buscar_producto(self, client):
        resp = client.get("/inventario/api/buscar?q=arroz")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_movimientos(self, client):
        resp = client.get("/inventario/movimientos")
        assert resp.status_code == 200


class TestCategoria:
    def test_crear_categoria(self, client):
        resp = client.post("/inventario/categorias/nueva", data={
            "nombre": "Categoría Test",
            "descripcion": "Para pruebas",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_lista_categorias(self, client):
        resp = client.get("/inventario/categorias")
        assert resp.status_code == 200
