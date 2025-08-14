# PAC3200 Power Monitor Dashboard

A modern, web-based dashboard for monitoring SENTRON PAC3200 power meters via Modbus TCP. This dashboard provides real-time monitoring, historical data visualization, and comprehensive power system analytics.

## Features

### 🎯 **Real-time Monitoring**
- Live voltage, current, and power readings
- Connection status indicator
- Auto-refresh capabilities
- Real-time data collection from PAC3200

### 📊 **Interactive Charts**
- Voltage trends (V1-N, V2-N, V3-N)
- Current trends (L1, L2, L3)
- Power trends (Active, Reactive, Apparent)
- Power Factor and Frequency monitoring

### 📈 **Data Analytics**
- Statistical summaries
- Historical data analysis
- Time-range selection (1 hour to 1 week)
- Database storage and retrieval

### 🎨 **Modern UI**
- Responsive Bootstrap design
- Professional color scheme
- Interactive controls
- Mobile-friendly interface

## Prerequisites

- Python 3.8 or higher
- SENTRON PAC3200 power meter
- Network connectivity to PAC3200
- Modbus TCP enabled on PAC3200

## Installation

1. **Clone or download the project files**
   ```bash
   # Ensure you have all these files in your project directory:
   # - app.py (Flask application)
   # - pac3200_logger.py (Your existing PAC3200 logger)
   # - templates/dashboard.html (Dashboard template)
   # - requirements.txt (Dependencies)
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure PAC3200 settings**
   - Edit `app.py` and update the configuration variables:
     ```python
     PAC3200_IP = '192.168.0.101'  # Your PAC3200 IP address
     PAC3200_PORT = 502             # Modbus TCP port (usually 502)
     UNIT_ID = 1                    # Modbus unit ID
     DATABASE_NAME = 'pac3200_readings.db'
     ```

## Usage

### Starting the Dashboard

1. **Run the Flask application**
   ```bash
   python app.py
   ```

2. **Access the dashboard**
   - Open your web browser
   - Navigate to: `http://localhost:5000`
   - The dashboard will automatically load and attempt to connect to PAC3200

### Dashboard Features

#### **Control Panel**
- **Collect Data**: Manually collect new readings from PAC3200
- **Refresh**: Update all dashboard data
- **Time Range**: Select historical data period (1h, 6h, 24h, 1 week)
- **Auto-refresh**: Enable automatic data updates every 30 seconds

#### **Key Metrics Display**
- **Voltages**: V1-N, V2-N, V3-N (Phase to Neutral)
- **Current**: L1, L2, L3 line currents
- **Power**: Total Active Power
- **Frequency**: System frequency

#### **Interactive Charts**
- **Voltage Trends**: Real-time voltage monitoring across all phases
- **Current Trends**: Current flow visualization
- **Power Trends**: Active, reactive, and apparent power
- **Power Factor & Frequency**: Combined chart with dual Y-axes

#### **Data Statistics**
- Total records count
- First and last reading timestamps
- Average voltage and power values
- System performance metrics

## API Endpoints

The dashboard provides several REST API endpoints:

- `GET /` - Main dashboard page
- `GET /api/latest_data` - Latest readings from database
- `GET /api/historical_data?hours=X` - Historical data for charts
- `POST /api/collect_data` - Collect new data from PAC3200
- `GET /api/statistics` - Statistical summary
- `GET /api/connection_status` - PAC3200 connection status

## Configuration

### PAC3200 Settings
- **IP Address**: Configure in `app.py`
- **Port**: Default Modbus TCP port is 502
- **Unit ID**: Modbus device identifier
- **Timeout**: Connection timeout in seconds

### Database Settings
- **SQLite Database**: Automatically created as `pac3200_readings.db`
- **Tables**: 
  - `pac3200_readings`: Main data storage
  - `parameter_definitions`: Register mapping and descriptions

### Dashboard Settings
- **Auto-refresh**: 30-second intervals
- **Chart Updates**: Real-time data visualization
- **Time Ranges**: Configurable historical data periods

## Troubleshooting

### Connection Issues
1. **Check Network Connectivity**
   - Ensure PAC3200 is accessible from your network
   - Verify IP address and port settings
   - Check firewall configurations

2. **Modbus Configuration**
   - Confirm Modbus TCP is enabled on PAC3200
   - Verify unit ID matches configuration
   - Check register address mapping

3. **Database Issues**
   - Ensure write permissions in project directory
   - Check SQLite database file integrity
   - Verify table structure matches expected schema

### Performance Issues
1. **Data Collection**
   - Reduce collection frequency if needed
   - Monitor database size and performance
   - Consider data archiving for long-term storage

2. **Chart Rendering**
   - Limit historical data range for better performance
   - Disable auto-refresh if not needed
   - Monitor browser memory usage

## File Structure

```
project_directory/
├── app.py                 # Flask application and API endpoints
├── pac3200_logger.py     # PAC3200 Modbus communication class
├── templates/
│   └── dashboard.html    # Dashboard HTML template
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── pac3200_readings.db   # SQLite database (created automatically)
```

## Customization

### Adding New Parameters
1. Update `pac3200_logger.py` register map
2. Modify database schema in `init_database()`
3. Update dashboard charts and metrics
4. Add new API endpoints if needed

### Styling Changes
- Modify CSS variables in `dashboard.html`
- Update Bootstrap classes for layout changes
- Customize chart colors and options

### Additional Features
- Implement data export functionality
- Add alarm/alert systems
- Create user authentication
- Implement data backup/restore

## Security Considerations

- **Network Security**: Ensure PAC3200 is on secure network
- **Access Control**: Consider implementing authentication
- **Data Protection**: Regular database backups
- **Input Validation**: All API inputs are validated

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify configuration settings
3. Review error logs in browser console
4. Check Flask application logs

## License

This project is provided as-is for educational and monitoring purposes. Ensure compliance with your organization's policies and local regulations.

---

**Note**: This dashboard is designed to work with your existing `PAC3200SQLLogger` class. Make sure all required methods and database structure are properly implemented before running the dashboard.