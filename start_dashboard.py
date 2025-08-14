#!/usr/bin/env python3
"""
PAC3200 Dashboard Startup Script
Provides an easy way to configure and start the dashboard
"""

import os
import sys
import socket
import subprocess
from pac3200_logger import PAC3200SQLLogger

def check_port_available(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return True
    except OSError:
        return False

def test_pac3200_connection(ip, port=502, unit_id=1):
    """Test connection to PAC3200"""
    print(f"Testing connection to PAC3200 at {ip}:{port}...")
    
    try:
        logger = PAC3200SQLLogger(host=ip, port=port, unit_id=unit_id)
        if logger.connect():
            print("✅ Successfully connected to PAC3200!")
            
            # Test reading a basic parameter
            voltage = logger.read_float32_register(1)  # V1-N Voltage
            if voltage is not None:
                print(f"✅ Test reading successful: V1-N = {voltage:.2f} V")
            else:
                print("⚠️  Connected but unable to read data. Check register mapping.")
            
            logger.disconnect()
            return True
        else:
            print("❌ Failed to connect to PAC3200")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 PAC3200 Electrical Monitoring Dashboard")
    print("=" * 60)
    
    # Check if dashboard.py exists
    if not os.path.exists('dashboard.py'):
        print("❌ dashboard.py not found. Please run from the correct directory.")
        sys.exit(1)
    
    # Configuration prompts
    print("\n🔧 Configuration Setup")
    print("-" * 30)
    
    # Get PAC3200 IP address
    default_ip = "192.168.0.101"
    pac3200_ip = input(f"Enter PAC3200 IP address (default: {default_ip}): ").strip()
    if not pac3200_ip:
        pac3200_ip = default_ip
    
    # Get Modbus port
    default_port = 502
    try:
        modbus_port = input(f"Enter Modbus TCP port (default: {default_port}): ").strip()
        if modbus_port:
            modbus_port = int(modbus_port)
        else:
            modbus_port = default_port
    except ValueError:
        print("Invalid port, using default 502")
        modbus_port = default_port
    
    # Get Unit ID
    default_unit_id = 1
    try:
        unit_id = input(f"Enter Modbus Unit ID (default: {default_unit_id}): ").strip()
        if unit_id:
            unit_id = int(unit_id)
        else:
            unit_id = default_unit_id
    except ValueError:
        print("Invalid unit ID, using default 1")
        unit_id = default_unit_id
    
    # Test connection
    print(f"\n🔍 Testing Connection")
    print("-" * 30)
    
    if not test_pac3200_connection(pac3200_ip, modbus_port, unit_id):
        print("\n⚠️  Connection test failed. Possible issues:")
        print("   1. Check PAC3200 IP address")
        print("   2. Verify network connectivity")
        print("   3. Ensure Modbus TCP is enabled on PAC3200")
        print("   4. Check unit ID setting")
        print("   5. Verify firewall settings")
        
        continue_anyway = input("\nContinue anyway? (y/N): ").lower().strip()
        if continue_anyway != 'y':
            print("Exiting...")
            sys.exit(1)
    
    # Check dashboard port
    dashboard_port = 5000
    if not check_port_available(dashboard_port):
        print(f"\n⚠️  Port {dashboard_port} is already in use.")
        try:
            dashboard_port = int(input("Enter alternative port (e.g., 5001): "))
        except ValueError:
            print("Invalid port, using 5000 anyway")
            dashboard_port = 5000
    
    # Update configuration in dashboard.py
    print(f"\n📝 Updating Configuration")
    print("-" * 30)
    
    try:
        # Read dashboard.py
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        # Update configuration
        content = content.replace("PAC3200_IP = '192.168.0.101'", f"PAC3200_IP = '{pac3200_ip}'")
        content = content.replace("PAC3200_PORT = 502", f"PAC3200_PORT = {modbus_port}")
        content = content.replace("UNIT_ID = 1", f"UNIT_ID = {unit_id}")
        
        if dashboard_port != 5000:
            content = content.replace("app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)", 
                                    f"app.run(debug=True, host='0.0.0.0', port={dashboard_port}, threaded=True)")
        
        # Write updated configuration
        with open('dashboard.py', 'w') as f:
            f.write(content)
        
        print("✅ Configuration updated successfully!")
        
    except Exception as e:
        print(f"❌ Failed to update configuration: {e}")
        print("Please manually edit dashboard.py with your settings")
    
    # Start dashboard
    print(f"\n🚀 Starting Dashboard")
    print("-" * 30)
    print(f"Dashboard will be available at: http://localhost:{dashboard_port}")
    print("Press Ctrl+C to stop the dashboard")
    print("\n" + "=" * 60)
    
    # Start the dashboard
    try:
        subprocess.run([sys.executable, 'dashboard.py'], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Dashboard failed to start: {e}")
        print("Check the error messages above for details")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()