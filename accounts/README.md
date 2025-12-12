# Accounts App

## Overview

The Accounts app is a Django application responsible for user authentication, registration, and role management in the TeamTrack project management system. It handles user account creation with role-based assignment and maintains user profiles with role-specific access levels.

## Features

### User Registration

- User registration with custom form handling
- Email validation and confirmation
- Secure password creation and confirmation
- Username, first name, and last name fields
- Service layer pattern for registration logic
- REST API endpoint for user registration
- Web view communicates with API endpoint for registration

### Architecture

- **Service Layer:** Centralized registration logic in `registration_service.py`
- **API Layer:** REST API using Django REST Framework with ViewSets
- **Web Layer:** Template-based views that consume the API
- **Separation of Concerns:** Clear distinction between API and web views

### Role-Based Access Control

The app supports four user roles:

- **Admin (ADMIN)** - Full system access and administration capabilities
- **Project Manager (PM)** - Project oversight and team management
- **Developer (DEV)** - Development and task execution
- **Guest (GT)** - Limited access (previously Stakeholder)

### User Profile Management

- One-to-one relationship between Django User and RegisterModel
- Automatic role assignment during registration
- User creation timestamp tracking

## Database Models

### RegisterModel

Extended user profile model that links to Django's built-in User model:

- `user` - OneToOneField to Django User model (CASCADE delete)
- `created_at` - Automatic timestamp of account creation

## Views

The views are now organized into separate modules:

### Web Views (`views/web.py`)

#### `register(request)`

- Handles both GET and POST requests
- GET: Displays empty registration form
- POST: Sends registration data to API endpoint using internal HTTP request
- Uses `requests` library to communicate with API
- Displays success/error messages based on API response
- Redirects to home on successful registration
- CSRF protection disabled (marked with `@csrf_exempt` decorator)

#### `home(request)`

- Renders the base template
- Serves as the home page view

### API Views (`views/api.py`)

#### `RegisterViewSet`

- REST API ViewSet for user registration
- Extends `ModelViewSet` from Django REST Framework
- Provides full CRUD operations for RegisterModel
- Uses `RegistrationSerializer` for data validation and processing
- Accessible via `/accounts/api/register/` endpoint

## Forms

### RegistrationForm

- **Fields:** username, first_name, last_name, email, password, confirm_password
- **Validation:** Custom password confirmation validation in `clean()` method
- Password mismatch error handling

## Serializers

### UserSerializer

- Handles User model serialization
- Write-only password fields for security
- Fields: username, first_name, last_name, email, password, confirm_password

### RegistrationSerializer

- Handles RegisterModel serialization
- Nested `UserSerializer` for user data
- Custom `create()` method that delegates to registration service
- Returns all RegisterModel fields

## Services

### `registration_service.py`

Service layer for registration business logic:

#### `register_user(username, first_name, last_name, email, password)`

- Creates Django User instance using `create_user()` method
- Automatically creates associated RegisterModel instance
- Returns the created RegisterModel
- Provides centralized registration logic used by both API and web views

## URL Configuration

The app now provides both web and API endpoints:

### Web Endpoints

- `/` - Home page
- `/register/` - User registration form

### API Endpoints

- `/api/register/` - RESTful registration endpoint (ViewSet with full CRUD)

## Security Considerations

- Uses Django's built-in `create_user()` method for secure password hashing
- Implements CSRF protection (currently disabled on register endpoint for testing)
- Password confirmation validation through form validation
- Write-only password fields in serializers
- Separation of concerns with service layer

## Integration Points

- Part of the larger TeamTrack project management system
- Works with Django's authentication system
- Provides foundation for role-based access control across the application
- Templates located in `accounts/templates/accounts/`
- Static files (CSS, JS) located in `accounts/static/`
- REST API integration using Django REST Framework
- Internal API communication pattern between web and API layers

## Technical Stack

- **Backend Framework:** Django
- **API Framework:** Django REST Framework
- **HTTP Client:** requests library (for internal API calls)
- **Database:** Django ORM with User and RegisterModel

## Future Enhancements

- Enable CSRF protection on production
- Add user profile editing functionality
- ~~Implement REST API endpoints for registration~~ ✅ **COMPLETED**
- Re-implement role assignment during registration
- Add role change management
- Implement user deactivation/deletion
- Add API authentication and permissions
- Implement token-based authentication for API endpoints
