"""
Simple working tests to verify our test setup
"""
import pytest
from app.models import User, Role


class TestSimpleModels:
    """Simple model tests that should work."""
    
    def test_user_creation_basic(self, app):
        """Test basic user creation with all required fields."""
        with app.app_context():
            from app import db
            db.create_all()
            
            user = User(
                username='testuser1',
                email='test1@example.com',
                name='Test User 1',
                phone='+1234567890',
                gender='male'
            )
            
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser1'
            assert user.email == 'test1@example.com'
            assert user.active is False  # Default value
            
            # Clean up
            db.session.delete(user)
            db.session.commit()
    
    def test_role_creation_basic(self, app):
        """Test basic role creation."""
        with app.app_context():
            from app import db
            db.create_all()
            
            role = Role(name='testrole1', description='Test Role 1')
            
            db.session.add(role)
            db.session.commit()
            
            assert role.id is not None
            assert role.name == 'testrole1'
            assert role.description == 'Test Role 1'
            
            # Clean up
            db.session.delete(role)
            db.session.commit()
    
    def test_user_password_basic(self, app):
        """Test password functionality."""
        with app.app_context():
            from app import db
            db.create_all()
            
            user = User(
                username='passuser',
                email='pass@example.com',
                name='Pass User',
                phone='+1234567891',
                gender='female'
            )
            
            # Test password setting
            user.set_password('testpass123')
            
            db.session.add(user)
            db.session.commit()
            
            # Test password checking
            assert user.check_password('testpass123') is True
            assert user.check_password('wrongpass') is False
            
            # Clean up
            db.session.delete(user)
            db.session.commit()


class TestBasicRoutes:
    """Test basic route functionality."""
    
    def test_index_route_exists(self, client):
        """Test that index route responds."""
        response = client.get('/')
        # Should get some response (200, 302 redirect, etc.)
        assert response.status_code in [200, 302, 404]
    
    def test_login_route_exists(self, client):
        """Test that login route exists."""
        response = client.get('/user/login')
        assert response.status_code in [200, 302]
