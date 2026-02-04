# Database Configuration Template
# Copy this file to config.py and update with your actual credentials

DB_CONFIG = {
    'host': 'localhost',           # MySQL server hostname or IP
    'user': 'phpmyadmin',                # MySQL username
    'password': '123',   # MySQL password - CHANGE THIS!
    'database': 'test',       # Database name
    'port': 3306,                  # MySQL port (default: 3306)
    'raise_on_warnings': True      # Raise exceptions on MySQL warnings
}

# Application Settings
APP_CONFIG = {
    'page_title': 'Course Management System',
    'page_icon': '📚',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Table Configuration
TABLE_NAME = 'tbl_courses'

# Field Constraints
CONSTRAINTS = {
    'course_code': {
        'max_length': 10,
        'required': True
    },
    'course_credits': {
        'min_value': 1,
        'max_value': 10,
        'required': True
    },
    'sessions_per_week': {
        'min_value': 1,
        'max_value': 10,
        'required': True
    }
}
