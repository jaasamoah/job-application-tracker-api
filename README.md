# Job Application Tracker API

## Overview

This is a Flask-based REST API for managing job applications. The application provides CRUD operations for tracking job applications with features like status management, company information, and application dates. It's designed as a simple, lightweight API that stores data in memory for demonstration purposes.

## System Architecture

The application follows a simple Flask web application architecture:

- **Framework**: Flask (Python web framework)
- **API Style**: RESTful API with JSON responses
- **Data Storage**: In-memory storage (Python lists/dictionaries)
- **Frontend**: Basic HTML documentation page with Bootstrap styling
- **CORS**: Enabled for cross-origin requests
- **Deployment**: Gunicorn WSGI server with autoscale deployment

## Key Components

### Backend Architecture
- **main.py**: Application entry point that imports and runs the Flask app
- **app.py**: Core Flask application with all API endpoints and business logic
- **In-memory Storage**: Job applications stored in Python list with auto-incrementing IDs

### Frontend Architecture
- **templates/index.html**: API documentation page with Bootstrap dark theme
- **static/style.css**: Custom CSS for styling the documentation page
- **Feather Icons**: Icon library for UI elements

### API Design
- RESTful endpoints for job application management
- JSON request/response format
- Input validation with error handling
- Status field validation against predefined options

## Data Flow

1. **Client Request**: HTTP requests sent to Flask application
2. **Validation**: Input data validated using custom validation functions
3. **Processing**: CRUD operations performed on in-memory data structure
4. **Response**: JSON responses with appropriate HTTP status codes

### Data Model
Job applications contain:
- `id`: Auto-incrementing integer
- `company_name`: Required string
- `position`: Required string
- `status`: One of predefined status values
- `application_date`: Optional ISO format date
- `notes`: Optional text field

### Valid Status Options
- Applied, Interview, Phone Screen, On-site, Rejected, Offer, Accepted, Withdrawn

## External Dependencies

### Python Packages
- **flask**: Web framework for API development
- **flask-cors**: Cross-origin resource sharing support
- **flask-sqlalchemy**: SQL toolkit (installed but not currently used)
- **gunicorn**: WSGI HTTP server for production deployment
- **psycopg2-binary**: PostgreSQL adapter (installed but not currently used)
- **email-validator**: Email validation utilities

### Frontend Dependencies
- **Bootstrap**: CSS framework with dark theme variant
- **Feather Icons**: Icon library for UI elements

## Deployment Strategy

- **Platform**: Replit with Nix environment
- **Runtime**: Python 3.11
- **Server**: Gunicorn with auto-reload for development
- **Scaling**: Autoscale deployment target
- **Port**: Application runs on port 5000
- **Environment**: Configured for both development and production modes
