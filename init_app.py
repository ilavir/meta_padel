#!/usr/bin/env python
"""
Complete database initialization script for Meta Padel Rating System.
This script fully initializes the application with an empty database.
"""
import argparse
import os
import sys
import sqlalchemy as sa
from flask import current_app
from PIL import Image, ImageDraw, ImageFont
from app import create_app, db
from app.models import User, Role
from config import DevelopmentConfig, ProductionConfig

def create_default_avatars():
    """Create default avatars for all users"""
    avatars_dir = current_app.config['AVATARS_FOLDER']
    os.makedirs(avatars_dir, exist_ok=True)
    
    # Define avatar sizes from config
    sizes = current_app.config['AVATARS_SIZES']
    
    # Color scheme for default avatar
    color_scheme = {'bg': '#95a5a6', 'text': '#ffffff'}  # Gray background with white text
    
    # Generate each size for default avatar
    for size_name, dimensions in sizes.items():
        width, height = dimensions
        
        # Create image with colored background
        img = Image.new('RGB', (width, height), color_scheme['bg'])
        draw = ImageDraw.Draw(img)
        
        # Try to use a system font, fallback to default if not available
        try:
            # Try to load a nice font
            font_size = min(width, height) // 3
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
        except (OSError, IOError):
            try:
                # Fallback to default font
                font_size = min(width, height) // 4
                font = ImageFont.load_default()
            except:
                font = None
        
        # Draw user icon (simple circle with person silhouette or just a circle)
        circle_radius = min(width, height) // 4
        center_x, center_y = width // 2, height // 2
        
        # Draw a simple circle as user icon
        draw.ellipse([
            center_x - circle_radius, 
            center_y - circle_radius,
            center_x + circle_radius, 
            center_y + circle_radius
        ], fill=color_scheme['text'])
        
        # Save the avatar
        suffix = f"_{size_name}" if size_name != 'medium' else '_medium'
        filename = f"default{suffix}.jpg"
        filepath = os.path.join(avatars_dir, filename)
        
        img.save(filepath, 'JPEG', quality=95, optimize=True)
        print(f"Created default avatar: {filename}")

def create_roles():
    """Create required roles in the database"""
    roles_data = [
        {"name": "superadmin", "description": "Super administrator with full system access"},
        {"name": "admin", "description": "Administrator with management access"},
        {"name": "player", "description": "Regular player"},
    ]

    created_roles = []
    for role_data in roles_data:
        # Check if role already exists
        existing_role = db.session.scalar(sa.select(Role).where(Role.name == role_data["name"]))
        if existing_role:
            print(f"Role '{role_data['name']}' already exists")
            created_roles.append(existing_role)
            continue

        # Create new role
        role = Role(name=role_data["name"], description=role_data["description"])
        db.session.add(role)
        created_roles.append(role)

    db.session.commit()
    print(f"Roles initialized: {', '.join(role.name for role in created_roles)}")
    return created_roles

def create_superadmin(email, password, username=None, name="Super Admin", phone="", gender="male"):
    """Create a superadmin user if it doesn't exist"""
    # Check if user already exists
    existing_user = db.session.scalar(sa.select(User).where(User.email == email))
    if existing_user:
        print(f"User '{email}' already exists")
        return existing_user

    # Generate username from email if not provided
    if not username:
        username = email.split('@')[0]

    # Set default avatar for all users
    avatar_filename = "default.jpg"

    # Create superadmin user
    user = User(
        username=username,
        email=email,
        name=name,
        phone=phone,
        gender=gender,
        avatar_filename=avatar_filename,
        active=True
    )
    user.set_password(password)

    # Assign superadmin role
    superadmin_role = db.session.scalar(sa.select(Role).where(Role.name == "superadmin"))
    if superadmin_role:
        user.add_role(superadmin_role)

    db.session.add(user)
    db.session.commit()
    print(f"Superadmin user '{email}' created successfully")
    return user

def create_database_tables():
    """Create all database tables"""
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully")

def run_migrations():
    """Run database migrations if migration folder exists"""
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    if os.path.exists(migrations_dir):
        try:
            from flask_migrate import upgrade
            print("Running database migrations...")
            upgrade()
            print("Database migrations completed successfully")
        except ImportError:
            print("Flask-Migrate not available, skipping migrations")
        except Exception as e:
            print(f"Migration failed: {e}")
    else:
        print("No migrations directory found, skipping migrations")

def initialize_application():
    """Initialize the complete application"""
    print("Starting complete application initialization...")
    
    # Create database tables or run migrations
    try:
        run_migrations()
    except Exception as e:
        print(f"Migrations failed, creating tables manually: {e}")
        create_database_tables()
    
    # Create default avatars
    print("Creating default avatars...")
    create_default_avatars()
    
    # Create roles
    print("Creating system roles...")
    create_roles()
    
    print("Application initialization completed successfully!")

def init_database(create_admin=False, email=None, password=None, username=None, name=None, phone=None, gender=None):
    """Initialize the database with required roles and optionally a superadmin user"""
    print("Starting database initialization...")

    # Initialize application components
    initialize_application()

    # Create superadmin user if requested
    if create_admin:
        if not all([email, password]):
            print("Error: email and password are required to create a superadmin user")
            return
        
        # Use provided values or defaults
        create_superadmin(
            email=email,
            password=password,
            username=username,
            name=name or "Super Admin",
            phone=phone or "",
            gender=gender or "male"
        )

    print("Database initialization completed successfully!")

def get_config_class():
    """Get the appropriate configuration class based on environment"""
    env = os.environ.get('FLASK_ENV', 'development').lower()
    if env == 'production':
        return ProductionConfig
    else:
        return DevelopmentConfig

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Meta Padel Rating System database")
    parser.add_argument("--create-admin", action="store_true", help="Create a superadmin user")
    parser.add_argument("--email", help="Email for the superadmin user")
    parser.add_argument("--password", help="Password for the superadmin user")
    parser.add_argument("--username", help="Username for the superadmin user (defaults to email prefix)")
    parser.add_argument("--name", help="Full name for the superadmin user")
    parser.add_argument("--phone", help="Phone number for the superadmin user")
    parser.add_argument("--gender", choices=['male', 'female'], default='male', help="Gender for the superadmin user")
    parser.add_argument("--config", choices=['development', 'production'], help="Configuration to use")

    args = parser.parse_args()

    # Create app with appropriate config
    config_class = None
    if args.config:
        if args.config == 'production':
            config_class = ProductionConfig
        else:
            config_class = DevelopmentConfig
    else:
        config_class = get_config_class()

    app = create_app(config_class=config_class)

    with app.app_context():
        if args.create_admin:
            init_database(
                create_admin=True,
                email=args.email,
                password=args.password,
                username=args.username,
                name=args.name,
                phone=args.phone,
                gender=args.gender
            )
        else:
            init_database()