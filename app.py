from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
from pac3200_logger import PAC3200SQLLogger

app = Flask(__name__)

# Configuration
PAC3200_IP = '192.168.0.101'
PAC3200_PORT = 502
UNIT_ID = 1
DATABASE_NAME = 'pac3200_readings.db'

# Initialize PAC3200 logger
logger = PAC3200SQLLogger(
    host=PAC3200_IP,
    port=PAC3200_PORT,
    unit_id=UNIT_ID,
    db_name=DATABASE_NAME
)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/latest_data')
def get_latest_data():
    """Get latest readings from database"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        
        # Get latest reading
        latest_query = '''
            SELECT * FROM pac3200_readings 
            ORDER BY timestamp DESC 
            LIMIT 1
        '''
        
        latest_df = pd.read_sql_query(latest_query, conn)
        
        if not latest_df.empty:
            latest_data = latest_df.iloc[0].to_dict()
            
            # Convert timestamp to string for JSON serialization
            if 'timestamp' in latest_data:
                latest_data['timestamp'] = str(latest_data['timestamp'])
            
            # Get connection status
            connection_status = logger.connect() if not logger.client else True
            
            return jsonify({
                'success': True,
                'data': latest_data,
                'connection_status': connection_status,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No data available',
                'connection_status': False
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'connection_status': False
        })
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/historical_data')
def get_historical_data():
    """Get historical data for charts"""
    try:
        hours = request.args.get('hours', 24, type=int)
        start_time = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(DATABASE_NAME)
        
        query = '''
            SELECT timestamp, V1_N_Voltage, V2_N_Voltage, V3_N_Voltage,
                   L1_Current, L2_Current, L3_Current,
                   Total_Active_Power, Total_Reactive_Power, Total_Apparent_Power,
                   Total_Power_Factor, Frequency
            FROM pac3200_readings 
            WHERE timestamp >= ? 
            ORDER BY timestamp ASC
        '''
        
        df = pd.read_sql_query(query, conn, params=[start_time])
        
        if not df.empty:
            # Convert timestamp to string for JSON serialization
            df['timestamp'] = df['timestamp'].astype(str)
            
            return jsonify({
                'success': True,
                'data': df.to_dict('records')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No historical data available'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/collect_data')
def collect_data():
    """Collect new data from PAC3200"""
    try:
        if not logger.client:
            if not logger.connect():
                return jsonify({
                    'success': False,
                    'message': 'Failed to connect to PAC3200'
                })
        
        record_id = logger.collect_and_store_data()
        
        if record_id:
            return jsonify({
                'success': True,
                'message': f'Data collected successfully (Record ID: {record_id})',
                'record_id': record_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to collect data'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/statistics')
def get_statistics():
    """Get statistical summary of data"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        
        # Get basic statistics
        stats_query = '''
            SELECT 
                COUNT(*) as total_records,
                MIN(timestamp) as first_reading,
                MAX(timestamp) as last_reading,
                ROUND(AVG(V1_N_Voltage), 2) as avg_v1,
                ROUND(AVG(V2_N_Voltage), 2) as avg_v2,
                ROUND(AVG(V3_N_Voltage), 2) as avg_v3,
                ROUND(AVG(Total_Active_Power), 2) as avg_power,
                ROUND(AVG(Frequency), 2) as avg_frequency
            FROM pac3200_readings
        '''
        
        stats_df = pd.read_sql_query(stats_query, conn)
        
        if not stats_df.empty:
            stats = stats_df.iloc[0].to_dict()
            
            # Convert timestamps to strings
            if 'first_reading' in stats:
                stats['first_reading'] = str(stats['first_reading']) if stats['first_reading'] else None
            if 'last_reading' in stats:
                stats['last_reading'] = str(stats['last_reading']) if stats['last_reading'] else None
            
            return jsonify({
                'success': True,
                'statistics': stats
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No statistics available'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/connection_status')
def get_connection_status():
    """Get current connection status"""
    try:
        if logger.client and logger.client.is_socket_open():
            status = True
            message = "Connected"
        else:
            status = False
            message = "Disconnected"
        
        return jsonify({
            'success': True,
            'connected': status,
            'message': message,
            'host': PAC3200_IP,
            'port': PAC3200_PORT
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'connected': False,
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)