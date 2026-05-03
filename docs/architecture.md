# Architecture

## Overview

TeamTrack is a Django + Django REST Framework application that supports both API-first workflows and server-rendered views. The codebase uses a service layer to isolate business logic from the web and API layers.

## Core Patterns

- Service layer pattern in core/services for business logic reuse
- API versioning under api/v1
- Role-based access control via custom permission classes
- Audit history and activity tracking for task changes

## Application Layers

- Web layer: Django views and templates (accounts, projects)
- API layer: DRF viewsets and serializers (api/v1)
- Service layer: domain logic (core/services)
- Data layer: Django models with enum-based validation

## Key Apps

- accounts: authentication, registration, profiles
- projects: project creation and membership
- tasks: task CRUD, comments, and history
- Calendar: events and deadline sync
- audit: system-wide audit logging
- core: shared services, enums, management commands

## Data Models (Selected)

- User: Django built-in user model
- RegisterModel: extended user profile record
- ProjectsModel and ProjectMembers
- TaskModel, CommentModel, TaskHistoryModel
- GlobalAuditLog for cross-module audit entries

## Query and Performance Notes

- Use select_related and prefetch_related in viewsets
- Annotate and aggregate for dashboard stats
- Keep task list responses optimized with minimal serializers
