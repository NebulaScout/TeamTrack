# Projects Domain

## Scope

Projects manages project creation, membership, and project-scoped task workflows. The web layer uses forms, while the API layer provides full CRUD.

## Highlights

- Project creators are automatically assigned Project Manager role
- Membership records enforce unique project-member pairs
- Service layer creates projects and membership atomically

## Services

- ProjectService.create_project for creation and membership bootstrap

## Key Endpoints

- /api/v1/projects/
- /api/v1/projects/{id}/tasks/
- /api/v1/projects/{id}/members/
