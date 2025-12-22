# Projects App

The `projects` Django app manages project creation and tracking within TeamTrack. This app provides both web-based forms and REST API integration for project management.

## Purpose

The projects app handles all project-related functionality:

- **Project creation** through web forms
- **Project data modeling** with user relationships
- **API integration** for project persistence
- **Form validation** for project data
- **Template rendering** for project management pages

## Models

### ProjectsModel

The core model for project data storage:

**Fields:**

- `project_name`: Unique project identifier (max 100 characters, required)
- `description`: Detailed project description (text field)
- `start_date`: Project start date (defaults to current date)
- `end_date`: Project completion date (required)
- `created_by`: ForeignKey to Django User model with CASCADE deletion
- `created_at`: Automatic timestamp for project creation

**Relationships:**

- Related to `User` model via `created_by` field
- Reverse relationship accessible via `user.projects.all()`
- Related to `ProjectMembers` via `members` reverse relationship

**Custom Permissions:**

- `assign_project`: Can assign a project to users
- `add_members`: Can add a user to a project

### ProjectMembers

Manages project membership and user roles within projects:

**Fields:**

- `project`: ForeignKey to `ProjectsModel` with CASCADE deletion
- `project_member`: ForeignKey to Django User model with CASCADE deletion
- `role_in_project`: CharField with role choices (max 50 characters, defaults to 'Guest')

**Role Choices:**

Dynamically generated from `ROLE_PERMISSIONS` defined in `core.services.roles`

**Constraints:**

- `unique_together`: ('project', 'project_member') - A user can only be added once per project

**Relationships:**

- Related to `ProjectsModel` via `project` field (reverse: `project.members.all()`)
- Related to `User` model via `project_member` field (reverse: `user.project_memberships.all()`)

## Forms

### ProjectCreationForm

ModelForm for project creation:

**Features:**

- Inherits validation from `ProjectsModel`
- Custom date widgets with HTML5 date input type
- Handles all required fields for project creation
- Automatically validates unique project names
- Provides error messages for invalid data

**Previous Implementation:**

- Commented-out version used `forms.Form` instead of ModelForm
- Migrated to ModelForm for better integration with model validation

## Views

### create_project

Login-required view for project creation:

**Request Flow:**

1. **GET Request:**

   - Instantiates empty `ProjectCreationForm`
   - Renders `create_project.html` template

2. **POST Request:**
   - Validates form data via `form.is_valid()`
   - Calls `ProjectService.create_project()` with user and validated data
   - Displays success message upon completion
   - Reinitializes form for additional project creation

**Service Integration:**

- Uses `ProjectService.create_project()` from `core.services.project_service`
- Automatically creates project with current user as creator
- Automatically adds creator as project member with "Project Manager" role

**Error Handling:**

- Form validation errors displayed in template
- Database errors handled by Django's ORM
- User feedback provided via messages framework

**Dependencies:**

- `ProjectCreationForm` for data validation
- `ProjectService` from `core.services.project_service`
- `login_required` decorator for authentication
- Django messages framework for user feedback

## URL Configuration

**Routes:**

- `/projects/create/` → `create_project` view (named: `add_new_project`)

**Integration:**

- Included in main `team_track/urls.py` under `/projects/` prefix
- All routes require authentication via `@login_required` decorator

## Templates

### create_project.html

Project creation form template located at `templates/projects/create_project.html`:

**User Experience:**

- Real-time validation feedback
- Clear error messages for invalid inputs
- Success confirmation after project creation
- Date picker widgets for date fields

## Service Layer Integration

The projects app uses a service layer pattern for business logic:

**ProjectService Methods:**

- `create_project(user, data)` - Creates project and assigns creator as Project Manager

**Service Features:**

- Atomic project and membership creation
- Automatic role assignment for project creators
- Centralized business logic separate from views
- Reusable across web and API layers

**Data Flow:**

1. User submits form via web interface
2. View validates form data
3. View calls `ProjectService.create_project()`
4. Service creates `ProjectsModel` instance
5. Service creates `ProjectMembers` instance with "Project Manager" role
6. Success message displayed to user

## Architecture

The projects app follows a service-oriented architecture:

**Web Layer:**

- Traditional Django forms and views for user interaction
- Template rendering for HTML responses
- Login-required authentication

**Service Layer:**

- `ProjectService` in `core/services/project_service.py`
- Centralized business logic for project operations
- Atomic operations for related model creation
- Role-based membership assignment

**API Layer:**

- REST API endpoints in `api/v1/projects/`
- `ProjectsViewSet` for CRUD operations
- `ProjectsSerializer` for data validation
- JWT authentication support

**Benefits:**

- Separation of concerns between web, service, and API layers
- Reusable service logic across web views and API endpoints
- Consistent business rules across all access points
- Easy testing of individual components
- Atomic operations ensure data integrity

## Important Notes

- All project creation uses `ProjectService` for consistent business logic
- Authentication required for all operations
- Unique constraint enforced on project names
- Project creators automatically assigned "Project Manager" role
- `ProjectMembers` record created for every project creator
- Users can only be added once per project (unique_together constraint)
- Form validation occurs at both form and model levels
- Custom permissions available for project assignment and member management
