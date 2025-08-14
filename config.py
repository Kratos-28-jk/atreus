"""
PAC3200 Dashboard Configuration
Centralized configuration for the PAC3200 Power Monitor Dashboard
"""

# PAC3200 Device Configuration
PAC3200_CONFIG = {
    'IP_ADDRESS': '192.168.0.101',  # Replace with your PAC3200 IP address
    'PORT': 502,                     # Modbus TCP port (usually 502)
    'UNIT_ID': 1,                    # Modbus unit ID
    'TIMEOUT': 3,                    # Connection timeout in seconds
    'RETRY_ATTEMPTS': 3,             # Number of retry attempts for failed connections
    'RETRY_DELAY': 5,                # Delay between retry attempts in seconds
}

# Database Configuration
DATABASE_CONFIG = {
    'NAME': 'pac3200_readings.db',   # SQLite database filename
    'BACKUP_ENABLED': True,          # Enable automatic database backups
    'BACKUP_INTERVAL_HOURS': 24,     # Backup interval in hours
    'MAX_BACKUP_FILES': 7,           # Maximum number of backup files to keep
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'HOST': '0.0.0.0',              # Host to bind to (0.0.0.0 for all interfaces)
    'PORT': 5000,                    # Port to bind to
    'DEBUG': False,                  # Enable debug mode
    'SECRET_KEY': 'your-secret-key-here',  # Flask secret key for sessions
    
    # Auto-refresh settings
    'AUTO_REFRESH_ENABLED': True,    # Enable auto-refresh by default
    'AUTO_REFRESH_INTERVAL': 30,     # Auto-refresh interval in seconds
    
    # Chart configuration
    'DEFAULT_TIME_RANGE': 24,        # Default time range in hours
    'MAX_DATA_POINTS': 1000,         # Maximum data points to display in charts
    'CHART_UPDATE_INTERVAL': 5,      # Chart update interval in seconds
    
    # Data collection settings
    'COLLECTION_TIMEOUT': 10,        # Timeout for data collection in seconds
    'MAX_COLLECTION_RETRIES': 3,     # Maximum retries for data collection
}

# Logging Configuration
LOGGING_CONFIG = {
    'LEVEL': 'INFO',                 # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    'FILE': 'dashboard.log',         # Log file name
    'MAX_SIZE_MB': 10,               # Maximum log file size in MB
    'BACKUP_COUNT': 5,               # Number of backup log files to keep
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Alert Configuration
ALERT_CONFIG = {
    'ENABLED': True,                 # Enable alert system
    'VOLTAGE_THRESHOLD': {           # Voltage thresholds for alerts
        'MIN': 200,                  # Minimum voltage (V)
        'MAX': 250,                  # Maximum voltage (V)
    },
    'CURRENT_THRESHOLD': {           # Current thresholds for alerts
        'MAX': 100,                  # Maximum current (A)
    },
    'POWER_THRESHOLD': {             # Power thresholds for alerts
        'MAX': 50000,                # Maximum power (W)
    },
    'FREQUENCY_THRESHOLD': {         # Frequency thresholds for alerts
        'MIN': 49.5,                 # Minimum frequency (Hz)
        'MAX': 50.5,                 # Maximum frequency (Hz)
    }
}

# Security Configuration
SECURITY_CONFIG = {
    'AUTHENTICATION_ENABLED': False, # Enable user authentication
    'SSL_ENABLED': False,            # Enable HTTPS/SSL
    'SSL_CERT_FILE': None,           # SSL certificate file path
    'SSL_KEY_FILE': None,            # SSL private key file path
    'CORS_ENABLED': False,           # Enable Cross-Origin Resource Sharing
    'ALLOWED_ORIGINS': [],           # List of allowed CORS origins
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'WORKER_THREADS': 4,             # Number of worker threads
    'CONNECTION_POOL_SIZE': 10,      # Database connection pool size
    'QUERY_TIMEOUT': 30,             # Database query timeout in seconds
    'CACHE_ENABLED': True,           # Enable data caching
    'CACHE_TTL': 300,                # Cache time-to-live in seconds
}

# Export Configuration
EXPORT_CONFIG = {
    'CSV_ENABLED': True,             # Enable CSV export
    'JSON_ENABLED': True,            # Enable JSON export
    'EXCEL_ENABLED': False,          # Enable Excel export (requires openpyxl)
    'MAX_EXPORT_RECORDS': 10000,     # Maximum records to export
    'EXPORT_DIRECTORY': 'exports',    # Directory for exported files
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    'EMAIL_ENABLED': False,          # Enable email notifications
    'SMTP_SERVER': 'smtp.gmail.com', # SMTP server address
    'SMTP_PORT': 587,                # SMTP server port
    'SMTP_USERNAME': '',             # SMTP username
    'SMTP_PASSWORD': '',             # SMTP password
    'EMAIL_FROM': '',                # From email address
    'EMAIL_TO': [],                  # List of recipient email addresses
    
    'WEBHOOK_ENABLED': False,        # Enable webhook notifications
    'WEBHOOK_URL': '',               # Webhook URL
    'WEBHOOK_TIMEOUT': 10,           # Webhook timeout in seconds
}

# Development Configuration
DEV_CONFIG = {
    'TEST_MODE': False,              # Enable test mode
    'MOCK_DATA': False,              # Use mock data instead of real PAC3200
    'LOG_REQUESTS': True,            # Log all HTTP requests
    'PROFILING_ENABLED': False,      # Enable performance profiling
}

def get_config():
    """Get complete configuration dictionary"""
    return {
        'pac3200': PAC3200_CONFIG,
        'database': DATABASE_CONFIG,
        'dashboard': DASHBOARD_CONFIG,
        'logging': LOGGING_CONFIG,
        'alerts': ALERT_CONFIG,
        'security': SECURITY_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'export': EXPORT_CONFIG,
        'notifications': NOTIFICATION_CONFIG,
        'development': DEV_CONFIG,
    }

def update_config(section, key, value):
    """Update a configuration value"""
    config = get_config()
    if section in config and key in config[section]:
        config[section][key] = value
        return True
    return False

def validate_config():
    """Validate configuration values"""
    errors = []
    
    # Validate PAC3200 configuration
    if not PAC3200_CONFIG['IP_ADDRESS'] or PAC3200_CONFIG['IP_ADDRESS'] == '192.168.0.101':
        errors.append("Please update PAC3200 IP address in config.py")
    
    if PAC3200_CONFIG['PORT'] < 1 or PAC3200_CONFIG['PORT'] > 65535:
        errors.append("Invalid PAC3200 port number")
    
    # Validate dashboard configuration
    if PAC3200_CONFIG['PORT'] == DASHBOARD_CONFIG['PORT']:
        errors.append("PAC3200 port and dashboard port cannot be the same")
    
    # Validate alert thresholds
    if ALERT_CONFIG['VOLTAGE_THRESHOLD']['MIN'] >= ALERT_CONFIG['VOLTAGE_THRESHOLD']['MAX']:
        errors.append("Voltage threshold min must be less than max")
    
    if ALERT_CONFIG['FREQUENCY_THRESHOLD']['MIN'] >= ALERT_CONFIG['FREQUENCY_THRESHOLD']['MAX']:
        errors.append("Frequency threshold min must be less than max")
    
    return errors

if __name__ == '__main__':
    # Configuration validation
    print("🔍 Validating configuration...")
    errors = validate_config()
    
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
        print("\nPlease fix these errors before running the dashboard.")
    else:
        print("✅ Configuration is valid")
    
    # Display current configuration
    print("\n📋 Current Configuration:")
    config = get_config()
    for section, settings in config.items():
        print(f"\n{section.upper()}:")
        for key, value in settings.items():
            if isinstance(value, (dict, list)):
                print(f"  {key}: {type(value).__name__}")
            else:
                print(f"  {key}: {value}")