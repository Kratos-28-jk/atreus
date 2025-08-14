#!/usr/bin/env python3
"""
PAC3200 Dashboard Startup Script
This script provides a simple way to start the PAC3200 dashboard with configuration options.
"""

import os
import sys
import argparse
from datetime import datetime

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'pandas', 'pymodbus']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_files():
    """Check if required files exist"""
    required_files = [
        'app.py',
        'pac3200_logger.py',
        'templates/dashboard.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    return True

def create_templates_directory():
    """Create templates directory if it doesn't exist"""
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("📁 Created templates directory")

def main():
    parser = argparse.ArgumentParser(description='PAC3200 Dashboard Startup Script')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    print("🚀 PAC3200 Power Monitor Dashboard")
    print("=" * 50)
    print(f"Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug mode: {args.debug}")
    print()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ All dependencies satisfied")
    
    # Check files
    print("🔍 Checking required files...")
    if not check_files():
        print("\n📁 Creating missing directories...")
        create_templates_directory()
        if not check_files():
            print("❌ Critical files still missing. Please ensure all files are present.")
            sys.exit(1)
    print("✅ All required files found")
    
    # Check if database exists
    if not os.path.exists('pac3200_readings.db'):
        print("📊 Database file not found. It will be created automatically on first run.")
    
    print("\n🎯 Starting dashboard...")
    print(f"🌐 Dashboard will be available at: http://{args.host}:{args.port}")
    print("📱 Press Ctrl+C to stop the dashboard")
    print("=" * 50)
    
    try:
        # Import and run Flask app
        from app import app
        
        # Update Flask app configuration
        app.config['DEBUG'] = args.debug
        
        # Start the application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False  # Disable reloader to avoid duplicate processes
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if port is already in use")
        print("2. Verify PAC3200 IP address in app.py")
        print("3. Ensure network connectivity to PAC3200")
        print("4. Check Flask application logs")
        sys.exit(1)

if __name__ == '__main__':
    main()