#!/usr/bin/env python
"""
Script to initialize the database with required roles and an optional superadmin user.
"""
import argparse
import sqlalchemy as sa
from app import create_app, db
from app.models import User, Role
from config import DevelopmentConfig

# Initialize Flask app
app = create_app(config_class=DevelopmentConfig)


def create_roles():
    """Create required roles in the database"""
    roles = [
        {"name": "superadmin", "description": "Super administrator with full system access"},
        {"name": "admin", "description": "Administrator with management access"},
        {"name": "player", "description": "Regular player"},
    ]

    created_roles = []
    for role_data in roles:
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

    # Create superadmin user
    user = User(
        username=username,
        email=email,
        name=name,
        phone=phone,
        gender=gender,
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


def init_database(create_admin=False, email=None, password=None, username=None):
    """Initialize the database with required roles and optionally a superadmin user"""
    print("Starting database initialization...")

    # Create roles
    roles = create_roles()

    # Create superadmin user if requested
    if create_admin:
        if not all([email, password]):
            print("Error: email, and password are required to create a superadmin user")
            return
        create_superadmin(email, password, username)

    print("Database initialization completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database with roles and optionally create a superadmin user")
    parser.add_argument("--create-admin", action="store_true", help="Create a superadmin user")
    parser.add_argument("--email", help="Email for the superadmin user")
    parser.add_argument("--password", help="Password for the superadmin user")
    parser.add_argument("--username", help="Username for the superadmin user (defaults to email prefix)")
    parser.add_argument("--name", default="Super Admin", help="Name for the superadmin user")
    parser.add_argument("--phone", default="", help="Phone number for the superadmin user")

    args = parser.parse_args()

    with app.app_context():
        if args.create_admin:
            init_database(
                create_admin=True,
                email=args.email,
                password=args.password,
                username=args.username
            )
        else:
            init_database()
