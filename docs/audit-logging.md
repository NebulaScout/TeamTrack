# Audit Logging

## Overview

TeamTrack records task-level change history and system-wide audit logs.

## Task History

TaskHistoryModel tracks changes to these fields:

- status
- priority
- assigned_to
- due_date
- title
- description

Each entry stores old/new values, the actor, and a timestamp.

## Global Audit Log

GlobalAuditLog records cross-module activity including:

- module (project, task, user, comment, system)
- action (created, updated, deleted, registered)
- actor and target references
- optional project scope
- metadata for additional context

## Services

- AuditService.log creates audit entries
- AuditService.created, updated, deleted for common actions
- AuditService.resolve_action_type for readable labels
