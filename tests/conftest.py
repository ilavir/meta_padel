"""
Test configuration and fixtures for Meta Padel Rating System
"""
import os
import tempfile
import shutil
import pytest
from werkzeug.security import generate_password_hash

# Set testing environment before importing app
os.environ['FLASK_ENV'] = 'testing'

from app import create_app, db
from app.models import User, Role, Score, UserRankHistory
from config import TestingConfig


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    # Set testing environment
    os.environ['FLASK_ENV'] = 'testing'
    
    app = create_app(TestingConfig)
    
    # Create application context
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Create default roles
        create_default_roles()
        
        yield app
        
        # Cleanup
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        # Start a transaction
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Configure session to use the transaction
        db.session.configure(bind=connection)
        
        yield db.session
        
        # Rollback transaction and close connection
        transaction.rollback()
        connection.close()
        db.session.remove()


@pytest.fixture
def temp_upload_dir(app):
    """Create temporary upload directory for testing."""
    temp_dir = tempfile.mkdtemp()
    avatars_dir = os.path.join(temp_dir, 'avatars')
    os.makedirs(avatars_dir, exist_ok=True)
    
    # Update app config to use temp directory
    app.config['UPLOAD_FOLDER'] = temp_dir
    app.config['AVATARS_FOLDER'] = avatars_dir
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def create_default_roles():
    """Create default roles for testing."""
    roles_data = [
        {'name': 'superadmin', 'description': 'Super Administrator'},
        {'name': 'admin', 'description': 'Administrator'},
        {'name': 'player', 'description': 'Player'}
    ]
    
    for role_data in roles_data:
        if not Role.query.filter_by(name=role_data['name']).first():
            role = Role(**role_data)
            db.session.add(role)
    
    db.session.commit()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        username='testuser',
        email='test@example.com',
        name='Test User',
        phone='+1234567890',
        gender='male',
        password_hash=generate_password_hash('testpassword'),
        active=True
    )
    
    # Add player role
    player_role = Role.query.filter_by(name='player').first()
    if player_role:
        user.roles.append(player_role)
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        username='admin',
        email='admin@example.com',
        name='Admin User',
        phone='+1234567891',
        gender='female',
        password_hash=generate_password_hash('adminpassword'),
        active=True
    )
    
    # Add admin role
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_role:
        user.roles.append(admin_role)
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def superadmin_user(db_session):
    """Create a superadmin user for testing."""
    user = User(
        username='superadmin',
        email='superadmin@example.com',
        name='Super Admin',
        phone='+1234567892',
        gender='male',
        password_hash=generate_password_hash('superadminpassword'),
        active=True
    )
    
    # Add superadmin role
    superadmin_role = Role.query.filter_by(name='superadmin').first()
    if superadmin_role:
        user.roles.append(superadmin_role)
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def authenticated_client(client, sample_user):
    """Create authenticated client session."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_user.id)
        sess['_fresh'] = True
    
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Create authenticated admin client session."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    
    return client
