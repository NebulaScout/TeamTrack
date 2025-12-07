# Accounts App

## Overview

The Accounts app is a Django application responsible for user authentication, registration, and role management in the TeamTrack project management system. It handles user account creation with role-based assignment and maintains user profiles with role-specific access levels.

## Features

### User Registration

- User registration with custom form handling
- Email validation and confirmation
- Secure password creation and confirmation
- Username, first name, and last name fields

### Role-Based Access Control

The app supports four user roles:

- **Admin (ADMIN)** - Full system access and administration capabilities
- **Project Manager (PM)** - Project oversight and team management
- **Developer (DEV)** - Development and task execution
- **Stakeholder (SH)** - Project visibility and reporting

### User Profile Management

- One-to-one relationship between Django User and RegisterModel
- Automatic role assignment during registration
- User creation timestamp tracking

## Database Models

### RegisterModel

Extended user profile model that links to Django's built-in User model:

- `user` - OneToOneField to Django User model (CASCADE delete)
- `role` - Character field storing user role (ADMIN, PM, DEV, or SH)
- `created_at` - Automatic timestamp of account creation

## Views

### `register(request)`

- Handles both GET and POST requests
- GET: Displays empty registration form
- POST: Processes form submission, creates User and RegisterModel instances, displays success message
- CSRF protection disabled (marked with `@csrf_exempt` decorator)

### `home(request)`

- Renders the base template
- Serves as the home page view

## Forms

### RegistrationForm

Custom user creation form extending Django's `UserCreationForm`:

- **Fields:** username, first_name, last_name, email, password1, password2, role
- **Role Selection:** Radio button widget for role selection
- **Validation:** Password confirmation and standard Django validation

## Security Considerations

- Uses Django's built-in `UserCreationForm` for secure password handling
- Implements CSRF protection (currently disabled on register endpoint for testing)
- Password confirmation validation through form validation

## Integration Points

- Part of the larger TeamTrack project management system
- Works with Django's authentication system
- Provides foundation for role-based access control across the application
- Templates located in `accounts/templates/accounts/`
- Static files (CSS, JS) located in `accounts/static/`

## Future Enhancements

- Enable CSRF protection on production
- Add user profile editing functionality
- Implement REST API endpoints for registration
- Add role change management
- Implement user deactivation/deletion
