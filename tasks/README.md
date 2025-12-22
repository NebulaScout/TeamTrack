# Tasks App

The `tasks` Django app manages task creation, assignment, and tracking within TeamTrack projects. This app provides REST API integration for comprehensive task management across project workflows.

## Purpose

The tasks app handles all task-related functionality:

- **Task creation** within projects
- **Task assignment** to team members
- **Status tracking** through task lifecycle
- **Priority management** for task organization
- **API-only access** through REST endpoints
- **User-filtered queries** for task visibility

## Models

### TaskModel

The core model for task data storage:

**Fields:**

- `project`: ForeignKey to `ProjectsModel` with CASCADE deletion (required)
- `title`: Task title (max 100 characters)
- `description`: Detailed task description (text field)
- `assigned_to`: ForeignKey to User model with SET_NULL on deletion (nullable)
- `status`: EnumField using `StatusEnum` (nullable, optional)
- `priority`: EnumField using `PriorityEnum` (nullable, optional)
- `due_date`: Task deadline date (required)
- `created_by`: ForeignKey to User model with SET_NULL on deletion (nullable)
- `created_at`: Automatic timestamp for task creation

**Relationships:**

- Related to `ProjectsModel` via `project` field (reverse: `project.project_tasks.all()`)
- Related to `User` model via `assigned_to` field (reverse: `user.assigned_tasks.all()`)
- Related to `User` model via `created_by` field (reverse: `user.created_tasks.all()`)

**Enumerations:**

Tasks use two custom enum types for structured data:

- `StatusEnum`: OPEN, IN_PROGRESS, DONE
- `PriorityEnum`: LOW, MEDIUM, HIGH

Both enums are defined in `core.services.enums` using Django's `TextChoices`.

## Service Layer

### TaskService

Centralized business logic for task operations in `core/services/task_service.py`:

#### create_task(user, project_id, data)

Creates a task within a project:

- **Parameters:**
  - `user`: Current authenticated user (set as task creator)
  - `project_id`: ID of the project to associate with the task
  - `data`: Validated task data (title, description, due_date, etc.)
- **Returns:** Created `TaskModel` instance
- **Process:**
  1. Fetches `ProjectsModel` instance by project_id
  2. Creates task with project relationship
  3. Sets `created_by` to current user

#### update_task(task_id, data)

Updates an existing task with new data:

- **Parameters:**
  - `task_id`: ID of the task to update
  - `data`: Dictionary of fields to update
- **Returns:** Updated `TaskModel` instance
- **Process:** Iterates through data and sets attributes dynamically

#### assign_task(task_id, assigned_to_id)

Assigns a task to a specific user:

- **Parameters:**
  - `task_id`: ID of the task to assign
  - `assigned_to_id`: ID of the user to assign the task to
- **Returns:** Updated `TaskModel` instance
- **Process:**
  1. Fetches task and user instances
  2. Sets `assigned_to` field
  3. Saves task

#### update_task_status(task_id, status)

Updates the status of a task:

- **Parameters:**
  - `task_id`: ID of the task to update
  - `status`: Status value from `StatusEnum`
- **Returns:** Updated `TaskModel` instance
- **Process:** Updates and saves status field

#### update_task_priority(task_id, priority)

Updates the priority of a task:

- **Parameters:**
  - `task_id`: ID of the task to update
  - `priority`: Priority value from `PriorityEnum`
- **Returns:** Updated `TaskModel` instance
- **Process:** Updates and saves priority field

## API Integration

The tasks app is primarily accessed through REST API endpoints:

**API Endpoints:**

- `GET /api/v1/tasks/` - List tasks (filtered to user's tasks)
- `POST /api/v1/tasks/` - Create task
- `GET /api/v1/tasks/:id/` - Retrieve specific task
- `PUT /api/v1/tasks/:id/` - Update task
- `PATCH /api/v1/tasks/:id/` - Partial update task
- `DELETE /api/v1/tasks/:id/` - Delete task
- `PATCH /api/v1/tasks/:id/assign/` - Assign task to user
- `PATCH /api/v1/tasks/:id/status/` - Update task status
- `PATCH /api/v1/tasks/:id/priority/` - Update task priority

**API Features:**

- JWT authentication required for all operations
- User-filtered queries (only shows tasks created by or assigned to current user)
- Custom actions for assignment, status, and priority updates
- Optimized queries with `prefetch_related` and `select_related`

**Serializers:**

- `TaskSerializer`: Handles task data validation and serialization
- `ExtendedUserSerializer`: Includes user's assigned and created tasks

**Permissions:**

- `TaskPermissions`: Controls access to task operations
- All CRUD operations require authentication
- Query filtering ensures users only access relevant tasks

## Architecture

The tasks app follows a service-oriented, API-first architecture:

**Service Layer:**

- `TaskService` in `core/services/task_service.py`
- Centralized business logic for all task operations
- Reusable methods across API endpoints
- Atomic operations with proper error handling

**API Layer:**

- REST API endpoints in `api/v1/tasks/`
- `TaskViewSet` for CRUD operations and custom actions
- `TaskSerializer` for data validation
- JWT authentication and custom permissions
- Optimized database queries for performance

**Data Layer:**

- `TaskModel` with relationships to projects and users
- Enum-based status and priority fields
- Automatic timestamp tracking
- Cascade and SET_NULL deletion behaviors

**Benefits:**

- API-first design for frontend flexibility
- Consistent business logic through service layer
- Efficient queries with proper optimization
- User-scoped data access for security
- Extensible custom actions for task workflows

## Enumerations

### StatusEnum

Defines task lifecycle states:

- **OPEN**: Task is created but not started
- **IN_PROGRESS**: Task is currently being worked on
- **DONE**: Task is completed

### PriorityEnum

Defines task importance levels:

- **LOW**: Low priority task
- **MEDIUM**: Medium priority task
- **HIGH**: High priority task

Both enums use Django's `TextChoices` for database storage and validation.

## Important Notes

- Tasks app has no web views - accessed exclusively through REST API - for now atleast:)
- All task operations use `TaskService` for consistent business logic
- Tasks are automatically filtered by user (created_by or assigned_to)
- JWT authentication required for all operations
- Task creators are automatically set from `request.user`
- Status and priority use enum validation for data integrity
- Tasks cascade delete when parent project is deleted
- Task assignments use SET_NULL to preserve task history if user is deleted
- Custom actions provide specialized endpoints for common workflows
- Optimized queries prevent N+1 problems with related data
