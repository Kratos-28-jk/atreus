#!/bin/bash

# PAC3200 Dashboard Installation Script
# This script automates the installation and setup of the PAC3200 Power Monitor Dashboard

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check if version is 3.8 or higher
    if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 1 ]]; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python $PYTHON_VERSION found, but Python 3.8 or higher is required"
        exit 1
    fi
}

# Function to check pip
check_pip() {
    if command_exists pip3; then
        PIP_CMD="pip3"
    elif command_exists pip; then
        PIP_CMD="pip"
    else
        print_error "pip is not installed. Please install pip."
        exit 1
    fi
    print_success "pip found"
}

# Function to create virtual environment
create_venv() {
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Linux/Mac
        source venv/bin/activate
    fi
    print_success "Virtual environment activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip first
    $PIP_CMD install --upgrade pip
    
    # Install required packages
    $PIP_CMD install -r requirements.txt
    
    print_success "Dependencies installed successfully"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create templates directory if it doesn't exist
    if [ ! -d "templates" ]; then
        mkdir -p templates
        print_success "Created templates directory"
    fi
    
    # Create exports directory if it doesn't exist
    if [ ! -d "exports" ]; then
        mkdir -p exports
        print_success "Created exports directory"
    fi
    
    # Create logs directory if it doesn't exist
    if [ ! -d "logs" ]; then
        mkdir -p logs
        print_success "Created logs directory"
    fi
}

# Function to check configuration
check_configuration() {
    print_status "Checking configuration..."
    
    if [ -f "config.py" ]; then
        # Run configuration validation
        $PYTHON_CMD config.py
        print_success "Configuration validated"
    else
        print_warning "config.py not found. Please create it manually."
    fi
}

# Function to set permissions
set_permissions() {
    print_status "Setting file permissions..."
    
    # Make scripts executable
    chmod +x run_dashboard.py
    chmod +x install.sh
    
    print_success "Permissions set"
}

# Function to create systemd service (Linux only)
create_systemd_service() {
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command_exists systemctl; then
        print_status "Creating systemd service..."
        
        SERVICE_FILE="/etc/systemd/system/pac3200-dashboard.service"
        
        if [ ! -f "$SERVICE_FILE" ]; then
            sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=PAC3200 Power Monitor Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python run_dashboard.py
Restart=always
RestartSec=10
Environment=PATH=$(pwd)/venv/bin

[Install]
WantedBy=multi-user.target
EOF
            print_success "Systemd service created"
            print_status "To enable the service, run: sudo systemctl enable pac3200-dashboard"
            print_status "To start the service, run: sudo systemctl start pac3200-dashboard"
        else
            print_warning "Systemd service already exists"
        fi
    else
        print_warning "Systemd service creation skipped (not Linux or systemctl not available)"
    fi
}

# Function to create startup script
create_startup_script() {
    print_status "Creating startup script..."
    
    STARTUP_SCRIPT="start_dashboard.sh"
    
    cat > "$STARTUP_SCRIPT" << 'EOF'
#!/bin/bash

# PAC3200 Dashboard Startup Script
# This script starts the dashboard with proper environment setup

cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
fi

# Start the dashboard
python run_dashboard.py "$@"
EOF
    
    chmod +x "$STARTUP_SCRIPT"
    print_success "Startup script created: $STARTUP_SCRIPT"
}

# Function to display final instructions
display_instructions() {
    echo
    echo "=========================================="
    echo "🎉 PAC3200 Dashboard Installation Complete!"
    echo "=========================================="
    echo
    echo "📋 Next Steps:"
    echo "1. Update PAC3200 IP address in config.py"
    echo "2. Ensure PAC3200 is accessible on your network"
    echo "3. Start the dashboard using one of these methods:"
    echo
    echo "   Option 1: Direct Python execution"
    echo "   $ source venv/bin/activate  # Linux/Mac"
    echo "   $ venv\\Scripts\\activate     # Windows"
    echo "   $ python run_dashboard.py"
    echo
    echo "   Option 2: Use startup script"
    echo "   $ ./start_dashboard.sh"
    echo
    echo "   Option 3: Use systemd service (Linux)"
    echo "   $ sudo systemctl start pac3200-dashboard"
    echo
    echo "🌐 Dashboard will be available at: http://localhost:5000"
    echo
    echo "📚 For more information, see README.md"
    echo "🔧 For troubleshooting, check the logs directory"
    echo
}

# Main installation function
main() {
    echo "🚀 PAC3200 Power Monitor Dashboard Installation"
    echo "=============================================="
    echo
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    check_python_version
    check_pip
    
    # Create virtual environment
    create_venv
    
    # Activate virtual environment
    activate_venv
    
    # Install dependencies
    install_dependencies
    
    # Create directories
    create_directories
    
    # Check configuration
    check_configuration
    
    # Set permissions
    set_permissions
    
    # Create systemd service (Linux only)
    create_systemd_service
    
    # Create startup script
    create_startup_script
    
    # Display final instructions
    display_instructions
}

# Check if script is run with sudo
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root (sudo)"
    print_error "Please run as a regular user"
    exit 1
fi

# Run main installation
main "$@"