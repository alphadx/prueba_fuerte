"""Tests para el módulo de Reportes y el Dashboard."""
import pytest


class TestDashboard:
    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data


class TestReportes:
    def test_index_reportes(self, client):
        resp = client.get("/reportes/")
        assert resp.status_code == 200

    def test_reporte_ventas(self, client):
        resp = client.get("/reportes/ventas")
        assert resp.status_code == 200

    def test_reporte_ventas_mes_especifico(self, client):
        resp = client.get("/reportes/ventas?mes=2024-01")
        assert resp.status_code == 200

    def test_reporte_inventario(self, client):
        resp = client.get("/reportes/inventario")
        assert resp.status_code == 200

    def test_reporte_personal(self, client):
        resp = client.get("/reportes/personal")
        assert resp.status_code == 200
