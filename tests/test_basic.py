"""
Basic tests to verify test setup is working
"""
import pytest
from app import create_app, db
from config import TestingConfig


class TestBasicSetup:
    """Test basic application setup."""
    
    def test_app_creation(self):
        """Test that app can be created with testing config."""
        app = create_app(TestingConfig)
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_database_connection(self, app):
        """Test database connection works."""
        with app.app_context():
            # Should be able to create tables
            db.create_all()
            
            # Should be able to query (even if empty)
            from app.models import User
            users = User.query.all()
            assert isinstance(users, list)
    
    def test_client_creation(self, client):
        """Test that test client works."""
        response = client.get('/')
        # Should get some response (even if 404 or redirect)
        assert response.status_code in [200, 302, 404]
    
    def test_config_values(self, app):
        """Test that testing configuration is applied."""
        with app.app_context():
            assert app.config['TESTING'] is True
            assert app.config['WTF_CSRF_ENABLED'] is False
            assert 'sqlite:///:memory:' in app.config['SQLALCHEMY_DATABASE_URI']
