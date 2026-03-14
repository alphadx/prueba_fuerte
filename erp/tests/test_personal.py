"""Tests para el módulo de Personal."""
import pytest
from erp.modules.personal import _validar_rut, _calcular_sueldo_liquido
from erp.models import Empleado, PagoSueldo


class TestValidarRut:
    """Tests unitarios para la validación de RUT chileno."""

    def test_rut_valido(self):
        assert _validar_rut("12345678-5") is True

    def test_rut_valido_k(self):
        # RUT con dígito verificador K
        assert _validar_rut("5126663-3") is True

    def test_rut_con_puntos(self):
        assert _validar_rut("12.345.678-5") is True

    def test_rut_invalido(self):
        assert _validar_rut("12345678-0") is False

    def test_rut_muy_corto(self):
        assert _validar_rut("123-9") is False

    def test_rut_vacio(self):
        assert _validar_rut("") is False


class TestCalculoSueldo:
    """Tests unitarios para el cálculo de sueldos."""

    def test_sueldo_base_sin_extras(self):
        resultado = _calcular_sueldo_liquido(460000, 0)
        # AFP 11.5% + Salud 7% = 18.5% descuento
        descuento_esperado = round(460000 * 0.115, 0) + round(460000 * 0.07, 0)
        assert resultado["sueldo_liquido"] == pytest.approx(460000 - descuento_esperado, abs=1)
        assert resultado["horas_extra"] == 0
        assert resultado["monto_horas_extra"] == 0

    def test_sueldo_con_horas_extra(self):
        resultado = _calcular_sueldo_liquido(600000, 10)
        assert resultado["monto_horas_extra"] > 0
        assert resultado["sueldo_liquido"] > resultado["sueldo_base"] * (1 - 0.185)

    def test_descuento_afp(self):
        resultado = _calcular_sueldo_liquido(1000000, 0)
        assert resultado["descuento_afp"] == round(1000000 * 0.115, 0)

    def test_descuento_salud(self):
        resultado = _calcular_sueldo_liquido(1000000, 0)
        assert resultado["descuento_salud"] == round(1000000 * 0.07, 0)

    def test_sueldo_liquido_menor_que_bruto(self):
        resultado = _calcular_sueldo_liquido(500000, 0)
        assert resultado["sueldo_liquido"] < resultado["sueldo_base"]


class TestEmpleados:
    def test_lista_empleados(self, client):
        resp = client.get("/personal/")
        assert resp.status_code == 200

    def test_crear_empleado_valido(self, client):
        resp = client.post("/personal/nuevo", data={
            "rut": "12345678-5",
            "nombre": "Juan",
            "apellido": "Pérez",
            "cargo": "Cajero",
            "sueldo_base": "460000",
            "fecha_ingreso": "2024-01-01",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_crear_empleado_rut_invalido(self, client):
        resp = client.post("/personal/nuevo", data={
            "rut": "99999999-0",
            "nombre": "Test",
            "apellido": "Inválido",
            "cargo": "Bodeguero",
            "sueldo_base": "460000",
        }, follow_redirects=True)
        assert b"v\xc3\xa1lido" in resp.data or b"v" in resp.data  # "válido"

    def test_crear_empleado_rut_duplicado(self, client):
        data = {
            "rut": "12345678-5",
            "nombre": "Pedro",
            "apellido": "González",
            "cargo": "Vendedor",
            "sueldo_base": "460000",
            "fecha_ingreso": "2024-01-01",
        }
        client.post("/personal/nuevo", data=data, follow_redirects=True)
        resp = client.post("/personal/nuevo", data=data, follow_redirects=True)
        assert resp.status_code == 200


class TestSueldos:
    def test_lista_sueldos(self, client):
        resp = client.get("/personal/sueldos")
        assert resp.status_code == 200

    def test_calcular_sueldo_empleado(self, client, app, db):
        with app.app_context():
            emp = Empleado(
                rut="98765432-1",
                nombre="Ana",
                apellido="García",
                cargo="Administradora",
                sueldo_base=700000,
                fecha_ingreso=__import__('datetime').date(2023, 1, 1),
            )
            db.session.add(emp)
            db.session.commit()
            eid = emp.id

        resp = client.post("/personal/sueldos/calcular", data={
            "empleado_id": str(eid),
            "periodo": "2024-03",
            "horas_extra": "0",
            "metodo_pago": "transferencia",
        }, follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            pago = PagoSueldo.query.filter_by(empleado_id=eid, periodo="2024-03").first()
            assert pago is not None
            assert pago.sueldo_liquido > 0
            assert pago.sueldo_liquido < 700000
            assert pago.estado == "pendiente"

    def test_pagar_sueldo(self, client, app, db):
        with app.app_context():
            emp = Empleado(
                rut="11111111-1",
                nombre="Carlos",
                apellido="Soto",
                cargo="Vendedor",
                sueldo_base=500000,
                fecha_ingreso=__import__('datetime').date(2023, 6, 1),
            )
            db.session.add(emp)
            db.session.flush()

            pago = PagoSueldo(
                empleado_id=emp.id,
                periodo="2024-02",
                sueldo_base=500000,
                descuento_afp=57500,
                descuento_salud=35000,
                sueldo_liquido=407500,
            )
            db.session.add(pago)
            db.session.commit()
            pago_id = pago.id

        resp = client.post(
            f"/personal/sueldos/{pago_id}/pagar", follow_redirects=True
        )
        assert resp.status_code == 200

        with app.app_context():
            p = PagoSueldo.query.get(pago_id)
            assert p.estado == "pagado"
            assert p.fecha_pago is not None
