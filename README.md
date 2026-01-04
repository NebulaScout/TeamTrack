# TeamTrack

A Django-based project management and team collaboration platform with REST API support, JWT authentication, and role-based access control.

## Features

- **User Authentication**: Secure login/registration with JWT token-based authentication
- **Project Management**: Create and manage projects with team members
- **Task Management**: Create, assign, and track tasks within projects
- **Role-Based Access Control**: Configurable roles and permissions
- **REST API**: Full-featured API (v1) for integration with other services

## Tech Stack

- **Backend**: Django 5.2, Django REST Framework
- **Database**: MySQL
- **Authentication**: JWT (Simple JWT)
- **Environment Management**: django-environ

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10 or higher
- MySQL Server
- pip (Python package manager)
- Git

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd TeamTrack
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
touch .env
```

Add the following environment variables to the `.env` file:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True # Set to False in production
BASE_URL=http://127.0.0.1:8000

# Database Configuration
DB_NAME=teamtrack_db
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
```

> **Note**: Generate a secure `SECRET_KEY` using:
>
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### 5. Set Up the Database

Create the MySQL database:

```sql
CREATE DATABASE teamtrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run migrations to create the database tables:

```bash
python manage.py migrate
```

### 6. Initialize Roles

Set up default roles and permissions:

```bash
python manage.py init_roles
```

### 7. Create a Superuser (Optional)

Create an admin account to access the Django admin panel:

```bash
python manage.py createsuperuser
```

### 8. Run the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000`

## Project Structure

```
TeamTrack/
├── accounts/          # User authentication and profiles
├── api/               # REST API configuration
│   └── v1/            # API version 1
│       ├── accounts/  # Account-related endpoints
│       ├── auth/      # Authentication endpoints
│       ├── projects/  # Project endpoints
│       └── tasks/     # Task endpoints
├── core/              # Core services and utilities
│   ├── management/    # Custom management commands
│   └── services/      # Business logic services
├── projects/          # Project management module
├── tasks/             # Task management module
├── team_track/        # Django project settings
├── templates/         # HTML templates
└── utils/             # Utility functions
```

## API Endpoints

### Authentication

| Method | Endpoint              | Description           |
| ------ | --------------------- | --------------------- |
| POST   | `/api/token/`         | Obtain JWT token pair |
| POST   | `/api/token/refresh/` | Refresh access token  |
| POST   | `/api/token/verify/`  | Verify token validity |

### API v1

- `/api/v1/accounts/` - Account management
- `/api/v1/projects/` - Project CRUD operations
- `/api/v1/tasks/` - Task CRUD operations

## Development

### Running Tests

```bash
python manage.py test
```

### Making Migrations

After modifying models, create and apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Code Style

Follow PEP 8 guidelines for Python code style.

## Production Deployment Notes

For production deployment:

1. Set `DEBUG=False` in your `.env` file
2. Configure a proper `SECRET_KEY`
3. Set up HTTPS (SSL/TLS certificates)
4. Configure allowed hosts in `settings.py`
5. Use a production-grade web server (e.g., Gunicorn + Nginx)
6. Set up proper database backups

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature-name`)
5. Open a Pull Request
