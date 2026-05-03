# Accounts Domain

## Scope

Accounts covers authentication, registration, and profile management. It supports both API-driven and server-rendered workflows.

## Highlights

- JWT authentication and token refresh
- Registration via API endpoint with service layer integration
- Profile view that consumes internal API endpoints
- Role assignment via Django Groups

## Services

- registration_service.register_user for account creation
- group_assignment.set_user_role for role changes

## Key Endpoints

- /api/v1/accounts/register/
- /api/v1/accounts/users/
- /api/v1/accounts/users/{id}/assign_role/
- /api/v1/accounts/users/me/
