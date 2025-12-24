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
    ├── accounts/        # Accounts API endpoints
    │   ├── __init__.py
    │   ├── serializers.py    # DRF serializers for accounts
    │   ├── viewsets.py       # DRF viewsets for accounts
    │   └── urls.py           # Accounts-specific URL routing
    ├── auth/            # Authentication API endpoints
    │   ├── viewsets.py       # DRF viewsets for auth
    │   └── urls.py           # Auth-specific URL routing
    ├── projects/        # Projects API endpoints
    │   ├── serializers.py    # DRF serializers for projects
    │   ├── viewsets.py       # DRF viewsets for projects
    │   └── urls.py           # Projects-specific URL routing
    └── tasks/           # Tasks API endpoints
        ├── serializers.py    # DRF serializers for tasks
        ├── viewsets.py       # DRF viewsets for tasks
        └── urls.py           # Tasks-specific URL routing
```

## URL Routing

The API uses a hierarchical URL structure:

```
/api/                           → Root API endpoint
/api/v1/                        → Version 1 API
/api/v1/accounts/register/      → Registration endpoints
/api/v1/accounts/users/         → User management endpoints
/api/v1/auth/                   → Authentication endpoints
/api/v1/projects/               → Project management endpoints
/api/v1/tasks/                  → Task management endpoints
```

### URL Flow

1. **Main URLs** (`team_track/urls.py`):

   - Routes `/api/` to `api.urls`

2. **API Root** (`api/urls.py`):

   - Routes `/api/v1/` to `api.v1.urls`

3. **Version 1** (`api/v1/urls.py`):

   - Routes `/api/v1/accounts/` to `api.v1.accounts.urls`
   - Routes `/api/v1/auth/` to `api.v1.auth.urls`
   - Routes `/api/v1/projects/` to `api.v1.projects.urls`
   - Routes `/api/v1/tasks/` to `api.v1.tasks.urls`

4. **Accounts API** (`api/v1/accounts/urls.py`):

   - Uses DRF's `DefaultRouter` to auto-generate REST endpoints
   - `/api/v1/accounts/register/` → `RegisterViewSet`
   - `/api/v1/accounts/users/` → `UserViewSet`

5. **Auth API** (`api/v1/auth/urls.py`):

   - Uses DRF's `DefaultRouter` to auto-generate REST endpoints
   - `/api/v1/auth/auth/logout/` → `AuthViewSet.logout`

6. **Projects API** (`api/v1/projects/urls.py`):

   - Uses DRF's `DefaultRouter` to auto-generate REST endpoints
   - `/api/v1/projects/` → `ProjectsViewSet` (registered as 'team-projects')
   - `/api/v1/projects/users/` → `UserViewSet` (extended user data with projects)

7. **Tasks API** (`api/v1/tasks/urls.py`):
   - Uses DRF's `DefaultRouter` to auto-generate REST endpoints
   - `/api/v1/tasks/` → `TaskViewSet` (registered as 'project_tasks')

## Authentication

The API uses **JWT (JSON Web Token)** authentication via `djangorestframework-simplejwt`:

- **Obtain Token**: `POST /api/token/` with username/password
- **Refresh Token**: `POST /api/token/refresh/` with refresh token
- **Verify Token**: `POST /api/token/verify/` with access token

All protected endpoints require the `Authorization: Bearer <token>` header.

## Current Endpoints

### Auth API (`/api/v1/auth/`)

#### Logout

- **Endpoint**: `/api/v1/auth/auth/logout/`
- **ViewSet**: `AuthViewSet`
- **Authentication**: JWT (JWTAuthentication)
- **Permissions**: `IsAuthenticated`
- **Methods**:
  - `POST` - Logout user by blacklisting refresh token

#### Logout Flow

1. Client sends POST request with refresh_token in request body
2. `AuthViewSet.logout` validates the refresh token
3. Blacklists the refresh token to revoke access
4. Returns success message

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

### Projects API (`/api/v1/projects/`)

#### Project Management

- **Endpoint**: `/api/v1/projects/`
- **ViewSet**: `ProjectsViewSet`
- **Serializer**: `ProjectsSerializer`
- **Model**: `ProjectsModel` (from `projects` app)
- **Authentication**: JWT (JWTAuthentication)
- **Permissions**: `ProjectPermissions`
- **Methods**:
  - `GET` - List all projects (authenticated users)
  - `POST` - Create project (authenticated users, automatically sets created_by to current user)
  - `GET /:id/` - Retrieve specific project (authenticated users)
  - `PUT /:id/` - Update project (authenticated users)
  - `PATCH /:id/` - Partial update (authenticated users)
  - `DELETE /:id/` - Delete project (authenticated users)

#### Extended User Data

- **Endpoint**: `/api/v1/projects/users/`
- **ViewSet**: `UserViewSet`
- **Serializer**: `ExtendedUserSerializer`
- **Model**: `User` (Django's built-in User model)
- **Methods**: Full CRUD operations with user data including related projects
- **Special Feature**: Includes projects relationship to show all projects created by each user

### Tasks API (`/api/v1/tasks/`)

#### Task Management

- **Endpoint**: `/api/v1/tasks/`
- **ViewSet**: `TaskViewSet`
- **Serializer**: `TaskSerializer`
- **Model**: `TaskModel` (from `tasks` app)
- **Authentication**: JWT (JWTAuthentication)
- **Permissions**: `TaskPermissions`
- **Methods**:
  - `GET` - List tasks (filtered to tasks created by or assigned to the current user)
  - `POST` - Create task (automatically sets created_by to current user)
  - `GET /:id/` - Retrieve specific task
  - `PUT /:id/` - Update task
  - `PATCH /:id/` - Partial update
  - `DELETE /:id/` - Delete task

#### Task Custom Actions

- **Assign Task**: `PATCH /api/v1/tasks/:id/assign/`
  - Assigns a task to a specific user
  - Request body: `{"assigned_to": <user_id>}`
  - Automatically tracks assignment change in task history
- **Update Status**: `PATCH /api/v1/tasks/:id/status/`
  - Updates task status
  - Request body: `{"status": "<status_value>"}`
  - Automatically tracks status change in task history
- **Update Priority**: `PATCH /api/v1/tasks/:id/priority/`

  - Updates task priority
  - Request body: `{"priority": "<priority_value>"}`
  - Automatically tracks priority change in task history

- **Task Comments**: `/api/v1/tasks/:id/comments/`

  - `POST` - Create comment on task
  - `GET` - List all comments for task
  - Request body (POST): `{"content": "<comment_text>"}`
  - Automatically sets author to current user
  - Optimized query with `select_related('author')`

- **Task History/Logs**: `GET /api/v1/tasks/:id/logs/`
  - Retrieves complete change history for a task
  - Shows all modifications with timestamps and users
  - Provides full audit trail of task changes

#### Task Query Optimization

The `TaskViewSet` uses optimized queries with:

- `prefetch_related('project')` - Reduces database queries for related projects
- `select_related('created_by')` - Optimizes user lookups
- Filters tasks to only show those created by or assigned to the current user

## Serializers

The API implements several serializers for data validation and transformation:

### RegistrationSerializer

Handles user registration with nested user creation:

- Validates registration data
- Contains nested `UserSerializer` for user account creation
- Delegates to `register_user()` service for atomic user creation

### UserSerializer

Basic user data serialization:

- Fields: `id`, `username`, `email`, `first_name`, `last_name`
- Used for user account data in accounts endpoints

### ExtendedUserSerializer

Extended user data with relationships:

- Extends `UserSerializer`
- Includes `projects` relationship showing all projects created by the user
- Used in Projects API's user endpoints

### ProjectsSerializer

Handles project data:

- Fields: `id`, `project_name`, `description`, `start_date`, `end_date`, `created_by`, `created_at`
- Uses `HiddenField` for `created_by` to automatically set from request.user
- Validates project data against `ProjectsModel`
- Integrated with `ProjectService` for business logic during project creation

### TaskSerializer

Handles task data with nested relationships:

- Fields: All fields from `TaskModel`
- Read-only fields: `id`, `created_by`, `created_at`, `project`, `comments`, `history`
- Nested `comments` - All comments associated with the task
- Nested `history` - Complete change history for the task
- Validates task data against `TaskModel`
- Uses `EnumField` for status and priority enumerations

### CommentSerializer

Handles comment data:

- Fields: `id`, `task`, `author`, `content`, `created_at`
- Read-only fields: `id`, `created_at`, `author`, `task`
- Validates comment data against `CommentModel`
- Automatically sets author from request.user

### TaskHistorySerializer

Handles task change history:

- Fields: All fields from `TaskHistoryModel`
- Read-only fields: `id`, `task`, `changed_by`, `timestamp`
- Tracks field changes with old and new values
- Provides audit trail for task modifications

### ExtendedUserSerializer (Tasks)

Extended user data with task relationships:

- Extends `UserSerializer`
- Includes `user_assigned_tasks` showing all tasks assigned to the user
- Includes `created_tasks` showing all tasks created by the user
- Includes `author_of_comment` showing all comments authored by the user
- Includes `task_changes` showing all task changes made by the user
- Provides comprehensive user activity tracking

## Permissions

The API implements custom permission classes to control access:

### UserPermissions

Controls access to user-related endpoints with the following rules:

- **List** (`GET /users/`): Admin only
- **Create** (`POST /users/`): Any user can register
- **Retrieve/Update** (`GET/PUT/PATCH /users/:id/`): Authenticated users only
- **Delete** (`DELETE /users/:id/`): Admin only
- **Object-level**: Users can only access/modify their own data unless they're staff

### ProjectPermissions

Controls access to project-related endpoints:

- **Extends** `UserPermissions` for base permission logic
- **All CRUD operations**: Require authentication (list, create, retrieve, update, partial_update, destroy)
- **Implementation**: Located in `core/services/permissions.py`
- **Applied to**: `ProjectsViewSet` for authenticated-only access

### TaskPermissions

Controls access to task-related endpoints:

- **All CRUD operations**: Require authentication
- **Query filtering**: Users can only access tasks they created or are assigned to
- **Custom actions**: Assignment, status, priority, comments, and logs require authentication
- **Implementation**: Located in `core/services/permissions.py`
- **Applied to**: `TaskViewSet` for authenticated and filtered access

## Versioning Strategy

The API uses **URL-based versioning** (`/api/v1/`, `/api/v2/`, etc.):

- **v1** is the current stable version
- Future versions can be added as separate modules (`api/v2/`)
- Deprecated versions can be maintained alongside newer versions
- Clients specify version in URL, ensuring backward compatibility

## Best Practices

1. **Keep API logic separate** from web views
2. **Use serializers** for all input validation
3. **Delegate business logic** to service layers (`core/services/`)
4. **Use ViewSets** with routers for standard CRUD operations
5. **Version early** - easier to add v1 now than refactor later
6. **Document endpoints** as they're created
7. **Implement proper permissions** to secure endpoints
8. **Use JWT authentication** for protected resources
9. **Track changes** automatically through service layer for audit trails
10. **Use nested serializers** for related data to reduce API calls
11. **Optimize queries** with prefetch_related and select_related

## Related Documentation

- [DRF Documentation](https://www.django-rest-framework.org/)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Accounts App](../accounts/README.md)
