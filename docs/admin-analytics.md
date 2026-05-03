# Admin Analytics and Dashboard

## Overview

Admin analytics provides dashboard endpoints for user, project, task, and audit log visibility.

## Base URL

- /dashboard/

## Key Endpoints

- /dashboard/ - user dashboard
- /dashboard/admin/ - admin quick stats
- /dashboard/admin/users/ - admin user list
- /dashboard/admin/users/{id}/ - admin user detail
- /dashboard/admin/projects/ - admin project list
- /dashboard/admin/projects/{id}/ - admin project detail
- /dashboard/admin/projects/{id}/members/ - project members
- /dashboard/admin/tasks/ - admin task list
- /dashboard/admin/tasks/{id}/ - admin task detail
- /dashboard/admin/tasks/{id}/comments/ - admin task comments
- /dashboard/admin/audit-logs/ - audit log list

## Notes

- Uses GlobalAuditLog for activity tracking
- AuditService resolves human-readable action names
- Supports filtering by project, user, module, and action
