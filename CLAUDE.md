# Meta Padel Rating System - Developer Guide

## Project Overview

This is a **Flask-based web application** for managing and tracking padel/tennis player ratings and scores. The application provides user management, role-based access control, score tracking, and player ranking functionality.

**Main Purpose**: Rating system for Meta Padel Dashboard with user profiles, scoring, and leaderboards.

## Technology Stack

### Core Framework
- **Flask 3.1.1** - Main web framework
- **Python 3.13** - Runtime environment
- **SQLAlchemy 2.0.41** - ORM and database abstraction
- **Flask-Login 0.6.3** - User session management
- **Flask-Migrate 4.1.0** - Database migrations (Alembic)
- **Flask-WTF 1.2.2** - Form handling and validation

### Frontend
- **Bootstrap 5** - CSS framework (static files in `/app/static/`)
- **Jinja2 3.1.6** - Template engine
- **Bootstrap Icons** - Icon library

### Database
- **Development**: SQLite (`app.db`)
- **Production**: MariaDB 11 (Docker container)
- **Testing**: In-memory SQLite

### Additional Libraries
- **Pillow 11.2.1** - Image processing for avatars
- **Sentry SDK 2.30.0** - Error monitoring
- **Gunicorn** - Production WSGI server
- **Faker** - Test data generation

## Project Structure

```
/home/lemian/projects/zubr.digital/meta_padel/rating/
├── app/                          # Main application package
│   ├── __init__.py              # App factory and configuration
│   ├── models.py                # SQLAlchemy models
│   ├── services.py              # Shared business logic
│   ├── cli.py                   # CLI commands
│   ├── avatar_utils.py          # Avatar image processing
│   ├── rating/                  # Rating blueprint
│   │   ├── __init__.py
│   │   ├── rating.py           # Main rating routes
│   │   ├── score_templates.py  # Score template management
│   │   ├── forms.py            # WTForms definitions
│   │   └── services.py         # Rating-specific logic
│   ├── user/                    # User authentication blueprint
│   │   ├── __init__.py
│   │   ├── routes.py           # Login/register/profile routes
│   │   └── forms.py            # User forms
│   ├── users/                   # User management blueprint (admin)
│   │   ├── __init__.py
│   │   ├── users.py            # User CRUD operations
│   │   ├── roles.py            # Role management
│   │   └── forms.py            # Admin forms
│   ├── static/                  # Static assets
│   │   ├── css/                # Bootstrap CSS and custom styles
│   │   ├── js/                 # Bootstrap JavaScript
│   │   ├── img/                # Static images
│   │   └── uploads/avatars/    # User avatar uploads
│   └── templates/               # Jinja2 templates
│       ├── base.html           # Base template
│       ├── rating/             # Rating templates
│       ├── user/               # User auth templates
│       └── users/              # Admin templates
├── migrations/                  # Alembic database migrations
├── config.py                   # Configuration classes
├── tennis.py                   # Main Flask application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Multi-container setup
├── init_db.py                  # Database initialization script
├── seed_data.py               # Test data generation
├── start.sh                   # Production startup script
└── logging.conf               # Logging configuration
```

## Database Architecture

### Core Models

1. **User** (`app/models.py:26`)
   - Primary user entity with authentication
   - Fields: username, email, name, phone, gender, avatar_filename, active, etc.
   - Methods: Role management, password handling, avatar processing
   - Relationships: roles (many-to-many), scores (one-to-many), rank_history

2. **Role** (`app/models.py:240`)
   - Role-based access control
   - Default roles: superadmin, admin, player
   - Many-to-many relationship with users

3. **Score** (`app/models.py:287`)
   - Individual score entries for users
   - Fields: user_id, score, comment, created_by, created_at
   - Used for calculating total scores and rankings

4. **ScoreTemplate** (`app/models.py:305`)
   - Predefined score templates for quick score entry
   - Fields: name, score, comment

5. **UserRankHistory** (`app/models.py:272`)
   - Historical ranking data for trend analysis
   - Tracks rank changes over time by gender/type

### Database Configuration
- **Development**: SQLite at `app.db`
- **Production**: MariaDB with environment variables
- **Migrations**: Located in `/migrations/versions/`

## Key Features & Functionality

### 1. User Management
- User registration, login, logout (`/app/user/routes.py`)
- Profile editing with avatar upload
- Role-based access control (superadmin, admin, player)
- User activation/deactivation

### 2. Rating System
- Player rankings by gender (male/female) or combined
- Score tracking and history
- Rank change calculations (daily snapshots)
- Score templates for quick entry

### 3. Avatar System
- Multi-size avatar generation (thumbnail, small, medium, large)
- Automatic image processing and optimization
- Default avatar fallback
- CLI commands for avatar management

### 4. Administrative Features
- User management interface (`/users/`)
- Role assignment and management
- Score template management
- Bulk operations via CLI

## Development Workflow

### Setup Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize application (database, default avatars, roles)
python init_app.py

# Create superadmin user with full initialization
python init_app.py --create-admin --email admin@example.com --password secure_password

# Run database migrations
flask db upgrade

# Generate test data
python seed_data.py

# Start development server
flask run
```

### CLI Commands
```bash
# Avatar management
flask avatar cleanup           # Remove orphaned avatars
flask avatar regenerate       # Regenerate all avatar sizes
flask avatar regenerate-user <username>  # Regenerate for specific user
flask avatar init-default     # Initialize default avatars
```

### Docker Commands
```bash
# Build and run with Docker Compose
docker-compose up --build

# Access application: http://localhost:5100
# Access phpMyAdmin: http://localhost:5188
```

## Configuration

### Environment Variables
- `FLASK_ENV`: development/production/testing
- `SECRET_KEY`: Flask secret key (required)
- `SESSION_COOKIE_NAME`: Session cookie name
- `SENTRY_FLASK_DSN`: Sentry error tracking DSN
- Database credentials for production (MariaDB)

### Configuration Classes (`config.py`)
- `DevelopmentConfig`: SQLite, debug enabled
- `ProductionConfig`: MariaDB, Sentry integration
- `TestingConfig`: In-memory SQLite

## URL Structure & Blueprints

### Main Routes
- `/` - Rating dashboard (main page)
- `/user/login` - User authentication
- `/user/register` - User registration
- `/user/profile` - User profile management
- `/users/` - Admin user management
- `/health` - Docker health check

### Blueprint Organization
- `rating` - Main rating functionality
- `user` - Authentication and profile
- `users` - Administrative user management
- `cli` - Command-line interface

## Security Features

- Password hashing with Werkzeug
- Role-based access control decorators
- CSRF protection via Flask-WTF
- User session management
- Input validation and sanitization
- Secure file upload handling

## Testing & Data

### Test Data Generation
- `seed_data.py` creates 10 test users with random scores
- Default password for test users: `password123`
- 4 roles: admin, player, coach, guest

### Logging
- Configured in `logging.conf`
- Outputs to stdout with timestamps
- Debug level in development

## Important Design Patterns

1. **Flask Application Factory**: `app/__init__.py:create_app()`
2. **Blueprint Architecture**: Modular route organization
3. **Role-Based Access Control**: Decorator pattern in `services.py`
4. **Database Migrations**: Alembic integration
5. **Multi-size Image Processing**: Avatar utility functions
6. **Environment-based Configuration**: Config classes

## Common Development Tasks

### Adding New Features
1. Create new blueprint if needed
2. Add models to `models.py`
3. Create database migration: `flask db migrate -m "description"`
4. Add forms in respective `forms.py`
5. Implement routes and templates
6. Update navigation in `base.html`

### Database Changes
1. Modify models in `models.py`
2. Generate migration: `flask db migrate -m "description"`
3. Review migration file in `migrations/versions/`
4. Apply migration: `flask db upgrade`

### Adding New Roles
1. Update `init_db.py:create_roles()`
2. Add role checks in route decorators
3. Update templates for role-specific UI

## Deployment Notes

- Application runs on port 5100 in production
- Uses Gunicorn WSGI server
- Docker containers for web app, database, and phpMyAdmin
- Avatar uploads persisted in Docker volume
- Health check endpoint at `/health`

## Language/Localization
- UI text is in Russian (Cyrillic)
- Error messages and flash messages in Russian
- Consider this when adding new text content

This application is well-structured for a rating system but could benefit from additional testing, API endpoints, and more comprehensive documentation.