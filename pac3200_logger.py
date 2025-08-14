import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import logging

# Set up logging
logging.basicConfig(filename='modbus_tcp_debug.log', level=logging.DEBUG)

class PAC3200SQLLogger:
    def __init__(self, host='192.168.0.101', port=502, unit_id=1, timeout=3, db_name='pac3200_data.db'):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.client = None
        self.db_name = db_name
        
        # SENTRON PAC3200 Register Map (0-based addresses)
        # Note: Using SQL-safe column names (no spaces, no special characters)
        self.registers = {
            # Voltage Measurements
            'V1_N_Voltage': 1,      # Phase 1 to Neutral
            'Maximum_Voltage_V1_n': 75,
            'V2_N_Voltage': 3,      # Phase 2 to Neutral
            'Maximum_Voltage_V2_n': 77,  
            'V3_N_Voltage': 5,      # Phase 3 to Neutral
            'Maximum_Voltage_V3_n': 79,
            'V1_V2_Voltage': 7,     # Phase 1 to Phase 2
            'Maximum_Voltage_V1_2': 81,
            'V2_V3_Voltage': 9,     # Phase 2 to Phase 3
            'Maximum_Voltage_V2_3': 83,
            'V3_V1_Voltage': 11,     # Phase 3 to Phase 1
            'Maximum_Voltage_V3_1': 85,
            'THD_R_Voltage_1': 43,
            'THD_R_Voltage_2': 45,
            'THD_R_Voltage_3': 47,
            'Average_Voltage_Vph_n': 57,
            'Average_Voltage_Vph_ph': 59,
            'Amplitude_Unbalance_Voltage': 71,
            'Maximum_THD_R_Voltage_1': 117,
            'Maximum_THD_R_Voltage_2': 119,
            'Maximum_THD_R_Voltage_3': 121,
            
            # Current Measurements  
            'L1_Current': 13,        # Phase 1 Current
            'Maximum_Current_1': 87,
            'L2_Current': 15,        # Phase 2 Current
            'Maximum_Current_2': 89,
            'L3_Current': 17,        # Phase 3 Current
            'Maximum_Current_3': 91,
            'Average_Current': 61,            
            'THD_R_Current_1': 49,
            'THD_R_Current_2': 51,
            'THD_R_Current_3': 53,
            'Amplitude_Unbalance_Current': 73,
            'Maximum_THD_R_Current_1': 123,
            'Maximum_THD_R_Current_2': 125,
            'Maximum_THD_R_Current_3': 127,
            'Max_Frequency': 129,
            'Max_Average_Voltage_Vph_n': 131,
            'Max_Average_Voltage_Vph_ph': 133,
            'Max_Average_Current': 135,
            'Max_Total_Apparent_Power': 137,
            'Max_Total_Active_Power': 139,
            'Max_Total_Reactive_Power': 141,
            'Maximum_Total_Power_Factor': 143,
            'Minimum_Voltage_V1_n': 145,
            'Minimum_Voltage_V2_n': 147,
            'Minimum_Voltage_V3_n': 149,
            'Minimum_Voltage_V1_2': 151,
            'Minimum_Voltage_V2_3': 153,
            'Minimum_Voltage_V3_1': 155,
            'Minimum_Current_1': 157,
            'Minimum_Current_2': 159,
            'Minimum_Current_3': 161,
            'Minimum_Apparent_Power_1': 163,
            'Minimum_Apparent_Power_2': 165,
            'Minimum_Apparent_Power_3': 167,
            'Minimum_Active_Power_1': 169,
            'Minimum_Active_Power_2': 171,
            'Minimum_Active_Power_3': 173,
            'Minimum_Reactive_Power_1': 175,
            'Minimum_Reactive_Power_2': 177,
            'Minimum_Reactive_Power_3': 179,
            'Minimum_Power_Factor_1': 181,
            'Minimum_Power_Factor_2': 183,
            'Minimum_Power_Factor_3': 185,
            'Min_Frequency': 187,
            'Min_Average_Voltage_Vph_n': 189,
            'Min_Average_Voltage_Vph_ph': 191,
            'Min_Average_Current': 193,
            'Min_Total_Apparent_Power': 195,
            'Min_Total_Active_Power': 197,
            'Min_Total_Reactive_Power': 199,
            'Minimum_Total_Power_Factor': 201,
            
            # Power Measurements
            'L1_Active_Power': 25,
            'Maximum_Active_Power_1': 99,   
            'L2_Active_Power': 27,
            'Maximum_Active_Power_2': 101,   
            'L3_Active_Power': 29,   # Fixed: was 23, should be 29
            'Maximum_Active_Power_3': 103,
            'Total_Active_Power': 65,
            
            'L1_Reactive_Power': 31,
            'Maximum_Reactive_Power_1': 105,  
            'L2_Reactive_Power': 33,  
            'Maximum_Reactive_Power_2': 107,
            'L3_Reactive_Power': 35, 
            'Maximum_Reactive_Power_3': 109,
            'Total_Reactive_Power': 67,
            
            'L1_Apparent_Power': 19,
            'Maximum_Apparent_Power_1': 93,
            'L2_Apparent_Power': 21,
            'Maximum_Apparent_Power_2': 95,
            'L3_Apparent_Power': 23,
            'Maximum_Apparent_Power_3': 97,
            'Total_Apparent_Power': 63,
            
            # Power Factor
            'L1_Power_Factor': 37,
            'Maximum_Power_Factor_1': 111,  
            'L2_Power_Factor': 39,  
            'Maximum_Power_Factor_2': 113,
            'L3_Power_Factor': 41,  
            'Maximum_Power_Factor_3': 115,
            'Total_Power_Factor': 69,
            
            # Frequency
            'Frequency': 55,        
            
            # Energy Measurements
            'Total_Active_Energy': 801,    
            'Total_Reactive_Energy': 805,  
        }
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with tables"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Create readings table with SQL-safe column names
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pac3200_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    V1_N_Voltage REAL,
                    V2_N_Voltage REAL,
                    V3_N_Voltage REAL,
                    V1_V2_Voltage REAL,
                    V2_V3_Voltage REAL,
                    V3_V1_Voltage REAL,
                    THD_R_Voltage_1 REAL,
                    Maximum_THD_R_Voltage_1 REAL,         
                    THD_R_Voltage_2 REAL,
                    Maximum_THD_R_Voltage_2 REAL,
                    THD_R_Voltage_3 REAL,
                    Maximum_THD_R_Voltage_3 REAL,
                    Average_Voltage_Vph_n REAL,
                    Max_Average_Voltage_Vph_n REAL,
                    Min_Average_Voltage_Vph_n REAL,     
                    Average_Voltage_Vph_ph REAL,
                    Max_Average_Voltage_Vph_ph REAL,
                    Min_Average_Voltage_Vph_ph REAL,
                    Amplitude_Unbalance_Voltage REAL,
                    Maximum_Voltage_V1_n REAL,
                    Minimum_Voltage_V1_n REAL,
                    Maximum_Voltage_V2_n REAL,
                    Minimum_Voltage_V2_n REAL,                    
                    Maximum_Voltage_V3_n REAL,
                    Minimum_Voltage_V3_n REAL,
                    Maximum_Voltage_V1_2 REAL,
                    Minimum_Voltage_V1_2 REAL,
                    Maximum_Voltage_V2_3 REAL,
                    Minimum_Voltage_V2_3 REAL,
                    Maximum_Voltage_V3_1 REAL,
                    Minimum_Voltage_V3_1 REAL,
                    L1_Current REAL,
                    L2_Current REAL,
                    L3_Current REAL,
                    THD_R_Current_1 REAL,
                    Maximum_THD_R_Current_1 REAL,      
                    THD_R_Current_2 REAL,
                    Maximum_THD_R_Current_2 REAL,
                    THD_R_Current_3 REAL,
                    Maximum_THD_R_Current_3 REAL,      
                    Average_Current REAL,
                    Max_Average_Current REAL,
                    Min_Average_Current REAL,
                    Amplitude_Unbalance_Current REAL,
                    Maximum_Current_1 REAL,
                    Minimum_Current_1 REAL,
                    Maximum_Current_2 REAL,
                    Minimum_Current_2 REAL, 
                    Maximum_Current_3 REAL,
                    Minimum_Current_3 REAL,                   
                    L1_Active_Power REAL,
                    Maximum_Active_Power_1 REAL,
                    Minimum_Active_Power_1 REAL,
                    L2_Active_Power REAL,
                    Maximum_Active_Power_2 REAL,
                    Minimum_Active_Power_2 REAL, 
                    L3_Active_Power REAL,
                    Maximum_Active_Power_3 REAL,
                    Minimum_Active_Power_3 REAL,
                    Total_Active_Power REAL,
                    Max_Total_Active_Power REAL,
                    Min_Total_Active_Power REAL,
                    L1_Reactive_Power REAL,
                    Maximum_Reactive_Power_1 REAL,
                    Minimum_Reactive_Power_1 REAL,
                    L2_Reactive_Power REAL,
                    Maximum_Reactive_Power_2 REAL,
                    Minimum_Reactive_Power_2 REAL,
                    L3_Reactive_Power REAL,
                    Maximum_Reactive_Power_3 REAL,
                    Minimum_Reactive_Power_3 REAL,
                    Total_Reactive_Power REAL,
                    Max_Total_Reactive_Power REAL,
                    Min_Total_Reactive_Power REAL,
                    L1_Apparent_Power REAL,
                    Maximum_Apparent_Power_1 REAL,
                    Minimum_Apparent_Power_1 REAL,      
                    L2_Apparent_Power REAL,
                    Maximum_Apparent_Power_2 REAL,
                    Minimum_Apparent_Power_2 REAL,       
                    L3_Apparent_Power REAL,
                    Maximum_Apparent_Power_3 REAL,
                    Minimum_Apparent_Power_3 REAL,
                    Total_Apparent_Power REAL,
                    Max_Total_Apparent_Power REAL,
                    Min_Total_Apparent_Power REAL,
                    L1_Power_Factor REAL,
                    Maximum_Power_Factor_1 REAL,
                    Minimum_Power_Factor_1 REAL,
                    L2_Power_Factor REAL,
                    Maximum_Power_Factor_2 REAL,
                    Minimum_Power_Factor_2 REAL,
                    L3_Power_Factor REAL,
                    Maximum_Power_Factor_3 REAL,
                    Minimum_Power_Factor_3 REAL,
                    Total_Power_Factor REAL,
                    Maximum_Total_Power_Factor REAL,
                    Minimum_Total_Power_Factor REAL,
                    Frequency REAL,
                    Max_Frequency REAL,
                    Min_Frequency REAL,
                    Total_Active_Energy REAL,
                    Total_Reactive_Energy REAL
                )
            ''')
            
            # Create parameter definitions table for reference
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parameter_definitions (
                    parameter_name TEXT PRIMARY KEY,
                    register_address INTEGER,
                    unit TEXT,
                    description TEXT
                )
            ''')
            
            # Insert parameter definitions with corrected register addresses
            param_data = [
                ('V1_N_Voltage', 2, 'V', 'Phase 1 to Neutral Voltage'),
                ('Maximum_Voltage_V1_n', 76, 'V', 'phase 1 to neutral max voltage'),
                ('Minimum_Voltage_V1_n', 146, 'V', 'phase 1 to neutral min voltage'),
                ('V2_N_Voltage', 4, 'V', 'Phase 2 to Neutral Voltage'),    
                ('Maximum_Voltage_V2_n', 78, 'V', 'phase 2 to neutral max voltage'),
                ('Minimum_Voltage_V2_n', 148, 'V', 'phase 2 to neutral min voltage'),
                ('V3_N_Voltage', 6, 'V', 'Phase 3 to Neutral Voltage'),
                ('Maximum_Voltage_V3_n', 80, 'V', 'phase 3 to neutral max voltage'),
                ('Minimum_Voltage_V3_n', 150, 'V', 'phase 3 to neutral min voltage'),
                ('V1_V2_Voltage', 8, 'V', 'Phase 1 to Phase 2 Voltage'),
                ('Maximum_Voltage_V1_V2', 82, 'V', 'Phase 1 to phase 2 max Voltage'),
                ('Minimum_Voltage_V1_V2', 152, 'V', 'phase 1 to phase 2 min voltage'),
                ('V2_V3_Voltage', 10, 'V', 'Phase 2 to Phase 3 Voltage'),
                ('Maximum_Voltage_V2_V3', 84, 'V', 'phase 2 to phase 3 max voltage'),
                ('Minimum_Voltage_V2_V3', 154, 'V', 'phase 2 to phase 3 min voltage'),
                ('V3_V1_Voltage', 12, 'V', 'Phase 3 to Phase 1 Voltage'),
                ('Maximum_Voltage_V3_V1', 86, 'V', 'phase 3 to phase 1 max voltage'),
                ('Minimum_Voltage_V3_V1', 156, 'V', 'phase 3 to phase 1 min voltage'),
                ('THD_R_Voltage_1', 44, '%', 'THD-R Voltage 1 percentage'),
                ('Maximum_THD_R_Voltage_1', 118, '%', 'Maximum THD-R Voltage 1 percentage'),
                ('THD_R_Voltage_2', 46, '%', 'THD-R Voltage 2 percentage'),
                ('Maximum_THD_R_Voltage_2', 120, '%', 'Maximum THD-R Voltage 2 percentage'),
                ('THD_R_Voltage_3', 48, '%', 'THD-R Voltage 3 percentage'),
                ('Maximum_THD_R_Voltage_3', 122, '%', 'Maximum THD-R Voltage 3 percentage'),
                ('Average_Voltage_Vph_n', 58, 'V', 'Average Voltage Vph-n'),
                ('Max_Average_Voltage_Vph_n', 132, 'V', 'Max. Average Voltage Vph-n'),
                ('Min_Average_Voltage_Vph_n', 190, 'V', 'Min. Average Voltage Vph-n'),
                ('Average_Voltage_Vph_ph', 60, 'V', 'Average Voltage Vph-ph'),
                ('Max_Average_Voltage_Vph_ph', 134, 'V', 'Max. Average Voltage Vph-ph'),
                ('Min_Average_Voltage_Vph_ph', 192, 'V', 'Min. Average Voltage Vph-ph'),
                ('Amplitude_Unbalance_Voltage', 72, '%', 'Amplitude Unbalance - Voltage'),
                ('L1_Current', 14, 'A', 'Phase 1 Current'),
                ('Maximum_Current_1', 88, 'A', 'Maximum Current 1'),
                ('Minimum_Current_1', 158, 'A', 'Minimum Current 1'),   
                ('L2_Current', 16, 'A', 'Phase 2 Current'),
                ('Maximum_Current_2', 90, 'A', 'Maximum Current 2'),
                ('Minimum_Current_2', 160, 'A', 'Minimum Current 2'),
                ('L3_Current', 18, 'A', 'Phase 3 Current'),
                ('Maximum_Current_3', 92, 'A', 'Maximum Current 3'),
                ('Minimum_Current_3', 162, 'A', 'Minimum Current 3'),
                ('Average_Current', 62, 'A', 'Average Current'),
                ('Max_Average_Current', 136, 'A', 'Max. Average Current'),
                ('Min_Average_Current', 194, 'A', 'Min. Average Current'),
                ('THD_R_Current_1', 50, '%', 'THD-R Current 1 percentage'),
                ('Maximum_THD_R_Current_1', 124, '%', 'Maximum THD-R Current 1 percentage'),
                ('THD_R_Current_2', 52, '%', 'THD-R Current 2 percentage'),
                ('Maximum_THD_R_Current_2', 126, '%', 'Maximum THD-R Current 2 percentage'),
                ('THD_R_Current_3', 54, '%', 'THD-R Current 3 percentage'),
                ('Maximum_THD_R_Current_3', 128, '%', 'Maximum THD-R Current 3 percentage'),
                ('Amplitude_Unbalance_Current', 74, '%', 'Amplitude Unbalance - Current'),                
                ('L1_Active_Power', 26, 'W', 'Phase 1 Active Power'),
                ('Maximum_Active_Power_1', 100, 'W', 'Maximum Active Power 1'),
                ('Minimum_Active_Power_1', 170, 'W', 'Minimum Active Power 1'),
                ('L2_Active_Power', 28, 'W', 'Phase 2 Active Power'),
                ('Maximum_Active_Power_2', 102, 'W', 'Maximum Active Power 2'),
                ('Minimum_Active_Power_2', 172, 'W', 'Minimum Active Power 2'),
                ('L3_Active_Power', 30, 'W', 'Phase 3 Active Power'),
                ('Maximum_Active_Power_3', 104, 'W', 'Maximum Active Power 3'),
                ('Minimum_Active_Power_3', 174, 'W', 'Minimum Active Power 3'),
                ('Total_Active_Power', 66, 'W', 'Total Active Power'),
                ('Max_Total_Active_Power', 140, 'W', 'Max. Total Active Power'),
                ('Min_Total_Active_Power', 198, 'W', 'Min. Total Active Power'),
                ('L1_Reactive_Power', 32, 'VAR', 'Phase 1 Reactive Power'),
                ('Maximum_Reactive_Power_1', 106, 'VAR', 'Maximum Reactive Power 1'),
                ('Minimum_Reactive_Power_1', 176, 'VAR', 'Minimum Reactive Power 1'),
                ('L2_Reactive_Power', 34, 'VAR', 'Phase 2 Reactive Power'),
                ('Maximum_Reactive_Power_2', 108, 'VAR', 'Maximum Reactive Power 2'),
                ('Minimum_Reactive_Power_2', 178, 'VAR', 'Minimum Reactive Power 2'),
                ('L3_Reactive_Power', 36, 'VAR', 'Phase 3 Reactive Power'),
                ('Maximum_Reactive_Power_3', 110, 'VAR', 'Maximum Reactive Power 3'),
                ('Minimum_Reactive_Power_3', 180, 'VAR', 'Minimum Reactive Power 3'),
                ('Total_Reactive_Power', 68, 'VAR', 'Total Reactive Power'),
                ('Max_Total_Reactive_Power', 142, 'VAR', 'Max. Total Reactive Power'),
                ('Min_Total_Reactive_Power', 200, 'VAR', 'Min. Total Reactive Power'),
                ('L1_Apparent_Power', 20, 'VA', 'Phase 1 Apparent Power'),
                ('Maximum_Apparent_Power_1', 94, 'VA', 'Maximum Apparent Power 1'),
                ('Minimum_Apparent_Power_1', 164, 'VA', 'Minimum Apparent Power 1'),
                ('L2_Apparent_Power', 22, 'VA', 'Phase 2 Apparent Power'),
                ('Maximum_Apparent_Power_2', 96, 'VA', 'Maximum Apparent Power 2'),
                ('Minimum_Apparent_Power_2', 166, 'VA', 'Minimum Apparent Power 2'),
                ('L3_Apparent_Power', 24, 'VA', 'Phase 3 Apparent Power'),
                ('Maximum_Apparent_Power_3', 98, 'VA', 'Maximum Apparent Power 3'),
                ('Minimum_Apparent_Power_3', 168, 'VA', 'Minimum Apparent Power 3'),
                ('Total_Apparent_Power', 64, 'VA', 'Total Apparent Power'),
                ('Max_Total_Apparent_Power', 138, 'VA', 'Max. Total Apparent Power'),
                ('Min_Total_Apparent_Power', 196, 'VA', 'Min. Total Apparent Power'),
                ('L1_Power_Factor', 38, '', 'Phase 1 Power Factor'),
                ('Maximum_Power_Factor_1', 112, '', 'Maximum Power Factor 1'),
                ('Minimum_Power_Factor_1', 182, '', 'Minimum Power Factor 1'),
                ('L2_Power_Factor', 40, '', 'Phase 2 Power Factor'),
                ('Maximum_Power_Factor_2', 114, '', 'Maximum Power Factor 2'),
                ('Minimum_Power_Factor_2', 184, '', 'Minimum Power Factor 2'),
                ('L3_Power_Factor', 42, '', 'Phase 3 Power Factor'),
                ('Maximum_Power_Factor_3', 116, '', 'Maximum Power Factor 3'),
                ('Minimum_Power_Factor_3', 186, '', 'Minimum Power Factor 3'),
                ('Total_Power_Factor', 70, '', 'Total Power Factor'),
                ('Maximum_Total_Power_Factor', 144, '', 'Maximum Total Power Factor'),
                ('Minimum_Total_Power_Factor', 202, '', 'Minimum Total Power Factor'),
                ('Frequency', 56, 'Hz', 'System Frequency'),
                ('Max_Frequency', 130, 'Hz', 'Max system Frequency'),
                ('Min_Frequency', 188, 'Hz', 'Min system Frequency'),
                ('Total_Active_Energy', 802, 'Wh', 'Total Active Energy'),
                ('Total_Reactive_Energy', 806, 'VARh', 'Total Reactive Energy'),
            ]
            
            cursor.executemany('''
                INSERT OR REPLACE INTO parameter_definitions 
                (parameter_name, register_address, unit, description) 
                VALUES (?, ?, ?, ?)
            ''', param_data)
            
            conn.commit()
            conn.close()
            print(f"✅ Database '{self.db_name}' initialized successfully")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def connect(self):
        """Connect to PAC3200"""
        try:
            self.client = ModbusClient(host=self.host, port=self.port, timeout=self.timeout)
            connection = self.client.connect()
            if connection:
                print(f"✅ Connected to SENTRON PAC3200 at {self.host}:{self.port}")
                return True
            else:
                print(f"❌ Failed to connect to {self.host}:{self.port}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from PAC3200"""
        if self.client:
            self.client.close()
            print("🔌 Disconnected from PAC3200")
    
    def read_float32_register(self, register_address):
        """Read a 32-bit float from PAC3200"""
        try:
            # For pymodbus 2.5.3, use slave parameter instead of unit
            rr = self.client.read_holding_registers(register_address, 2, unit=self.unit_id)
            
            if rr.isError():
                print(f"❌ Modbus Error reading register {register_address}: {rr}")
                return None
                
            decoder = BinaryPayloadDecoder.fromRegisters(
                rr.registers, 
                byteorder=Endian.Big, 
                wordorder=Endian.Big
            )
            
            value = decoder.decode_32bit_float()
            return value
            
        except Exception as e:
            print(f"❌ Error reading register {register_address}: {e}")
            return None
    
    def read_specific_parameters(self, parameter_list):
        """Read specific parameters by name"""
        if not self.client:
            print("❌ Not connected to PAC3200")
            return None
            
        data = {}
        
        for param_name in parameter_list:
            if param_name in self.registers:
                register_addr = self.registers[param_name]
                value = self.read_float32_register(register_addr)
                data[param_name] = value
                if value is not None:
                    print(f"✅ {param_name}: {value:.3f}")
                else:
                    print(f"❌ Failed to read {param_name}")
            else:
                print(f"❌ Parameter '{param_name}' not found in register map")
                
        return data
    
    def read_all_parameters(self):
        """Read all parameters and return as dictionary"""
        if not self.client:
            print("❌ Not connected to PAC3200")
            return None
            
        data = {}
        total_params = len(self.registers)
        successful_reads = 0
        
        print(f"📊 Reading {total_params} parameters from PAC3200...")
        
        for param_name, register_addr in self.registers.items():
            value = self.read_float32_register(register_addr)
            data[param_name] = value
            if value is not None:
                successful_reads += 1
                
        print(f"✅ Successfully read {successful_reads}/{total_params} parameters")
        return data
    
    def save_to_database(self, data):
        """Save readings to database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Filter out None values and prepare data
            valid_data = {k: v for k, v in data.items() if v is not None}
            
            if not valid_data:
                print("❌ No valid data to save")
                return None
            
            # Prepare column names and values
            columns = list(valid_data.keys())
            values = list(valid_data.values())
            
            # Create SQL query
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            query = f'''
                INSERT INTO pac3200_readings ({column_names}) 
                VALUES ({placeholders})
            '''
            
            cursor.execute(query, values)
            conn.commit()
            record_id = cursor.lastrowid
            conn.close()
            
            print(f"✅ Data saved to database (Record ID: {record_id}, {len(valid_data)} parameters)")
            return record_id
            
        except Exception as e:
            print(f"❌ Database save error: {e}")
            return None
    
    def collect_and_store_data(self):
        """Collect data from PAC3200 and store in database"""
        print(f"\n📊 Collecting data from PAC3200...")
        
        # Read all parameters
        data = self.read_all_parameters()
        
        if data:
            # Save to database
            record_id = self.save_to_database(data)
            
            if record_id:
                print(f"✅ Successfully collected and stored data (Record ID: {record_id})")
                return record_id
        
        return None
    
    def query_latest_readings(self, limit=10):
        """Query latest readings from database"""
        try:
            conn = sqlite3.connect(self.db_name)
            
            query = f'''
                SELECT * FROM pac3200_readings 
                ORDER BY timestamp DESC 
                LIMIT {limit}
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None
    
    def query_readings_by_timerange(self, start_time, end_time):
        """Query readings by time range"""
        try:
            conn = sqlite3.connect(self.db_name)
            
            query = '''
                SELECT * FROM pac3200_readings 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            '''
            
            df = pd.read_sql_query(query, conn, params=[start_time, end_time])
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None
    
    def get_parameter_summary(self):
        """Get parameter definitions"""
        try:
            conn = sqlite3.connect(self.db_name)
            
            query = '''
                SELECT parameter_name, register_address, unit, description
                FROM parameter_definitions
                ORDER BY register_address
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None
    
    def display_latest_data(self, limit=5):
        """Display latest readings in tabular format"""
        print(f"\n📋 LATEST {limit} READINGS FROM DATABASE")
        print("=" * 120)
        
        df = self.query_latest_readings(limit)
        
        if df is not None and not df.empty:
            # Select key columns for display
            display_columns = ['timestamp', 'V1_N_Voltage', 'V2_N_Voltage', 'V3_N_Voltage', 
                             'L1_Current', 'L2_Current', 'L3_Current', 'Total_Active_Power', 'Frequency']
            
            # Filter columns that exist in the dataframe
            existing_columns = [col for col in display_columns if col in df.columns]
            
            if existing_columns:
                display_df = df[existing_columns]
                
                # Format numerical columns
                for col in display_df.columns:
                    if col != 'timestamp' and display_df[col].dtype in ['float64', 'int64']:
                        display_df[col] = display_df[col].round(3)
                
                print(display_df.to_string(index=False))
            else:
                # If key columns don't exist, show first few columns
                display_df = df.iloc[:, :8]  # Show first 8 columns
                print(display_df.to_string(index=False))
                
            print(f"\nTotal records in database: {len(df)}")
        else:
            print("❌ No data found in database")
    
    def display_key_parameters(self):
        """Display key electrical parameters from latest reading"""
        df = self.query_latest_readings(1)
        
        if df is not None and not df.empty:
            latest = df.iloc[0]
            print(f"\n⚡ KEY ELECTRICAL PARAMETERS")
            print("=" * 50)
            print(f"Timestamp: {latest.get('timestamp', 'N/A')}")
            print(f"\n🔌 VOLTAGES:")
            print(f"  V1-N: {latest.get('V1_N_Voltage', 'N/A'):.2f} V")
            print(f"  Maximum Voltage V1-n: {latest.get('Maximum_Voltage_V1_n','N/A'):.2f} V")
            print(f"  Minimum Voltage V1-n: {latest.get('Minimum_Voltage_V1_n','N/A'):.2f} V")
            print(f"  V2-N: {latest.get('V2_N_Voltage', 'N/A'):.2f} V")
            print(f"  Maximum Voltage V2-n: {latest.get('Maximum_Voltage_V2_n','N/A'):.2f} V")
            print(f"  Minimum Voltage V2-n: {latest.get('Minimum_Voltage_V2_n','N/A'):.2f} V") 
            print(f"  V3-N: {latest.get('V3_N_Voltage', 'N/A'):.2f} V")
            print(f"  Maximum Voltage V3-n: {latest.get('Maximum_Voltage_V2_n','N/A'):.2f} V")
            print(f"  Minimum Voltage V3-n: {latest.get('Minimum_Voltage_V2_n','N/A'):.2f} V")
            print(f"  V1-V2 Voltage: {latest.get('V1_V2_Voltage','N/A'):.2f} V")
            print(f"  Maximum Voltage V1-V2: {latest.get('Maximum_Voltage_V1_V2','N/A'):.2f} V")
            print(f"  Minimum Voltage V1-V2: {latest.get('Minimum_Voltage_V1_V2','N/A'):.2f} V")
            print(f"  V2-V3 Voltage: {latest.get('V2_V3_Voltage','N/A'):.2f} V")
            print(f"  Maximum Voltage V2-V3: {latest.get('Maximum_Voltage_V2_V3','N/A'):.2f} V")
            print(f"  Minimum Voltage V2-V3: {latest.get('Minimum_Voltage_V2_V3','N/A'):.2f} V")
            print(f"  V3-V1 Voltage: {latest.get('V3_V1_Voltage','N/A'):.2f} V")
            print(f"  Maximum Voltage V3-V1: {latest.get('Maximum_Voltage_V3_V1','N/A'):.2f} V")
            print(f"  Minimum Voltage V3-V1: {latest.get('Minimum_Voltage_V3_V1','N/A'):.2f} V")
            print(f"  THD-R Voltage 1: {latest.get('THD_R_Voltage_1','N/A'):.2f} %")
            print(f"  Maximum THD-R Voltage 1: {latest.get('Maximum_THD_R_Voltage_1','N/A'):.2f} %")
            print(f"  THD-R Voltage 2: {latest.get('THD_R_Voltage_2','N/A'):.2f} %")
            print(f"  Maximum THD-R Voltage 2: {latest.get('Maximum_THD_R_Voltage_2','N/A'):.2f} %")
            print(f"  THD-R Voltage 3: {latest.get('THD_R_Voltage_3','N/A'):.2f} %")
            print(f"  Maximum THD-R Voltage 3: {latest.get('Maximum_THD_R_Voltage_3','N/A'):.2f} %")
            print(f"  Average Voltage Vph-n: {latest.get('Average_Voltage_Vph_n','N/A'):.2f} V")
            print(f"  Max Average Voltage Vph-n: {latest.get('Max_Average_Voltage_Vph_n','N/A'):.2f} v")
            print(f"  Min Average Voltage Vph-n: {latest.get('Min_Average_Voltage_Vph_n','N/A'):.2f} V")
            print(f"  Average Voltage Vph-ph: {latest.get('Average_Voltage_Vph_ph','N/A'):.2f} V")
            print(f"  Max Average Voltage Vph-ph: {latest.get('Max_Average_Voltage_Vph_ph','N/A'):.2f} V")
            print(f"  Min Average Voltage Vph-ph: {latest.get('Min_Average_Voltage_Vph_ph','N/A'):.2f} V")
            print(f"  Amplitude Unbalance Voltage: {latest.get('Amplitude_Unbalance_Voltage','N/A'):.2f} %")
            print(f"\n🔄 CURRENTS:")
            print(f"  L1: {latest.get('L1_Current', 'N/A'):.2f} A")
            print(f"  Maximum Current 1: {latest.get('Maximum_Current_1','N/A'):.2f} A")
            print(f"  Minimum Current 1: {latest.get('Minimum_Current_1','N/A'):.2f} A")
            print(f"  L2: {latest.get('L2_Current', 'N/A'):.2f} A")
            print(f"  Maximum Current 2: {latest.get('Maximum_Current_2','N/A'):.2f} A")
            print(f"  Minimum Current 2: {latest.get('Minimum_Current_1','N/A'):.2f} A")
            print(f"  L3: {latest.get('L3_Current', 'N/A'):.2f} A")
            print(f"  Maximum Current 3: {latest.get('Maximum_Current_3','N/A'):.2f} A")
            print(f"  Minimum Current 3: {latest.get('Minimum_Current_3','N/A'):.2f} A")
            print(f"  Average Current: {latest.get('Average_Current','N/A'):.2f} A")
            print(f"  Max Average Current: {latest.get('Max_Average_Current','N/A'):.2f} A")
            print(f"  Min Average Current: {latest.get('Max_Average_Current','N/A'):.2f} A")
            print(f"  THD-R Current 1: {latest.get('THD_R_Current_1','N/A'):.2f} %")
            print(f"  Maximum THD-R Current 1: {latest.get('Maximum_THD_R_Current_1','N/A'):.2f} %")
            print(f"  THD-R Current 2: {latest.get('THD_R_Current_2','N/A'):.2f} %")
            print(f"  Maximum THD-R Current 2: {latest.get('Maximum_THD_R_Current_2','N/A'):.2f} %")
            print(f"  THD-R Current 3: {latest.get('THD_R_Current_3','N/A'):.2f} %")
            print(f"  Maximum THD-R Current 3: {latest.get('Maximum_THD_R_Current_3','N/A'):.2f} %")
            print(f"  Amplitude Unbalance Current: {latest.get('Amplitude_Unbalance_Current','N/A'):.2f} %")
            print(f"\n⚡ POWER:")
            print(f"  L1 Active Power: {latest.get('L1_Active_Power','N/A'):.2f} W")
            print(f"  Maximum Active Power 1: {latest.get('Maximum_Active_Power_1','N/A'):.2f} W")
            print(f"  Minimum Active Power 1: {latest.get('Minimum_Active_Power_1','N/A'):.2f} W")
            print(f"  L2 Active Power: {latest.get('L2_Active_Power','N/A'):.2f} W")
            print(f"  Maximum Active Power 2: {latest.get('Maximum_Active_Power_2','N/A'):.2f} W")
            print(f"  Minimum Active Power 2: {latest.get('Minimum_Active_Power_2','N/A'):.2f} W")
            print(f"  L3 Active Power: {latest.get('L2_Active_Power','N/A'):.2f} W")
            print(f"  Maximum Active Power 3: {latest.get('Maximum_Active_Power_3','N/A'):.2f} W")
            print(f"  Minimum Active Power 3: {latest.get('Minimum_Active_Power_3','N/A'):.2f} W")
            print(f"  Total Active: {latest.get('Total_Active_Power', 'N/A'):.2f} W")
            print(f"  Max Total Active Power: {latest.get('Max_Total_Active_Power','N/A'):.2f} W")
            print(f"  Min Total Active Power: {latest.get('Min_Total_Active_Power','N/A'):.2f} W")
            print(f"  L1 Reactive Power: {latest.get('L1_Reactive_Power','N/A'):.2f} VAR")
            print(f"  Maximum Reactive Power 1: {latest.get('Maximum_Reactive_Power_1','N/A'):.2f} VAR")
            print(f"  Minimum Reactive Power 1: {latest.get('Minimum_Reactive_Power_1','N/A'):.2f} VAR")
            print(f"  L2 Reactive Power: {latest.get('L2_Reactive_Power','N/A'):.2f} VAR")
            print(f"  Maximum Reactive Power 2: {latest.get('Maximum_Reactive_Power_2','N/A'):.2f} VAR")
            print(f"  Minimum Reactive Power 2: {latest.get('Minimum_Reactive_Power_2','N/A'):.2f} VAR")
            print(f"  L3 Reactive Power: {latest.get('L3_Reactive_Power','N/A'):.2f} VAR")
            print(f"  Maximum Reactive Power 3: {latest.get('Maximum_Reactive_Power_3','N/A'):.2f} VAR")
            print(f"  Minimum Reactive Power 3: {latest.get('Minimum_Reactive_Power_3','N/A'):.2f} VAR")
            print(f"  Total Reactive: {latest.get('Total_Reactive_Power', 'N/A'):.2f} VAR")
            print(f"  Max Total Reactive Power: {latest.get('Max_Total_Reactive_Power','N/A'):.2f} VAR")
            print(f"  Min Total Reactive Power: {latest.get('Min_Total_Reactive_Power','N/A'):.2f} VAR")
            print(f"  L1 Apparent Power: {latest.get('L1_Apparent_Power','N/A'):.2f} VA")
            print(f"  Maximum Apparent Power 1: {latest.get('Maximum_Apparent_Power_1','N/A'):.2f} VA")
            print(f"  Minimum Apparent Power 1: {latest.get('Minimum_Apparent_Power_1','N/A'):.2f} VA")
            print(f"  L2 Apparent Power: {latest.get('L2_Apparent_Power','N/A'):.2f} VA")
            print(f"  Maximum Apparent Power 2: {latest.get('Maximum_Apparent_Power_2','N/A'):.2f} VA")
            print(f"  Minimum Apparent Power 2: {latest.get('Minimum_Apparent_Power_2','N/A'):.2f} VA")
            print(f"  L3 Apparent Power: {latest.get('L3_Apparent_Power','N/A'):.2f} VA")
            print(f"  Maximum Apparent Power 3: {latest.get('Maximum_Apparent_Power_3','N/A'):.2f} VA")
            print(f"  Minimum Apparent Power 3: {latest.get('Minimum_Apparent_Power_3','N/A'):.2f} VA")
            print(f"  Total Apparent: {latest.get('Total_Apparent_Power', 'N/A'):.2f} VA")
            print(f"  Max Total Apparent Power: {latest.get('Max_Total_Apparent_Power','N/A'):.2f} VA")
            print(f"  Min Total Apparent Power: {latest.get('Min_Total_Apparent_Power','N/A'):.2f} VA")
            print(f"\n POWER FACTOR:")
            print(f"  L1 Power Factor: {latest.get('L1_Power_Factor','N/A'):.3f}")
            print(f"  Maximum Power Factor 1: {latest.get('Maximum_Power_Factor_1','N/A'):.3f}")
            print(f"  Minimum Power Factor 1: {latest.get('Minimum_Power_Factor_1','N/A'):.3f}")
            print(f"  L2 Power Factor: {latest.get('L2_Power_Factor','N/A'):.3f}")
            print(f"  Maximum Power Factor 2: {latest.get('Maximum_Power_Factor_2','N/A'):.3f}")
            print(f"  Minimum Power Factor 2: {latest.get('Minimum_Power_Factor_2','N/A'):.3f}")
            print(f"  L3 Power Factor: {latest.get('L3_Power_Factor','N/A'):.3f}")
            print(f"  Maximum Power Factor 3: {latest.get('Maximum_Power_Factor_3','N/A'):.3f}")
            print(f"  Minimum Power Factor 3: {latest.get('Minimum_Power_Factor_3','N/A'):.3f}")
            print(f"  Total Power Factor: {latest.get('Total_Power_Factor', 'N/A'):.3f}")
            print(f"  Maximum Total Power Factor: {latest.get('Maximum_Total_Power_Factor','N/A'):.3f}")
            print(f"  Minimum Total Power Factor: {latest.get('Minimum_Total_Power_Factor','N/A'):.3f}")
            print(f"\n📊 FREQUENCY:")
            print(f"  {latest.get('Frequency', 'N/A'):.2f} Hz")
            print(f"  Max Frequency: {latest.get('Max_Frequency','N/A'):.2f} Hz")
            print(f"  Min Frequency: {latest.get('Min_Frequency','N/A'):.2f} Hz")
    
    def test_connection_and_basic_reads(self):
        """Test connection and read basic parameters"""
        print("\n🔧 TESTING CONNECTION AND BASIC READS")
        print("=" * 50)
        
        # Test basic voltage readings
        basic_params = ['V1_N_Voltage', 'V2_N_Voltage', 'V3_N_Voltage', 'Frequency']
        
        for param in basic_params:
            if param in self.registers:
                register_addr = self.registers[param]
                print(f"Testing {param} (Register {register_addr})...", end=" ")
                value = self.read_float32_register(register_addr)
                if value is not None:
                    print(f"✅ {value:.3f}")
                else:
                    print("❌ Failed")
            else:
                print(f"❌ {param} not found in register map")
    
    def continuous_data_logging(self, interval=60):
        """Continuously log data to database"""
        print(f"\n🔄 Starting continuous data logging (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while True:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n⏰ {timestamp}")
                
                record_id = self.collect_and_store_data()
                
                if record_id:
                    # Display key parameters
                    self.display_key_parameters()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Data logging stopped by user")

def main():
    # Configuration
    PAC3200_IP = '192.168.0.101'  # Replace with your PAC3200 IP address
    PAC3200_PORT = 502
    UNIT_ID = 1
    DATABASE_NAME = 'pac3200_readings.db'
    
    # Create PAC3200 SQL Logger instance
    logger = PAC3200SQLLogger(
        host=PAC3200_IP, 
        port=PAC3200_PORT, 
        unit_id=UNIT_ID,
        db_name=DATABASE_NAME
    )
    
    try:
        # Connect to PAC3200
        if not logger.connect():
            print("\n🔧 Connection failed. Please check:")
            print("  1. PAC3200 IP address is correct")
            print("  2. Network connectivity")
            print("  3. Modbus TCP is enabled on PAC3200")
            print("  4. Unit ID is correct")
            return
        
        print("\n🎯 PAC3200 SQL Data Logger Menu")
        print("=" * 40)
        print("1. Test connection and basic reads")
        print("2. Collect single reading and store")
        print("3. Display latest readings from database")
        print("4. Show parameter definitions")
        print("5. Start continuous logging")
        print("6. Query data by time range")
        print("7. Read specific parameters")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            # Test connection and basic reads
            logger.test_connection_and_basic_reads()
            
        elif choice == '2':
            # Single reading
            logger.collect_and_store_data()
            logger.display_key_parameters()
            
        elif choice == '3':
            # Display latest readings
            limit = int(input("Enter number of records to display (default 10): ") or 10)
            logger.display_latest_data(limit)
            
        elif choice == '4':
            # Show parameter definitions
            print("\n📋 PARAMETER DEFINITIONS")
            print("=" * 80)
            df = logger.get_parameter_summary()
            if df is not None:
                print(df.to_string(index=False))
            
        elif choice == '5':
            # Continuous logging
            interval = int(input("Enter logging interval in seconds (default 60): ") or 60)
            logger.continuous_data_logging(interval)
            
        elif choice == '6':
            # Query by time range
            print("Enter time range (YYYY-MM-DD HH:MM:SS format)")
            start_time = input("Start time: ")
            end_time = input("End time: ")
            
            df = logger.query_readings_by_timerange(start_time, end_time)
            if df is not None and not df.empty:
                print(f"\n📋 READINGS FROM {start_time} TO {end_time}")
                print("=" * 120)
                # Show only first 10 columns for readability
                display_df = df.iloc[:, :10]
                print(display_df.to_string(index=False))
                print(f"\nTotal records found: {len(df)}")
            else:
                print("❌ No data found for the specified time range")
        
        elif choice == '7':
            # Read specific parameters
            print("\nAvailable parameters:")
            print("Basic: V1_N_Voltage, V2_N_Voltage, V3_N_Voltage")
            print("       L1_Current, L2_Current, L3_Current")
            print("       Total_Active_Power, Frequency")
            print("\nEnter parameter names separated by commas:")
            param_input = input("Parameters: ").strip()
            
            if param_input:
                param_list = [p.strip() for p in param_input.split(',')]
                data = logger.read_specific_parameters(param_list)
                
                if data:
                    print("\n📊 PARAMETER VALUES:")
                    print("-" * 40)
                    for param, value in data.items():
                        if value is not None:
                            print(f"{param}: {value:.3f}")
                        else:
                            print(f"{param}: Failed to read")
        
        else:
            print("❌ Invalid choice")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        logger.disconnect()

def run_sql_queries():
    """Run example SQL queries on the database"""
    db_name = 'pac3200_readings.db'
    
    try:
        conn = sqlite3.connect(db_name)
        
        print("\n📊 SQL QUERY EXAMPLES")
        print("=" * 50)
        
        # Query 1: Latest readings
        print("\n1. Latest 5 readings:")
        df1 = pd.read_sql_query('''
            SELECT timestamp, V1_N_Voltage, V2_N_Voltage, V3_N_Voltage, 
                   Total_Active_Power, Frequency 
            FROM pac3200_readings 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''', conn)
        print(df1.to_string(index=False))
        
        # Query 2: Average values
        print("\n2. Average values:")
        df2 = pd.read_sql_query('''
            SELECT 
                ROUND(AVG(V1_N_Voltage), 2) as Avg_V1_Voltage,
                ROUND(AVG(V2_N_Voltage), 2) as Avg_V2_Voltage,
                ROUND(AVG(V3_N_Voltage), 2) as Avg_V3_Voltage,
                ROUND(AVG(Total_Active_Power), 2) as Avg_Power,
                COUNT(*) as Total_Records
            FROM pac3200_readings
        ''', conn)
        print(df2.to_string(index=False))
        
        # Query 3: Voltage statistics
        print("\n3. Voltage statistics:")
        df3 = pd.read_sql_query('''
            SELECT 
                'V1-N' as Phase,
                ROUND(MIN(V1_N_Voltage), 2) as Min_V,
                ROUND(MAX(V1_N_Voltage), 2) as Max_V,
                ROUND(AVG(V1_N_Voltage), 2) as Avg_V
            FROM pac3200_readings
            WHERE V1_N_Voltage IS NOT NULL
            UNION ALL
            SELECT 
                'V2-N' as Phase,
                ROUND(MIN(V2_N_Voltage), 2) as Min_V,
                ROUND(MAX(V2_N_Voltage), 2) as Max_V,
                ROUND(AVG(V2_N_Voltage), 2) as Avg_V
            FROM pac3200_readings
            WHERE V2_N_Voltage IS NOT NULL
            UNION ALL
            SELECT 
                'V3-N' as Phase,
                ROUND(MIN(V3_N_Voltage), 2) as Min_V,
                ROUND(MAX(V3_N_Voltage), 2) as Max_V,
                ROUND(AVG(V3_N_Voltage), 2) as Avg_V
            FROM pac3200_readings
            WHERE V3_N_Voltage IS NOT NULL
        ''', conn)
        print(df3.to_string(index=False))
        
        conn.close()
        
    except Exception as e:
        print(f"❌ SQL Query error: {e}")

# Additional utility functions
def backup_database(source_db='pac3200_readings.db', backup_name=None):
    """Backup database"""
    if backup_name is None:
        backup_name = f"pac3200_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        import shutil
        shutil.copy2(source_db, backup_name)
        print(f"✅ Database backed up to: {backup_name}")
    except Exception as e:
        print(f"❌ Backup error: {e}")

def export_to_csv(db_name='pac3200_readings.db', csv_name=None):
    """Export database to CSV"""
    if csv_name is None:
        csv_name = f"pac3200_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    try:
        conn = sqlite3.connect(db_name)
        df = pd.read_sql_query("SELECT * FROM pac3200_readings ORDER BY timestamp DESC", conn)
        df.to_csv(csv_name, index=False)
        conn.close()
        print(f"✅ Data exported to: {csv_name}")
        print(f"Records exported: {len(df)}")
    except Exception as e:
        print(f"❌ Export error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'sql':
            run_sql_queries()
        elif sys.argv[1] == 'backup':
            backup_database()
        elif sys.argv[1] == 'export':
            export_to_csv()
        else:
            print("Usage: python pac3200_logger.py [sql|backup|export]")
    else:
        main()