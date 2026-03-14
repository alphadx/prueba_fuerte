"""
Fixtures comunes para los tests del ERP.
"""
import pytest
from erp import create_app, db as _db
from erp.config import TestConfig


@pytest.fixture(scope="session")
def app():
    """Crea la aplicación Flask en modo test con BD en memoria."""
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Devuelve la sesión de BD y hace rollback al final del test."""
    with app.app_context():
        yield _db
        _db.session.rollback()
