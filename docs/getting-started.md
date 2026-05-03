# Getting Started

## Prerequisites

- Python 3.10+
- MySQL Server
- pip
- Git

## Setup

1. Clone the repo

```bash
git clone <repository-url>
cd TeamTrack
```

2. Create and activate a virtual environment

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

Create a .env file in the project root:

```bash
touch .env
```

Example values:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
BASE_URL=http://127.0.0.1:8000

# Database Configuration
DB_NAME=teamtrack_db
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
```

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

5. Create the database

```sql
CREATE DATABASE teamtrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. Run migrations

```bash
python manage.py migrate
```

7. Initialize roles

```bash
python manage.py init_roles
```

8. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

9. Run the development server

```bash
python manage.py runserver
```

The app will be available at http://127.0.0.1:8000

## Common Tasks

- Run tests: `python manage.py test`
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
