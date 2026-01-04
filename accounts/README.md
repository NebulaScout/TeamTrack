# Accounts App

## Overview

The Accounts app is a Django application responsible for user authentication, registration, and profile management in the TeamTrack project management system. It handles user account creation and maintains user profiles with comprehensive authentication and authorization mechanisms.

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

Role-based access control architecture has been implemented with custom permission classes that define granular access control based on user authentication status and administrative privileges. The system differentiates between regular authenticated users and administrative staff for access to various operations.

**Role Management Features:**

- Users can be assigned to roles (Admin, Project Manager, Developer, Guest)
- Admin-only endpoint for assigning roles to users
- User's primary role exposed in API responses
- Role assignment via `set_user_role()` service function
- Roles are managed through Django's built-in Groups system

### User Profile Management

- One-to-one relationship between Django User and RegisterModel
- User creation timestamp tracking
- Profile data retrieval through authenticated API endpoints

## Database Models

### RegisterModel

Extended user profile model that links to Django's built-in User model:

- `user` - OneToOneField to Django User model (CASCADE delete)
- `created_at` - Automatic timestamp of account creation

**Note:** Role enumeration fields are currently commented out in the model. The role management system is under architectural review for future implementation.

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
- Fields: `id`, `username`, `first_name`, `last_name`, `email`, `password`, `confirm_password`, `role`
- **Role field**: SerializerMethod that returns the user's primary group/role name
- Password fields excluded from response output

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

### `group_assignment.py`

Service layer for user role management:

#### `set_user_role(user, role_name)`

- Assigns a user to a specific role/group
- Clears existing group memberships and sets the new role
- Raises `RuntimeError` if the specified role doesn't exist
- Used by the `assign_role` API endpoint
- Integrates with Django's built-in Groups system

## API ViewSets

### `RegisterViewSet`

Located in `api/v1/accounts/viewsets.py`:

- **Base Class:** `viewsets.ModelViewSet`
- **Queryset:** `RegisterModel.objects.all()`
- **Serializer:** `RegistrationSerializer`
- **Purpose:** Handles user registration via REST API
- **Authentication:** None (allows public registration)
- **Permissions:** Default ModelViewSet permissions

### `UserViewSet`

Located in `api/v1/accounts/viewsets.py`:

- **Base Class:** `viewsets.ModelViewSet`
- **Queryset:** `User.objects.all()`
- **Serializer:** `UserSerializer`
- **Authentication:** `JWTAuthentication`
- **Permissions:** `UserPermissions` (custom permission class)
- **Purpose:** Manages user CRUD operations with role-based access control

**Custom Actions:**

- **`GET /me/`** - Get current authenticated user's profile

  - Permissions: `IsAuthenticated`
  - Returns serialized data for the requesting user
  - Useful for fetching logged-in user's information

- **`PATCH /{id}/assign_role/`** - Assign a role to a user
  - Permissions: `IsAdminUser` (admin only)
  - Request body: `{"role": "<role_name>"}`
  - Available roles: Admin, Project Manager, Developer, Guest
  - Uses `set_user_role()` service for role assignment
  - Returns updated user data on success

### `ProfileViewSet`

Located in `api/v1/accounts/viewsets.py`:

- **Base Class:** `viewsets.ModelViewSet`
- **Queryset:** `User.objects.all()`
- **Serializer:** `UserSerializer`
- **Authentication:** `JWTAuthentication`
- **Permissions:** `UserPermissions` (custom permission class)
- **Purpose:** Handles user profile operations with authentication

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

### `utils/permissions.py`

Custom permission classes for fine-grained access control:

#### `UserPermissions`

Custom permission class that extends Django REST Framework's `BasePermission`:

- **list**: Restricted to authenticated staff/admin users only
- **create**: Open to any user (allows registration)
- **retrieve, update, partial_update**: Requires authentication
- **destroy**: Restricted to authenticated staff/admin users only
- **Object-level permissions**: Users can only access/modify their own objects or admin can access any

#### `ProjectPermissions`

Extends `UserPermissions` with project-specific access control:

- **create, list, retrieve, update, partial_update, destroy**: Requires authentication
- All other actions are denied by default

### `services/api_client.py`

Centralized API client for internal communication:

#### `APIClient` Class

Manages HTTP requests with automatic authentication and token refresh:

- **`__init__(request)`**: Initializes client with request context and base URL
- **`_get_headers()`**: Builds authorization headers with JWT access token from session
- **`\_request(method, path, **kwargs)`\*\*: Core request method that:
  - Constructs full URL from base URL and path
  - Attaches authorization headers
  - Handles 401 responses with automatic token refresh
  - Retries failed requests with refreshed token
  - Returns response object for caller to handle
- **HTTP method helpers**: `get()`, `post()`, `put()`, `patch()`, `delete()`

The APIClient eliminates code duplication by centralizing header management and token refresh logic across all web views that communicate with internal APIs.

### Web Endpoints

- `/` - Home page
- `/register/` - User registration form
- `/login/` - User login with JWT token generation
- `/logout/` - User logout
- `/profile/` - User profile view (requires authentication)

### API Endpoints

#### Registration & User Management (`/api/v1/accounts/`)

**RegisterViewSet**

- Handles user registration through REST API
- Uses `RegistrationSerializer` for data validation
- Endpoint: `/api/v1/accounts/register/`
- Queryset: `RegisterModel.objects.all()`

**UserViewSet**

- Manages user CRUD operations
- JWT authentication required
- Custom `UserPermissions` for granular access control
- Endpoint: `/api/v1/accounts/users/`
- Queryset: `User.objects.all()`
- **Custom endpoints:**
  - `GET /api/v1/accounts/users/me/` - Get current user's profile
  - `PATCH /api/v1/accounts/users/{id}/assign_role/` - Assign role to user (admin only)

**ProfileViewSet**

- Handles user profile operations
- JWT authentication required
- Custom `UserPermissions` for access control
- Endpoint: `/api/v1/accounts/profile/`
- Queryset: `User.objects.all()`

#### Token Management (`/api/token/`)

- `/api/token/` - JWT token generation (login)
- `/api/token/refresh/` - Access token refresh

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

## URL Configuration

The accounts app URL patterns are defined in `accounts/urls.py`:

```python
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
]
```

These URLs are included in the main project URL configuration.

## Technical Stack

- **Backend Framework:** Django
- **API Framework:** Django REST Framework
- **Authentication:** djangorestframework-simplejwt (JWT tokens)
- **HTTP Client:** requests library (for internal API calls)
- **Database:** Django ORM with User and RegisterModel
- **Session Management:** Django sessions for token storage

## Future Enhancements

- Add user profile editing functionality
- Add role change management capabilities for non-admin users
- Implement user deactivation/deletion workflows
- Add password reset functionality with email verification
- Enhance token security with additional token blacklisting scenarios
- Add email uniqueness constraint with proper migration handling
- Implement multi-factor authentication (MFA)
- Implement audit logging for user actions
- Add bulk role assignment functionality
