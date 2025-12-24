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
- `due_date`: Task deadline date (nullable, optional)
- `created_by`: ForeignKey to User model with SET_NULL on deletion (nullable)
- `created_at`: Automatic timestamp for task creation
- `updated_at`: Automatic timestamp updated on every save

**Relationships:**

- Related to `ProjectsModel` via `project` field (reverse: `project.project_tasks.all()`)
- Related to `User` model via `assigned_to` field (reverse: `user.assigned_tasks.all()`)
- Related to `User` model via `created_by` field (reverse: `user.created_tasks.all()`)
- Related to `CommentModel` via `comments` reverse relationship
- Related to `TaskHistoryModel` via `history` reverse relationship

**Enumerations:**

Tasks use custom enum types for structured data:

- `StatusEnum`: OPEN, IN_PROGRESS, DONE
- `PriorityEnum`: LOW, MEDIUM, HIGH

Both enums are defined in `core.services.enums` using Django's `TextChoices`.

### CommentModel

Manages comments and discussions on tasks:

**Fields:**
`

- `task`: ForeignKey to `TaskModel` with CASCADE deletion (required)
- `author`: ForeignKey to User model with SET_NULL on deletion (nullable)
- `content`: Comment text content (text field, required)
- `created_at`: Automatic timestamp for comment creation

**Relationships:**

- Related to `TaskModel` via `task` field (reverse: `task.comments.all()`)
- Related to `User` model via `author` field (reverse: `user.task_comments.all()`)

### TaskHistoryModel

Tracks all changes made to tasks for audit trail:

**Fields:**

- `task`: ForeignKey to `TaskModel` with SET_NULL on deletion (nullable)
- `changed_by`: ForeignKey to User model with SET_NULL on deletion (nullable)
- `field_changed`: EnumField using `TaskFieldEnum` (required)
- `old_value`: Previous field value (text field, nullable)
- `new_value`: Updated field value (text field, required)
- `timestamp`: Timestamp of change (defaults to current time)

**Relationships:**

- Related to `TaskModel` via `task` field (reverse: `task.history.all()`)
- Related to `User` model via `changed_by` field (reverse: `user.task_changes.all()`)

**Tracked Fields:**

Changes are tracked for these fields (defined in `TaskFieldEnum`):

- Status
- Priority
- Assigned To
- Due Date
- Title
- Description

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

#### update_task(user, task_id, data)

Updates an existing task with change tracking:

- **Parameters:**
  - `user`: User making the change (for history tracking)
  - `task_id`: ID of the task to update
  - `data`: Dictionary of fields to update
- **Returns:** Updated `TaskModel` instance
- **Process:**
  1. Iterates through data and checks if field is tracked
  2. Creates `TaskHistoryModel` entry for tracked fields
  3. Sets attributes dynamically
  4. Saves task

#### assign_task(altered_by, task_id, assigned_to_id)

Assigns a task to a specific user with change tracking:

- **Parameters:**
  - `altered_by`: User performing the assignment (for history tracking)
  - `task_id`: ID of the task to assign
  - `assigned_to_id`: ID of the user to assign the task to
- **Returns:** Updated `TaskModel` instance
- **Process:**
  1. Fetches task and user instances
  2. Checks if assignee is different from current
  3. Creates `TaskHistoryModel` entry if changed
  4. Sets `assigned_to` field
  5. Saves task

#### update_task_status(user, task_id, status)

Updates the status of a task with change tracking:

- **Parameters:**
  - `user`: User making the change (for history tracking)
  - `task_id`: ID of the task to update
  - `status`: Status value from `StatusEnum`
- **Returns:** Updated `TaskModel` instance
- **Process:**
  1. Checks if status is different from current
  2. Creates `TaskHistoryModel` entry if changed
  3. Updates and saves status field

#### update_task_priority(user, task_id, priority)

Updates the priority of a task with change tracking:

- **Parameters:**
  - `user`: User making the change (for history tracking)
  - `task_id`: ID of the task to update
  - `priority`: Priority value from `PriorityEnum`
- **Returns:** Updated `TaskModel` instance
- **Process:**
  1. Checks if priority is different from current
  2. Creates `TaskHistoryModel` entry if changed
  3. Updates and saves priority field

### CommentService

Centralized business logic for comment operations in `core/services/task_service.py`:

#### create_comment(user, task, data)

Creates a comment on a task:

- **Parameters:**
  - `user`: Current authenticated user (set as comment author)
  - `task`: TaskModel instance to comment on
  - `data`: Validated comment data (content)
- **Returns:** Created `CommentModel` instance
- **Process:**
  1. Fetches `TaskModel` instance
  2. Creates comment with task relationship
  3. Sets `author` to current user

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
- `POST /api/v1/tasks/:id/comments/` - Create comment on task
- `GET /api/v1/tasks/:id/comments/` - List all comments for task
- `GET /api/v1/tasks/:id/logs/` - Retrieve task change history

**API Features:**

- JWT authentication required for all operations
- User-filtered queries (only shows tasks created by or assigned to current user)
- Custom actions for assignment, status, priority updates, comments, and logs
- Optimized queries with `prefetch_related` and `select_related`
- Automatic change tracking with history logs
- Nested comment and history data in task responses

**Serializers:**

- `TaskSerializer`: Handles task data validation with nested comments and history
- `CommentSerializer`: Handles comment data validation and serialization
- `TaskHistorySerializer`: Handles change history serialization
- `ExtendedUserSerializer`: Includes user's assigned tasks, created tasks, comments, and change history

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

### TaskFieldEnum

Defines fields tracked in task history:

- **STATUS**: Status field changes
- **PRIORITY**: Priority field changes
- **ASSIGNED_TO**: Assignment changes
- **DUE_DATE**: Due date changes
- **TITLE**: Title changes
- **DESCRIPTION**: Description changes

All enums use Django's `TextChoices` for database storage and validation.

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
- **Change tracking** automatically logs all modifications to tracked fields
- **Comments** allow team collaboration and discussion on tasks
- **Task history** provides complete audit trail of all changes
- History entries preserve user information even if user is deleted (SET_NULL)
- `updated_at` timestamp automatically tracks last modification time
