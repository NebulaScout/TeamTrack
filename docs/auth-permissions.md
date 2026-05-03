# Auth and Permissions

## Authentication

TeamTrack uses JWT authentication via djangorestframework-simplejwt. Tokens are obtained from /api/token/ and sent in the Authorization header.

## Roles

Users can be assigned one of the following roles using Django Groups:

- Admin
- Project Manager
- Developer
- Guest

Role assignment is managed by a service helper and is used by permission classes to gate access.

## Permission Classes

- UserPermissions: user CRUD with admin-only list/delete
- ProjectPermissions: project CRUD with authenticated access
- TaskPermissions: task CRUD with user-scoped query filtering
- IsAdminDashboardUser: admin dashboard access control

## Access Patterns

- Web views use login_required and session-stored JWT tokens
- API viewsets enforce permissions and filter querysets for scoping
- Admin endpoints require staff or Admin group membership
