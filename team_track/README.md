# TeamTrack

TeamTrack is a Collaborative Task Scheduling and Tracking System (CTSTS) designed to help software engineering teams organize projects, assign work, monitor progress, and stay aligned.

## Overview

TeamTrack is built with Django and Django REST Framework, providing both web-based views and a RESTful API for managing team collaboration. The application follows a clean architecture with separation between API and web layers, enabling flexible integration with frontend applications while maintaining traditional server-rendered views.

### Current Features

**User Authentication & Management**

- JWT-based authentication with access and refresh tokens
- User registration with email validation
- Secure login/logout functionality
- User profile management with API integration
- Automatic token refresh mechanism
- Role-based permissions for access control

**Project Management**

- Create, update, and manage projects through web forms and API
- Automatic project ownership assignment
- Project member management with role-based access
- Automatic "Project Manager" role assignment for project creators
- Unique project name constraints
- Custom permissions for project assignment and member management
- Service layer integration for project operations
- Authentication required for all project operations

**Task Management**

- Create, assign, and track tasks within projects
- Task status tracking (OPEN, IN_PROGRESS, DONE)
- Task priority management (LOW, MEDIUM, HIGH)
- Automatic task filtering by user (created or assigned)
- Custom API actions for task assignment, status, and priority updates
- Due date tracking and management
- Service layer integration for task operations
- Optimized queries with prefetch and select related

**Task Comments**

- Add comments to tasks for team collaboration
- View all comments on a task via API
- Comment authorship tracking
- Automatic timestamp recording

**Task History & Audit Trail**

- Automatic tracking of all task changes
- Tracks changes to: status, priority, assigned user, due date, title, description
- Records old and new values for each change
- Timestamps and user attribution for all modifications
- View task change history via `/api/v1/tasks/{id}/logs/` endpoint

**REST API**

- Versioned API structure (`/api/v1/`)
- User management endpoints with role-based permissions
- Project management endpoints with full CRUD operations
- Task management endpoints with custom actions
- Authentication endpoints with logout and token blacklisting
- Registration endpoints
- JWT token generation, refresh, and verification endpoints
- Custom permission classes for granular access control
- Extended user data with project and task relationships
- User-filtered queries for enhanced security

**Architecture**

- Service layer pattern for business logic
- Service-oriented design with reusable business logic
- API-first design for tasks, hybrid approach for projects
- Session-based token storage for web views
- Modular app structure (accounts, projects, tasks, api, core)
- Centralized service layer in core app
- Enum-based validation for structured data (status, priority)
- Optimized database queries for performance

### Technology Stack

- **Backend:** Django 6.0
- **API Framework:** Django REST Framework
- **Authentication:** djangorestframework-simplejwt (with token blacklisting)
- **Database:** Django ORM
- **Enumerations:** django-enum
- **Environment Management:** django-environ

### Project Structure

```
TeamTrack/
├── accounts/          # User authentication and management
├── api/              # RESTful API endpoints (versioned)
│   └── v1/           # API version 1
│       ├── accounts/ # User and registration API
│       ├── auth/     # Authentication API (logout)
│       ├── projects/ # Project management API
│       └── tasks/    # Task management API
├── projects/         # Project management functionality
├── tasks/            # Task management functionality
├── core/             # Shared services and utilities
│   ├── services/     # Business logic layer
│   │   ├── project_service.py
│   │   ├── task_service.py
│   │   ├── permissions.py
│   │   ├── roles.py
│   │   └── enums.py
│   └── management/   # Custom management commands
├── utils/            # Helper functions (JWT)
├── templates/        # HTML templates
└── team_track/       # Django project settings
```

### Key Components

**Models:**

- `User` - Django's built-in user model
- `RegisterModel` - User registration tracking
- `ProjectsModel` - Project data and relationships
- `ProjectMembers` - Project membership with roles
- `TaskModel` - Task data with status and priority
- `CommentModel` - Task comments with author tracking
- `TaskHistoryModel` - Audit trail for task changes

**Services:**

- `ProjectService` - Project creation and member management
- `TaskService` - Task CRUD, assignment, status, and priority updates
- `CommentService` - Comment creation and management
- `RegistrationService` - User registration workflows

**Enumerations:**

- `StatusEnum` - Task status values (OPEN, IN_PROGRESS, DONE)
- `PriorityEnum` - Task priority values (LOW, MEDIUM, HIGH)
- `TaskFieldEnum` - Tracked task fields for audit history (status, priority, assigned_to, due_date, title, description)

**Permissions:**

- `UserPermissions` - User access control
- `ProjectPermissions` - Project access control
- `TaskPermissions` - Task access control with user filtering

For detailed documentation on specific components:

- [Accounts App Documentation](accounts/README.md)
- [API Documentation](api/README.md)
- [Projects App Documentation](projects/README.md)
- [Tasks App Documentation](tasks/README.md)
