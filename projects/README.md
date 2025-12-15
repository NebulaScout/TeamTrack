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
   - Converts date fields to ISO format for API compatibility
   - Sends data to REST API via `APIClient`
   - Handles success/error responses with Django messages

**API Integration:**

- Endpoint: `POST /api/v1/projects/`
- Authentication: Handled by `APIClient` (JWT tokens)
- Automatic token refresh on authentication failure

**Error Handling:**

- Form validation errors displayed in template
- HTTP errors caught and displayed via messages framework
- Connection errors handled gracefully with user feedback

**Dependencies:**

- `requests` library for HTTP communication
- `APIClient` from `services.api_client`
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

## API Integration

The projects app integrates with the REST API layer:

**API Endpoints Used:**

- `POST /api/v1/projects/` - Create project via API

**APIClient Features:**

- Automatic JWT token management
- Token refresh on expiration
- Request/response handling
- Error propagation to view layer

**Data Flow:**

1. User submits form via web interface
2. View validates form data
3. View sends data to REST API via APIClient
4. API creates project in database
5. Response returned to view
6. Success/error message displayed to user

## Architecture

The projects app follows a hybrid architecture:

**Web Layer:**

- Traditional Django forms and views for user interaction
- Template rendering for HTML responses
- Login-required authentication

**API Layer:**

- REST API endpoints in `api/v1/projects/`
- ProjectsViewSet for CRUD operations
- ProjectsSerializer for data validation
- JWT authentication support

**Service Integration:**

- APIClient abstracts HTTP communication
- Centralized API base URL configuration
- Automatic authentication handling

**Benefits:**

- Separation of concerns between web and API
- Reusable API for frontend frameworks
- Consistent data validation across layers
- Easy testing of individual components

## Important Notes

- All project creation flows through the REST API
- Authentication required for all operations
- Unique constraint enforced on project names
- Dates automatically converted to ISO format for API
- Created_by field set automatically by API using request.user
- Form validation occurs at both form and model levels
