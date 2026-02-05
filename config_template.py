# Database Configuration Template
# Copy this file to config.py and update with your actual credentials

DB_CONFIG = {
    'host': 'https://sv51.byethost51.org:2083/cpsess5207811907/3rdparty/phpMyAdmin/index.php?route=/database/structure&db=upendral_classicmodels',           # MySQL server hostname or IP
    'user': 'root',                # MySQL username
    'password': 'Bhugaon123$',   # MySQL password - CHANGE THIS!
    'database': 'upendral_classicmodels',       # Database name
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
