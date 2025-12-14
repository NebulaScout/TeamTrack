# Accounts App

## Overview

The Accounts app is a Django application responsible for user authentication, registration, and role management in the TeamTrack project management system. It handles user account creation with role-based assignment and maintains user profiles with role-specific access levels.

## Features

### User Authentication

- JWT-based authentication using `djangorestframework-simplejwt`
- Custom login view with automatic token generation
- Session-based token storage (access and refresh tokens)
- Token refresh mechanism for expired access tokens
- Secure logout functionality
- Login required decorator for protected views

### User Registration

- User registration with custom form handling
- Email validation and confirmation
- Secure password creation and confirmation
- Username, first name, and last name fields
- Service layer pattern for registration logic
- REST API endpoint for user registration
- Web view communicates with API endpoint for registration

### User Profile Management

- User profile view with API integration
- JWT token-based authentication for API requests
- Automatic token refresh on expiration
- Error handling for authentication failures
- Session expiration handling with redirect to login

### Architecture

- **Service Layer:** Centralized registration logic in `registration_service.py`
- **API Layer:** REST API using Django REST Framework with ViewSets
- **Web Layer:** Template-based views that consume the API
- **Authentication Layer:** JWT token management with session storage
- **Utility Layer:** Token refresh and authentication helpers in `utils/jwt.py`
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

### `CustomLoginView`

- Extends Django's built-in `LoginView`
- Generates JWT tokens upon successful authentication
- Stores access and refresh tokens in session
- Uses `AuthenticationForm` for validation
- Integrates with `/api/token/` endpoint for token generation
- Error handling for token generation failures
- Template: `accounts/login.html`

### `register(request)`

- Handles both GET and POST requests
- GET: Displays empty registration form
- POST: Sends registration data to API endpoint using internal HTTP request
- Uses `requests` library to communicate with API
- Displays success/error messages based on API response
- Redirects to login on successful registration
- Integrates with `/api/v1/accounts/register/` endpoint

### `home(request)`

- Renders the base template
- Serves as the home page view

### `user_profile(request)`

- Protected view requiring login (`@login_required`)
- Retrieves user profile data from API
- Uses JWT token from session for authentication
- Automatic token refresh on expiration
- Handles authentication errors with redirect to login
- Error handling for HTTP and connection errors
- Template: `accounts/user_profile.html`

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

## Utilities

### `utils/jwt.py`

JWT token management utilities:

#### `refresh_access_token(request)`

- Refreshes expired access tokens using refresh token
- Retrieves refresh token from session
- Calls `/api/token/refresh/` endpoint
- Updates session with new access token
- Returns new access token or `None` on failure
- Error handling for HTTP and connection errors

### Web Endpoints

- `/` - Home page
- `/register/` - User registration form
- `/login/` - User login with JWT token generation
- `/logout/` - User logout
- `/profile/` - User profile view (requires authentication)

## Security Considerations

- Uses Django's built-in `create_user()` method for secure password hashing
- JWT-based authentication with access and refresh tokens
- Session-based token storage for web views
- Automatic token refresh mechanism
- Login required decorator for protected views
- Password confirmation validation through form validation
- Write-only password fields in serializers
- Separation of concerns with service layer
- HTTP error handling for API communication

## Integration Points

- Part of the larger TeamTrack project management system
- Works with Django's authentication system
- JWT token integration with `djangorestframework-simplejwt`
- Session management for token storage
- Provides foundation for role-based access control across the application
- Templates located in `accounts/templates/accounts/`
- Static files (CSS, JS) located in `accounts/static/`
- REST API integration using Django REST Framework
- Internal API communication pattern between web and API layers
- Token-based API authentication for protected endpoints

## Technical Stack

- **Backend Framework:** Django
- **API Framework:** Django REST Framework
- **Authentication:** djangorestframework-simplejwt (JWT tokens)
- **HTTP Client:** requests library (for internal API calls)
- **Database:** Django ORM with User and RegisterModel
- **Session Management:** Django sessions for token storage

## Future Enhancements

- Add user profile editing functionality
- Re-implement role assignment during registration
- Add role change management
- Implement user deactivation/deletion
- Add password reset functionality
- Enhance token security with token blacklisting
