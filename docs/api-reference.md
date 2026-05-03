# API Reference

## Source of Truth

The canonical API definition is in schema.yml. Use it to validate request and response shapes.

## Base URLs

- /api/ for root API routing
- /api/v1/ for versioned endpoints

## Authentication

- POST /api/token/ to obtain JWT access and refresh tokens
- POST /api/token/refresh/ to refresh access tokens
- POST /api/token/verify/ to verify tokens

Most endpoints require `Authorization: Bearer <token>`.

## Endpoint Groups

### Accounts

- /api/v1/accounts/register/
- /api/v1/accounts/users/

### Auth

- /api/v1/auth/login/
- /api/v1/auth/logout/
- /api/v1/auth/me/

### Projects

- /api/v1/projects/
- /api/v1/projects/{id}/tasks/
- /api/v1/projects/{id}/members/

### Tasks

- /api/v1/tasks/
- /api/v1/tasks/{id}/assign/
- /api/v1/tasks/{id}/comments/
- /api/v1/tasks/{id}/logs/

### Calendar

- /api/v1/calendar/events/
- /api/v1/calendar/deadline-sync/

## Response Format

Most endpoints return JSON via DRF serializers. Some API responses are standardized using a shared response mixin.
