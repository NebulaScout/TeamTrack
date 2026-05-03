# Management Commands

TeamTrack includes custom management commands for seeding and maintenance. Review each command file for exact behavior and parameters.

## Commands

- init_roles: create default roles and permissions
- seed_all: run the common seed commands in sequence
- seed_users: seed sample users
- seed_groups: seed default groups/roles
- seed_projects: seed sample projects and memberships
- seed_tasks: seed sample tasks
- seed_audit_logs: seed audit log entries
- seed_calendar: seed calendar events
- seed_avatars: seed avatar assets
- generate_profiles: build user profile data

## Where to Look

- core/management/commands/
