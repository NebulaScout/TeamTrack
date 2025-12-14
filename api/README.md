# API Application

This is the centralized API application for TeamTrack, providing RESTful endpoints for all business logic using Django REST Framework (DRF).

## Purpose

The `api` app serves as a dedicated layer for all REST API endpoints, separating API concerns from web/template views. This structure provides:

- **Clean separation** between API and web functionality
- **Versioning support** for API evolution without breaking changes
- **Centralized API logic** making it easier to maintain and scale
- **Clear organization** for frontend teams consuming the API

## Structure

```
api/
├── __init__.py
├── apps.py              # Django app configuration
├── urls.py              # Root API URL configuration
├── README.md            # This file
└── v1/                  # API Version 1
    ├── __init__.py
    ├── urls.py          # V1 URL routing
    └── accounts/        # Accounts API endpoints
        ├── __init__.py
        ├── serializers.py    # DRF serializers for accounts
        ├── viewsets.py       # DRF viewsets for accounts
        ├── permissions.py    # Custom permission classes
        └── urls.py           # Accounts-specific URL routing
```

## URL Routing

The API uses a hierarchical URL structure:

```
/api/                           → Root API endpoint
/api/v1/                        → Version 1 API
/api/v1/accounts/register/      → Registration endpoints
/api/v1/accounts/users/         → User management endpoints
```

### URL Flow

1. **Main URLs** (`team_track/urls.py`):

   - Routes `/api/` to `api.urls`

2. **API Root** (`api/urls.py`):

   - Routes `/api/v1/` to `api.v1.urls`

3. **Version 1** (`api/v1/urls.py`):

   - Routes `/api/v1/accounts/` to `api.v1.accounts.urls`

4. **Accounts API** (`api/v1/accounts/urls.py`):
   - Uses DRF's `DefaultRouter` to auto-generate REST endpoints
   - `/api/v1/accounts/register/` → `RegisterViewSet`
   - `/api/v1/accounts/users/` → `UserViewSet`

## Authentication

The API uses **JWT (JSON Web Token)** authentication via `djangorestframework-simplejwt`:

- **Obtain Token**: `POST /api/token/` with username/password
- **Refresh Token**: `POST /api/token/refresh/` with refresh token
- **Verify Token**: `POST /api/token/verify/` with access token

All protected endpoints require the `Authorization: Bearer <token>` header.

## Current Endpoints

### Accounts API (`/api/v1/accounts/`)

#### Registration

- **Endpoint**: `/api/v1/accounts/register/`
- **ViewSet**: `RegisterViewSet`
- **Serializer**: `RegistrationSerializer`
- **Model**: `RegisterModel` (from `accounts` app)
- **Methods**:
  - `GET` - List all registrations
  - `POST` - Create registration
  - `GET /:id/` - Retrieve specific registration
  - `PUT /:id/` - Update registration
  - `PATCH /:id/` - Partial update
  - `DELETE /:id/` - Delete registration

#### Registration Flow

1. Client sends POST request with user data
2. `RegistrationSerializer` validates nested `UserSerializer` data
3. Calls `register_user()` service from `accounts.services.registration_service`
4. Creates both `User` and `RegisterModel` instances
5. Returns created registration data

#### User Management

- **Endpoint**: `/api/v1/accounts/users/`
- **ViewSet**: `UserViewSet`
- **Serializer**: `UserSerializer`
- **Model**: `User` (Django's built-in User model)
- **Authentication**: JWT (JWTAuthentication)
- **Permissions**: `UserPermissions`
- **Methods**:
  - `GET` - List all users (admin only)
  - `POST` - Create user (any user)
  - `GET /:id/` - Retrieve specific user (authenticated users)
  - `PUT /:id/` - Update user (owner or admin)
  - `PATCH /:id/` - Partial update (owner or admin)
  - `DELETE /:id/` - Delete user (admin only)

## Permissions

The API implements custom permission classes to control access:

### UserPermissions

Controls access to user-related endpoints with the following rules:

- **List** (`GET /users/`): Admin only
- **Create** (`POST /users/`): Any user can register
- **Retrieve/Update** (`GET/PUT/PATCH /users/:id/`): Authenticated users only
- **Delete** (`DELETE /users/:id/`): Admin only
- **Object-level**: Users can only access/modify their own data unless they're staff

## Versioning Strategy

The API uses **URL-based versioning** (`/api/v1/`, `/api/v2/`, etc.):

- **v1** is the current stable version
- Future versions can be added as separate modules (`api/v2/`)
- Deprecated versions can be maintained alongside newer versions
- Clients specify version in URL, ensuring backward compatibility

## Best Practices

1. **Keep API logic separate** from web views
2. **Use serializers** for all input validation
3. **Delegate business logic** to service layers (`accounts/services/`)
4. **Use ViewSets** with routers for standard CRUD operations
5. **Version early** - easier to add v1 now than refactor later
6. **Document endpoints** as they're created
7. **Implement proper permissions** to secure endpoints
8. **Use JWT authentication** for protected resources

## Related Documentation

- [DRF Documentation](https://www.django-rest-framework.org/)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Accounts App](../accounts/README.md)
