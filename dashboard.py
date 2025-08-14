from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import threading
import time
from pac3200_logger import PAC3200SQLLogger  # Import your existing logger

app = Flask(__name__)

# Configuration
DATABASE_NAME = 'pac3200_readings.db'
PAC3200_IP = '192.168.0.101'  # Replace with your PAC3200 IP address
PAC3200_PORT = 502
UNIT_ID = 1

# Global variables for data collection
logger_instance = None
data_collection_thread = None
is_collecting = False

def init_database_if_not_exists():
    """Initialize database if it doesn't exist"""
    if not os.path.exists(DATABASE_NAME):
        logger = PAC3200SQLLogger(
            host=PAC3200_IP, 
            port=PAC3200_PORT, 
            unit_id=UNIT_ID,
            db_name=DATABASE_NAME
        )
        print("Database initialized for dashboard")

def background_data_collection():
    """Background thread for continuous data collection"""
    global logger_instance, is_collecting
    
    logger_instance = PAC3200SQLLogger(
        host=PAC3200_IP, 
        port=PAC3200_PORT, 
        unit_id=UNIT_ID,
        db_name=DATABASE_NAME
    )
    
    if logger_instance.connect():
        print("Connected to PAC3200 for background data collection")
        while is_collecting:
            try:
                logger_instance.collect_and_store_data()
                time.sleep(30)  # Collect data every 30 seconds
            except Exception as e:
                print(f"Error in background collection: {e}")
                time.sleep(60)  # Wait longer on error
    else:
        print("Failed to connect to PAC3200 for background collection")

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/latest_data')
def get_latest_data():
    """API endpoint to get latest readings"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        
        # Get latest reading
        query = """
            SELECT * FROM pac3200_readings 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            latest = df.iloc[0].to_dict()
            # Convert timestamp to string for JSON serialization
            if 'timestamp' in latest:
                latest['timestamp'] = str(latest['timestamp'])
            
            # Replace NaN values with None for JSON serialization
            for key, value in latest.items():
                if pd.isna(value):
                    latest[key] = None
                    
            return jsonify(latest)
        else:
            return jsonify({"error": "No data available"})
            
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/historical_data')
def get_historical_data():
    """API endpoint to get historical data for charts"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        conn = sqlite3.connect(DATABASE_NAME)
        
        # Get historical data
        query = f"""
            SELECT timestamp, V1_N_Voltage, V2_N_Voltage, V3_N_Voltage,
                   L1_Current, L2_Current, L3_Current,
                   Total_Active_Power, Total_Reactive_Power, Total_Apparent_Power,
                   Frequency, Total_Power_Factor
            FROM pac3200_readings 
            WHERE timestamp >= datetime('now', '-{hours} hours')
            ORDER BY timestamp DESC 
            LIMIT {limit}
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            # Convert to list of dictionaries for JSON
            data = df.to_dict('records')
            
            # Convert timestamps and handle NaN values
            for record in data:
                if 'timestamp' in record:
                    record['timestamp'] = str(record['timestamp'])
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
            
            return jsonify(data)
        else:
            return jsonify([])
            
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/statistics')
def get_statistics():
    """API endpoint to get basic statistics"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        
        # Get statistics for the last 24 hours
        query = """
            SELECT 
                COUNT(*) as total_records,
                ROUND(AVG(V1_N_Voltage), 2) as avg_v1_voltage,
                ROUND(AVG(V2_N_Voltage), 2) as avg_v2_voltage,
                ROUND(AVG(V3_N_Voltage), 2) as avg_v3_voltage,
                ROUND(AVG(L1_Current), 2) as avg_l1_current,
                ROUND(AVG(L2_Current), 2) as avg_l2_current,
                ROUND(AVG(L3_Current), 2) as avg_l3_current,
                ROUND(AVG(Total_Active_Power), 2) as avg_total_power,
                ROUND(AVG(Frequency), 2) as avg_frequency,
                ROUND(MIN(V1_N_Voltage), 2) as min_v1_voltage,
                ROUND(MAX(V1_N_Voltage), 2) as max_v1_voltage,
                ROUND(MIN(Total_Active_Power), 2) as min_total_power,
                ROUND(MAX(Total_Active_Power), 2) as max_total_power
            FROM pac3200_readings 
            WHERE timestamp >= datetime('now', '-24 hours')
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            stats = df.iloc[0].to_dict()
            
            # Handle NaN values
            for key, value in stats.items():
                if pd.isna(value):
                    stats[key] = 0
                    
            return jsonify(stats)
        else:
            return jsonify({"total_records": 0})
            
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/start_collection')
def start_collection():
    """API endpoint to start background data collection"""
    global data_collection_thread, is_collecting
    
    if not is_collecting:
        is_collecting = True
        data_collection_thread = threading.Thread(target=background_data_collection)
        data_collection_thread.daemon = True
        data_collection_thread.start()
        return jsonify({"status": "started", "message": "Data collection started"})
    else:
        return jsonify({"status": "already_running", "message": "Data collection already running"})

@app.route('/api/stop_collection')
def stop_collection():
    """API endpoint to stop background data collection"""
    global is_collecting, logger_instance
    
    if is_collecting:
        is_collecting = False
        if logger_instance:
            logger_instance.disconnect()
        return jsonify({"status": "stopped", "message": "Data collection stopped"})
    else:
        return jsonify({"status": "not_running", "message": "Data collection not running"})

@app.route('/api/collection_status')
def collection_status():
    """API endpoint to get data collection status"""
    return jsonify({"is_collecting": is_collecting})

@app.route('/api/recent_readings')
def get_recent_readings():
    """API endpoint to get recent readings for table display"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect(DATABASE_NAME)
        
        query = f"""
            SELECT id, timestamp, 
                   ROUND(V1_N_Voltage, 2) as V1_N_Voltage,
                   ROUND(V2_N_Voltage, 2) as V2_N_Voltage,
                   ROUND(V3_N_Voltage, 2) as V3_N_Voltage,
                   ROUND(L1_Current, 2) as L1_Current,
                   ROUND(L2_Current, 2) as L2_Current,
                   ROUND(L3_Current, 2) as L3_Current,
                   ROUND(Total_Active_Power, 2) as Total_Active_Power,
                   ROUND(Frequency, 2) as Frequency
            FROM pac3200_readings 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            data = df.to_dict('records')
            
            # Convert timestamps and handle NaN values
            for record in data:
                if 'timestamp' in record:
                    record['timestamp'] = str(record['timestamp'])
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
            
            return jsonify(data)
        else:
            return jsonify([])
            
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    # Initialize database
    init_database_if_not_exists()
    
    print("Starting PAC3200 Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)