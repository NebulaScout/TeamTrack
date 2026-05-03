# Tasks Domain

## Scope

Tasks manages task CRUD, assignment, comments, and change history. The app is API-first with custom actions for common workflows.

## Highlights

- Task history tracks status, priority, assignment, and content changes
- Comment threads are tied to tasks for collaboration
- User-scoped query filtering for task visibility

## Services

- TaskService.create_task for task creation
- TaskService.update_task for audited updates
- TaskService.assign_task for assignment changes
- CommentService.create_comment for task comments

## Key Endpoints

- /api/v1/tasks/
- /api/v1/tasks/{id}/assign/
- /api/v1/tasks/{id}/comments/
- /api/v1/tasks/{id}/logs/
