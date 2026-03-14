"""Tests para el módulo de Ventas y Pagos."""
import json
import pytest
from erp.models import Producto, Venta
from erp.modules.ventas import _procesar_pago, _generar_numero_boleta


class TestProcesarPago:
    """Tests unitarios para la función de pago automático."""

    def test_pago_efectivo(self, app):
        with app.app_context():
            result = _procesar_pago("efectivo", 1000)
        assert result["estado"] == "aprobado"
        assert result["referencia"].startswith("EFE-")

    def test_pago_debito(self, app):
        with app.app_context():
            result = _procesar_pago("debito", 2500)
        assert result["estado"] == "aprobado"
        assert result["referencia"].startswith("TBK-")

    def test_pago_credito(self, app):
        with app.app_context():
            result = _procesar_pago("credito", 5000)
        assert result["estado"] == "aprobado"
        assert result["referencia"].startswith("TBK-")

    def test_pago_mercadopago(self, app):
        with app.app_context():
            result = _procesar_pago("mercadopago", 3000)
        assert result["estado"] == "aprobado"
        assert result["referencia"].startswith("MP-")

    def test_pago_transferencia(self, app):
        with app.app_context():
            result = _procesar_pago("transferencia", 50000)
        assert result["estado"] == "aprobado"
        assert result["referencia"].startswith("TRF-")

    def test_pago_transferencia_con_referencia(self, app):
        with app.app_context():
            result = _procesar_pago("transferencia", 50000, "TRF-CUSTOM-123")
        assert result["referencia"] == "TRF-CUSTOM-123"

    def test_metodo_invalido(self, app):
        with app.app_context():
            result = _procesar_pago("cripto", 1000)
        assert result["estado"] == "rechazado"


class TestPOS:
    def _producto_id(self, app, db):
        """Obtiene el ID de un producto activo con stock."""
        with app.app_context():
            p = Producto.query.filter(Producto.activo == True, Producto.stock_actual > 0).first()
            return p.id if p else None

    def test_pos_carga(self, client):
        resp = client.get("/ventas/pos")
        assert resp.status_code == 200
        assert b"Carrito" in resp.data

    def test_venta_exitosa(self, client, app, db):
        with app.app_context():
            p = Producto.query.filter(
                Producto.activo == True, Producto.stock_actual > 0
            ).first()
            pid = p.id
            stock_antes = p.stock_actual

        payload = {
            "items": [{"producto_id": pid, "cantidad": 1}],
            "metodo_pago": "efectivo",
            "empleado_id": None,
        }
        resp = client.post(
            "/ventas/pos/procesar",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["estado"] == "ok"
        assert data["numero_boleta"].startswith("B")
        assert data["total"] > 0
        assert data["referencia_pago"].startswith("EFE-")

        # Verificar que el stock bajó
        with app.app_context():
            p = Producto.query.get(pid)
            assert p.stock_actual == stock_antes - 1

    def test_venta_carrito_vacio(self, client):
        payload = {"items": [], "metodo_pago": "efectivo"}
        resp = client.post(
            "/ventas/pos/procesar",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert b"vac" in resp.data  # "vacío"

    def test_venta_metodo_invalido(self, client, app):
        with app.app_context():
            p = Producto.query.filter(
                Producto.activo == True, Producto.stock_actual > 0
            ).first()
            pid = p.id

        payload = {
            "items": [{"producto_id": pid, "cantidad": 1}],
            "metodo_pago": "bitcoin",
        }
        resp = client.post(
            "/ventas/pos/procesar",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_venta_stock_insuficiente(self, client, app, db):
        with app.app_context():
            p = Producto(
                codigo="NOSTOCK001",
                nombre="Sin Stock",
                precio_compra=100,
                precio_venta=200,
                stock_actual=0,
                stock_minimo=1,
            )
            db.session.add(p)
            db.session.commit()
            pid = p.id

        payload = {
            "items": [{"producto_id": pid, "cantidad": 1}],
            "metodo_pago": "efectivo",
        }
        resp = client.post(
            "/ventas/pos/procesar",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert b"insuficiente" in resp.data


class TestHistorialVentas:
    def test_lista_ventas(self, client):
        resp = client.get("/ventas/")
        assert resp.status_code == 200

    def test_filtro_metodo(self, client):
        resp = client.get("/ventas/?metodo=efectivo")
        assert resp.status_code == 200

    def test_boleta_no_existente(self, client):
        resp = client.get("/ventas/9999")
        assert resp.status_code == 404

    def test_boleta_existente(self, client, app, db):
        # Crear una venta primero
        with app.app_context():
            p = Producto.query.filter(
                Producto.activo == True, Producto.stock_actual > 0
            ).first()
            pid = p.id

        payload = {
            "items": [{"producto_id": pid, "cantidad": 1}],
            "metodo_pago": "debito",
        }
        resp_venta = client.post(
            "/ventas/pos/procesar",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp_venta.status_code == 200

        with app.app_context():
            v = Venta.query.order_by(Venta.id.desc()).first()
            vid = v.id

        resp = client.get(f"/ventas/{vid}/boleta")
        assert resp.status_code == 200
        assert b"BOLETA" in resp.data


class TestIVA:
    def test_iva_calculado_correctamente(self, client, app, db):
        """IVA = 19% del total (precio incluye IVA)."""
        with app.app_context():
            p = Producto(
                codigo="IVA001",
                nombre="Prod IVA",
                precio_compra=840,
                precio_venta=1000,
                stock_actual=10,
                stock_minimo=1,
            )
            db.session.add(p)
            db.session.commit()
            pid = p.id

        payload = {
            "items": [{"producto_id": pid, "cantidad": 1}],
            "metodo_pago": "efectivo",
        }
        resp = client.post(
            "/ventas/pos/procesar",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["total"] == 1000
        # IVA = 1000 * 0.19 / 1.19 ≈ 159.66 → redondeado 160
        assert data["iva"] == round(1000 * 0.19 / 1.19, 0)
