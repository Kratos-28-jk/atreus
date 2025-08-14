# PAC3200 Electrical Monitoring Dashboard

A comprehensive web-based dashboard for monitoring SENTRON PAC3200 electrical parameters via Modbus TCP. This dashboard provides real-time data visualization, historical trending, and data logging capabilities.

## Features

### 🚀 Key Features
- **Real-time Monitoring**: Live electrical parameter display with automatic updates
- **Interactive Charts**: Historical trends for voltage, current, power, and frequency
- **Data Logging**: Automatic SQLite database storage of all readings
- **Modern UI**: Responsive design with Bootstrap 5 and gradient styling
- **API Endpoints**: RESTful API for external integrations
- **Background Collection**: Automatic data collection without blocking the UI

### 📊 Monitored Parameters
- **Voltages**: Phase-to-neutral (V1-N, V2-N, V3-N), Phase-to-phase (V1-V2, V2-V3, V3-V1)
- **Currents**: All three phases (L1, L2, L3) with averages
- **Power**: Active, Reactive, Apparent power per phase and total
- **Quality**: Power Factor, Frequency, THD-R for voltages and currents
- **Energy**: Total active and reactive energy consumption
- **Statistics**: Min/Max values for all parameters

## Installation

### Prerequisites
- Python 3.8 or higher
- Network connectivity to SENTRON PAC3200 device
- PAC3200 with Modbus TCP enabled

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure PAC3200 IP Address
Edit the configuration in `dashboard.py` and `pac3200_logger.py`:
```python
PAC3200_IP = '192.168.0.101'  # Replace with your PAC3200 IP address
PAC3200_PORT = 502
UNIT_ID = 1
```

### 3. Database Setup
The SQLite database will be automatically created on first run. The database file will be named `pac3200_readings.db`.

## Usage

### Starting the Dashboard
```bash
python dashboard.py
```

The dashboard will be available at: **http://localhost:5000**

### Dashboard Interface

#### 1. Control Panel
- **Start Collection**: Begin automatic data collection from PAC3200
- **Stop Collection**: Stop data collection
- **Status Indicator**: Shows connection status with animated indicator

#### 2. Key Metrics Cards
- **Voltage Card**: Average voltage with individual phase readings
- **Current Card**: Average current with individual phase readings  
- **Power Card**: Total active power with reactive and apparent power
- **Frequency Card**: System frequency and power factor

#### 3. Real-time Charts
- **Voltage Trends**: 24-hour historical voltage data for all phases
- **Current Trends**: 24-hour historical current data for all phases
- **Power Consumption**: Active, reactive, and apparent power trends
- **Frequency & Power Factor**: System frequency and power factor over time

#### 4. Recent Readings Table
- Displays the latest 20 readings from the database
- Automatically refreshes every 10 seconds
- Manual refresh button available

### API Endpoints

The dashboard provides several REST API endpoints for external integration:

#### GET `/api/latest_data`
Returns the most recent reading from the database.

#### GET `/api/historical_data?hours=24&limit=100`
Returns historical data for charts.
- `hours`: Time range (default: 24)
- `limit`: Maximum records (default: 100)

#### GET `/api/statistics`
Returns statistical summary of the last 24 hours.

#### GET `/api/recent_readings?limit=50`
Returns recent readings for table display.
- `limit`: Number of records (default: 50)

#### GET `/api/start_collection`
Starts background data collection.

#### GET `/api/stop_collection`
Stops background data collection.

#### GET `/api/collection_status`
Returns current collection status.

### Using the Original CLI Tool

You can still use the original command-line interface:
```bash
python pac3200_logger.py
```

This provides a menu-driven interface for:
1. Testing connection
2. Single readings
3. Continuous logging
4. Database queries
5. Data export

## Configuration

### Network Settings
Edit these parameters in both `dashboard.py` and `pac3200_logger.py`:
```python
PAC3200_IP = '192.168.0.101'    # PAC3200 IP address
PAC3200_PORT = 502              # Modbus TCP port (usually 502)
UNIT_ID = 1                     # Modbus unit ID
DATABASE_NAME = 'pac3200_readings.db'  # Database file name
```

### Data Collection Interval
In `dashboard.py`, modify the collection interval:
```python
time.sleep(30)  # Collect data every 30 seconds
```

### Chart Update Frequency
In the dashboard HTML template:
```javascript
setInterval(updateDashboard, 10000); // Update every 10 seconds
```

## Database Schema

### pac3200_readings Table
Main table storing all electrical readings with timestamp.

### parameter_definitions Table
Reference table with parameter descriptions, units, and register addresses.

## Troubleshooting

### Connection Issues
1. **Check IP Address**: Verify PAC3200 IP address is correct
2. **Network Connectivity**: Ensure network connectivity to PAC3200
3. **Modbus Settings**: Verify Modbus TCP is enabled on PAC3200
4. **Unit ID**: Check if unit ID is correct (usually 1)

### Dashboard Issues
1. **Port Conflicts**: If port 5000 is in use, modify the port in `dashboard.py`
2. **Permission Issues**: Ensure write permissions for database file
3. **Browser Compatibility**: Use a modern browser (Chrome, Firefox, Safari, Edge)

### Data Issues
1. **Missing Data**: Check if data collection is started via the dashboard
2. **Database Errors**: Check file permissions and disk space
3. **Register Mapping**: Verify register addresses match your PAC3200 model

## Advanced Usage

### Data Export
Export data to CSV:
```bash
python pac3200_logger.py export
```

### Database Backup
Create database backup:
```bash
python pac3200_logger.py backup
```

### SQL Queries
Run example SQL queries:
```bash
python pac3200_logger.py sql
```

### Custom API Integration
Use the REST API endpoints to integrate with other systems:
```python
import requests

# Get latest data
response = requests.get('http://localhost:5000/api/latest_data')
data = response.json()
print(f"Current Power: {data['Total_Active_Power']} W")
```

## File Structure
```
/workspace/
├── dashboard.py           # Main Flask dashboard application
├── pac3200_logger.py     # PAC3200 communication and logging
├── requirements.txt      # Python dependencies
├── templates/
│   └── dashboard.html    # Dashboard HTML template
├── pac3200_readings.db   # SQLite database (created automatically)
└── modbus_tcp_debug.log  # Debug log file
```

## Technical Specifications

### Supported PAC3200 Parameters
- 90+ electrical parameters including voltage, current, power, energy
- Real-time and min/max values
- THD-R (Total Harmonic Distortion) measurements
- Power quality indicators

### Web Technologies
- **Backend**: Flask 2.3.3, Python 3.8+
- **Frontend**: Bootstrap 5, Chart.js, vanilla JavaScript
- **Database**: SQLite 3
- **Communication**: Modbus TCP via pymodbus 2.5.3

### Performance
- **Data Collection**: Every 30 seconds (configurable)
- **Dashboard Updates**: Every 10 seconds
- **Chart Data**: Last 100 points (24 hours)
- **Table Display**: Latest 20 readings

## Security Considerations

1. **Network Security**: Use VPN or secure network for production
2. **Authentication**: Add authentication for production deployments
3. **Firewall**: Configure firewall rules for Modbus TCP (port 502)
4. **Database**: Backup database regularly

## License

This project is open source. Modify and distribute as needed.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the PAC3200 manual for Modbus configuration
3. Verify network connectivity and settings
4. Check log files for error messages

## Version History

- **v1.0**: Initial release with dashboard and CLI interface
- Complete PAC3200 register mapping
- Real-time charts and data visualization
- SQLite database integration
- REST API endpoints