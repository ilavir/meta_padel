#!/usr/bin/env python
"""
Script to populate the database with test data for users, scores, and roles.
"""
import random
from datetime import datetime, timedelta
from faker import Faker
import sqlalchemy as sa
from app import create_app, db
from app.models import User, Role, Score
from config import DevelopmentConfig

# Initialize Flask app and Faker
app = create_app(config_class=DevelopmentConfig)
fake = Faker()

# Number of test records to create
NUM_USERS = 10
NUM_ROLES = 3
SCORES_PER_USER = 5


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


def create_users(roles):
    """Create test users with random roles"""
    users = []
    for i in range(NUM_USERS):
        # Create user with fake data
        user = User(
            email=fake.email(),
            name=fake.name(),
            phone=fake.phone_number(),
            gender=random.choice(["male", "female"]),
            about_me=fake.text(max_nb_chars=200),
            active=random.choice([True, False])
        )
        user.set_password("password123")

        # Assign 1-3 random roles to each user
        num_roles = random.randint(1, 3)
        selected_roles = random.sample(roles, num_roles)
        for role in selected_roles:
            user.add_role(role)

        db.session.add(user)
        users.append(user)

    db.session.commit()
    print(f"Created {len(users)} users")
    return users


def create_scores(users):
    """Create random scores for users"""
    scores = []
    now = datetime.now()

    for user in users:
        for _ in range(SCORES_PER_USER):
            # Random score between 1 and 100
            score_value = random.randint(1, 100)
            # Random date within the last 30 days
            score_date = now - timedelta(days=random.randint(0, 30))
            # Random user as creator (could be the same user or different)
            creator = random.choice(users)

            score = Score(
                user_id=user.id,
                score=score_value,
                comment=fake.sentence(),
                created_by=creator.id,
                created_at=score_date
            )
            db.session.add(score)
            scores.append(score)

    db.session.commit()
    print(f"Created {len(scores)} scores")


def seed_database():
    """Main function to seed the database with test data"""
    print("Starting database seeding...")

    # Create all database tables
    db.create_all()
    print("Database tables created")

    # Check if non-superadmin users already exist
    non_superadmin_users = db.session.scalars(
        sa.select(User).join(User.roles).where(Role.name != "superadmin")
    ).first()
    if non_superadmin_users:
        print("Database already contains non-superadmin users. Skipping seeding to avoid duplicates.")
        return

    # Create test data
    roles = create_roles()
    users = create_users(roles)
    create_scores(users)

    print("Database seeding completed successfully!")


if __name__ == "__main__":
    with app.app_context():
        seed_database()
