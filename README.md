# Meta Padel Rating System

A Flask-based web application for managing padel/tennis player ratings and scores with user management, role-based access control, and leaderboard functionality.

## Features

- **User Management**: Registration, authentication, and role-based access control
- **Rating System**: Player scoring, rankings, and historical tracking
- **Multi-size Avatars**: Automatic avatar processing in multiple sizes
- **Responsive Design**: Bootstrap-based UI with Russian language support
- **Production Ready**: Docker containerization with MariaDB database

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd meta_padel/rating
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your settings:
   ```env
   # Database settings
   MARIADB_ROOT_PASSWORD=your_root_password
   MARIADB_DATABASE=meta_padel
   MARIADB_USER=padel_user
   MARIADB_PASSWORD=your_db_password
   
   # Flask settings
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=production
   ```

3. **Build and start the application**
   ```bash
   docker-compose up --build -d
   ```

4. **Initialize the application**
   
   Wait for containers to be healthy, then initialize the database:
   ```bash
   docker-compose exec web python init_app.py --create-admin --email admin@example.com --password your_admin_password --name "Administrator"
   ```

5. **Access the application**
   - **Web Application**: http://localhost:5100
   - **phpMyAdmin**: http://localhost:5188
   - Login with the admin credentials you created in step 4

## Manual Installation (Development)

### Prerequisites

- Python 3.13+
- MariaDB or SQLite
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (for local development and running tests)

### Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   export FLASK_APP=tennis.py
   export FLASK_ENV=development
   ```

3. **Initialize database**
   ```bash
   # Initialize with admin user
   python init_app.py --create-admin --email admin@example.com --password secure_password
   
   # Or initialize without admin (roles only)
   python init_app.py
   ```

4. **Run the application**
   ```bash
   flask run
   ```

## Application Initialization Options

The `init_app.py` script provides comprehensive application initialization:

```bash
# Full initialization with admin user
python init_app.py --create-admin --email admin@example.com --password secure_password --name "Admin User" --phone "+1234567890" --gender male

# Initialize only database structure and roles
python init_app.py

# View all options
python init_app.py --help
```

### Initialization Features

- **Database Setup**: Creates all required tables or runs migrations
- **Default Avatars**: Generates default user avatars in multiple sizes
- **System Roles**: Creates superadmin, admin, and player roles
- **Admin User**: Optionally creates a superadmin user

## Docker Services

The application runs with the following services:

- **web**: Flask application (port 5100)
- **mariadb**: MariaDB 11 database
- **phpmyadmin**: Database administration interface (port 5188)

## Development

### Running Tests

The application includes a comprehensive test suite using pytest, run via
[`uv`](https://docs.astral.sh/uv/), which manages an isolated virtual
environment from `pyproject.toml`/`uv.lock` — no manual `pip install` needed.

```bash
# Run all tests (uv creates/updates .venv automatically)
uv run pytest

# Run a specific test file
uv run pytest tests/test_scheduler.py -v
```

Coverage (`--cov=app --cov-report=term-missing`) is configured in
`pyproject.toml` and reported to the terminal only; no HTML report is
generated. See `TESTING.md` for details.

Production's Docker image still installs from `requirements.txt` (pip),
which is regenerated from the `uv` lockfile via:
```bash
uv export --no-default-groups --no-annotate --no-hashes -o requirements.txt
```

#### Test Structure

```
tests/
├── conftest.py           # Test configuration and fixtures
├── test_forms.py         # Form validation tests
└── test_scheduler.py     # Scheduler job and lock-recovery tests
```

#### Test Configuration

Tests use the `TestingConfig` which:
- Uses in-memory SQLite database
- Disables CSRF protection
- Uses temporary upload directories
- Provides isolated test environment

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade
```

### Adding Test Data

```bash
# Use the existing seed script if available
python seed_data.py
```

## Configuration

The application supports multiple configuration environments:

- **Development**: Uses SQLite database
- **Production**: Uses MariaDB with Docker

Key configuration options in `config.py`:
- Database connection settings
- Avatar upload settings and sizes
- Security settings
- Logging configuration

## File Structure

```
├── app/                    # Main application package
│   ├── models.py          # Database models
│   ├── user/              # User management blueprint
│   ├── users/             # Admin user management
│   ├── rating/            # Rating system blueprint
│   └── static/            # Static files and uploads
├── migrations/            # Database migrations
├── docker-compose.yml     # Docker services configuration
├── Dockerfile            # Application container definition
├── init_app.py           # Application initialization script
├── tennis.py             # Application entry point
└── config.py             # Configuration settings
```

## Security Features

- Non-root container execution
- Role-based access control
- Password hashing
- Secure file uploads
- SQL injection protection

## Support

For issues and questions:
1. Check the application logs: `docker-compose logs web`
2. Verify database connectivity: `docker-compose logs mariadb`
3. Access phpMyAdmin for database inspection

## License

[Add your license information here]