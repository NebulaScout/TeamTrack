# TeamTrack

TeamTrack is a Collaborative Task Scheduling and Tracking System (CTSTS) designed to help software engineering teams organize projects, assign work, monitor progress, and stay aligned.

## Overview

TeamTrack is built with Django and Django REST Framework, providing both web-based views and a RESTful API for managing team collaboration. The application follows a clean architecture with separation between API and web layers, enabling flexible integration with frontend applications while maintaining traditional server-rendered views.

### Current Features

**User Authentication & Management**

- JWT-based authentication with access and refresh tokens
- User registration with email validation
- Secure login/logout functionality
- User profile management with API integration
- Automatic token refresh mechanism

**REST API**

- Versioned API structure (`/api/v1/`)
- User management endpoints with role-based permissions
- Registration endpoints
- JWT token generation and refresh endpoints
- Custom permission classes for granular access control

**Architecture**

- Service layer pattern for business logic
- API-first design with internal HTTP communication
- Session-based token storage for web views
- Modular app structure (accounts, api)

### Technology Stack

- **Backend:** Django 6.0
- **API Framework:** Django REST Framework
- **Authentication:** djangorestframework-simplejwt
- **Database:** Django ORM
- **Environment Management:** django-environ

### Project Structure

```
TeamTrack/
├── accounts/          # User authentication and management
├── api/              # RESTful API endpoints (versioned)
└── team_track/       # Django project settings
```

For detailed documentation on specific components:

- [Accounts App Documentation](accounts/README.md)
- [API Documentation](api/README.md)
