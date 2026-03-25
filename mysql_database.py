"""
MySQL Database Module
Professional MySQL database with connection pooling
"""

import mysql.connector
from mysql.connector import Error, pooling
import json
from datetime import datetime
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()

class MunicipalDatabase:
    DEPARTMENT_TABLES = {
        "traffic management cell": "dept_traffic_complaints",
        "public works department": "dept_public_works_complaints",
        "public works": "dept_public_works_complaints",
        "roads": "dept_public_works_complaints",
        "water supply board": "dept_water_supply_complaints",
        "water supply": "dept_water_supply_complaints",
        "sanitation department": "dept_sanitation_complaints",
        "sanitation": "dept_sanitation_complaints",
        "electrical department": "dept_electrical_complaints",
        "electrical": "dept_electrical_complaints",
        "drainage department": "dept_drainage_complaints",
        "drainage": "dept_drainage_complaints",
        "parks and recreation": "dept_parks_complaints",
        "parks": "dept_parks_complaints",
        "public health department": "dept_health_complaints",
        "health": "dept_health_complaints",
        "building and planning department": "dept_building_complaints",
        "building": "dept_building_complaints",
        "general administration": "dept_general_complaints",
        "general": "dept_general_complaints"
    }

    def __init__(self):
        """Initialize MySQL database with connection pool"""
        self.config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'municipal_chatbot')
        }
        
        # Create connection pool
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="municipal_pool",
                pool_size=5,
                **self.config
            )
            print(f"✅ Connected to MySQL database: {self.config['database']}")
            self.create_tables()
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            print(f"💡 Make sure MySQL is running and credentials in .env are correct")
            raise
    
    def get_connection(self):
        """Get connection from pool"""
        return self.pool.get_connection()
    
    def create_tables(self):
        """Create all necessary tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Citizens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS citizens (
                    citizen_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    phone VARCHAR(20) UNIQUE,
                    address TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Complaints table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    complaint_id VARCHAR(50) PRIMARY KEY,
                    citizen_id VARCHAR(50),
                    department VARCHAR(255),
                    description TEXT,
                    location TEXT,
                    status VARCHAR(50) DEFAULT 'Registered',
                    remarks TEXT,
                    latitude DECIMAL(10, 8),
                    longitude DECIMAL(11, 8),
                    satellite_image_path TEXT,
                    user_image_path TEXT,
                    satellite_detection_result TEXT,
                    user_detection_result TEXT,
                    verification_status VARCHAR(100),
                    verification_confidence DECIMAL(5, 4),
                    verification_result_json TEXT,
                    last_checked_date TIMESTAMP NULL,
                    last_verified_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (citizen_id) REFERENCES citizens(citizen_id)
                )
            """)
            
            # Building Plans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS building_plans (
                    plan_id VARCHAR(50) PRIMARY KEY,
                    citizen_id VARCHAR(50),
                    plot_number VARCHAR(100),
                    plan_type VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'Submitted',
                    remarks TEXT,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (citizen_id) REFERENCES citizens(citizen_id)
                )
            """)
            
            # Water Connections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS water_connections (
                    connection_id VARCHAR(50) PRIMARY KEY,
                    citizen_id VARCHAR(50),
                    address TEXT,
                    connection_type VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'Applied',
                    remarks TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (citizen_id) REFERENCES citizens(citizen_id)
                )
            """)
            
            # Satellite Images table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_images (
                    image_id VARCHAR(50) PRIMARY KEY,
                    complaint_id VARCHAR(50) NOT NULL,
                    latitude DECIMAL(10, 8) NOT NULL,
                    longitude DECIMAL(11, 8) NOT NULL,
                    image_path TEXT NOT NULL,
                    image_timestamp TIMESTAMP NULL,
                    download_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    image_size_bytes INT,
                    source VARCHAR(100) DEFAULT 'google_maps_api',
                    image_metadata TEXT,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
                )
            """)
            
            # Satellite Detections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_detections (
                    detection_id VARCHAR(50) PRIMARY KEY,
                    complaint_id VARCHAR(50) NOT NULL,
                    image_id VARCHAR(50),
                    detection_type VARCHAR(50) DEFAULT 'satellite',
                    garbage_probability DECIMAL(5, 4),
                    road_damage_probability DECIMAL(5, 4),
                    water_pooling_probability DECIMAL(5, 4),
                    vegetation_damage_probability DECIMAL(5, 4),
                    overall_confidence DECIMAL(5, 4),
                    detected_issues TEXT,
                    detection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    model_version VARCHAR(50),
                    detection_metadata TEXT,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
                    FOREIGN KEY (image_id) REFERENCES satellite_images(image_id)
                )
            """)
            
            # Process Logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_logs (
                    process_id VARCHAR(50) PRIMARY KEY,
                    complaint_id VARCHAR(50) NOT NULL,
                    process_type VARCHAR(100),
                    steps TEXT,
                    status VARCHAR(50),
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP NULL,
                    error_message TEXT,
                    process_data TEXT,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
                )
            """)

            self._create_department_tables(cursor)
            self._backfill_department_tables(cursor)
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Error as e:
            print(f"Error creating tables: {e}")

    def _normalize_department(self, department):
        """Normalize department text for stable table mapping"""
        return " ".join(str(department or "general administration").strip().lower().split())

    def _department_table_name(self, department):
        """Resolve department-specific table name"""
        normalized = self._normalize_department(department)
        if normalized in self.DEPARTMENT_TABLES:
            return self.DEPARTMENT_TABLES[normalized]

        if "traffic" in normalized:
            return "dept_traffic_complaints"
        if "road" in normalized or "public work" in normalized:
            return "dept_public_works_complaints"
        if "water" in normalized:
            return "dept_water_supply_complaints"
        if "sanitation" in normalized or "garbage" in normalized:
            return "dept_sanitation_complaints"
        if "electric" in normalized or "streetlight" in normalized:
            return "dept_electrical_complaints"
        if "drain" in normalized or "sewer" in normalized:
            return "dept_drainage_complaints"
        if "park" in normalized:
            return "dept_parks_complaints"
        if "health" in normalized:
            return "dept_health_complaints"
        if "building" in normalized or "planning" in normalized:
            return "dept_building_complaints"

        return "dept_general_complaints"

    def _create_department_tables(self, cursor):
        """Create one complaints table per department"""
        for table_name in sorted(set(self.DEPARTMENT_TABLES.values())):
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    complaint_id VARCHAR(50) NOT NULL UNIQUE,
                    citizen_id VARCHAR(50),
                    department VARCHAR(255),
                    description TEXT,
                    location TEXT,
                    status VARCHAR(50) DEFAULT 'Registered',
                    remarks TEXT,
                    latitude DECIMAL(10, 8),
                    longitude DECIMAL(11, 8),
                    created_at TIMESTAMP NULL,
                    updated_at TIMESTAMP NULL,
                    routed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE
                )
            """)

    def _sync_complaint_to_department_table(self, cursor, complaint_id, complaint_data, remarks):
        """Insert/update complaint record into resolved department table"""
        department = complaint_data.get('department') or 'General Administration'
        table_name = self._department_table_name(department)
        location = complaint_data.get('location')
        description = complaint_data.get('description')
        citizen_id = complaint_data.get('citizen_id')

        cursor.execute(f"""
            INSERT INTO {table_name}
                (complaint_id, citizen_id, department, description, location, status, remarks, latitude, longitude, created_at, updated_at)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, NULL, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                citizen_id = VALUES(citizen_id),
                department = VALUES(department),
                description = VALUES(description),
                location = VALUES(location),
                status = VALUES(status),
                remarks = VALUES(remarks),
                updated_at = CURRENT_TIMESTAMP
        """, (
            complaint_id,
            citizen_id,
            department,
            description,
            location,
            'Registered',
            remarks
        ))

    def _backfill_department_tables(self, cursor):
        """Backfill old complaints into department tables without duplicates"""
        cursor.execute("""
            SELECT complaint_id, citizen_id, department, description, location, status, remarks,
                   latitude, longitude, created_at, updated_at
            FROM complaints
        """)
        rows = cursor.fetchall()

        for row in rows:
            complaint_id, citizen_id, department, description, location, status, remarks, latitude, longitude, created_at, updated_at = row
            table_name = self._department_table_name(department)
            cursor.execute(f"""
                INSERT INTO {table_name}
                    (complaint_id, citizen_id, department, description, location, status, remarks, latitude, longitude, created_at, updated_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    citizen_id = VALUES(citizen_id),
                    department = VALUES(department),
                    description = VALUES(description),
                    location = VALUES(location),
                    status = VALUES(status),
                    remarks = VALUES(remarks),
                    latitude = VALUES(latitude),
                    longitude = VALUES(longitude),
                    updated_at = VALUES(updated_at)
            """, (
                complaint_id,
                citizen_id,
                department,
                description,
                location,
                status,
                remarks,
                latitude,
                longitude,
                created_at,
                updated_at
            ))
    
    def generate_id(self, prefix):
        """Generate unique ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{timestamp}{random_str}"
    
    # ==================== CITIZEN MANAGEMENT ====================
    
    def register_citizen(self, citizen_data):
        """Register a new citizen"""
        citizen_id = self.generate_id('CIT')
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO citizens (citizen_id, name, email, phone, address)
                VALUES (%s, %s, %s, %s, %s)
            """, (citizen_id, citizen_data.get('name'), citizen_data.get('email'),
                  citizen_data.get('phone'), citizen_data.get('address')))
            conn.commit()
            cursor.close()
            conn.close()
            return citizen_id
        except Error as e:
            print(f"Error registering citizen: {e}")
            return None
    
    def get_citizen(self, citizen_id=None, phone=None, email=None):
        """Get citizen by ID, phone, or email"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            if citizen_id:
                cursor.execute("SELECT * FROM citizens WHERE citizen_id = %s", (citizen_id,))
            elif phone:
                cursor.execute("SELECT * FROM citizens WHERE phone = %s", (phone,))
            elif email:
                cursor.execute("SELECT * FROM citizens WHERE email = %s", (email,))
            else:
                return None
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result
        except Error as e:
            print(f"Error getting citizen: {e}")
            return None
    
    def update_citizen(self, citizen_id, updates):
        """Update citizen information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [citizen_id]
            cursor.execute(
                f"UPDATE citizens SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE citizen_id = %s",
                values
            )
            conn.commit()
            affected = cursor.rowcount > 0
            cursor.close()
            conn.close()
            return affected
        except Error as e:
            print(f"Error updating citizen: {e}")
            return False
    
    # ==================== COMPLAINTS ====================
    
    def save_complaint(self, complaint_data):
        """Save a new complaint"""
        complaint_id = self.generate_id('CMP')
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            urgency = complaint_data.get('urgency', 'medium')
            priority_note = complaint_data.get('priority_note', '')
            remarks = f"Priority: {urgency.upper()}"
            if priority_note:
                remarks = f"{remarks} | {priority_note}"
            
            cursor.execute("""
                INSERT INTO complaints (complaint_id, citizen_id, department, description, location, remarks)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (complaint_id, complaint_data.get('citizen_id'), complaint_data.get('department'),
                  complaint_data.get('description'), complaint_data.get('location'), remarks))

            self._sync_complaint_to_department_table(cursor, complaint_id, complaint_data, remarks)
            conn.commit()
            cursor.close()
            conn.close()
            return complaint_id
        except Error as e:
            print(f"Error saving complaint: {e}")
            return None
    
    def get_complaint(self, complaint_id):
        """Get complaint by ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM complaints WHERE complaint_id = %s", (complaint_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result
        except Error as e:
            print(f"Error getting complaint: {e}")
            return None
    
    def get_complaints_by_citizen(self, citizen_id):
        """Get all complaints by a citizen"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM complaints WHERE citizen_id = %s ORDER BY created_at DESC",
                (citizen_id,)
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Error as e:
            print(f"Error getting complaints: {e}")
            return []
    
    def update_complaint_status(self, complaint_id, status, remarks=None):
        """Update complaint status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if remarks:
                cursor.execute("""
                    UPDATE complaints SET status = %s, remarks = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE complaint_id = %s
                """, (status, remarks, complaint_id))
            else:
                cursor.execute("""
                    UPDATE complaints SET status = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE complaint_id = %s
                """, (status, complaint_id))
            conn.commit()
            affected = cursor.rowcount > 0
            cursor.close()
            conn.close()
            return affected
        except Error as e:
            print(f"Error updating complaint status: {e}")
            return False
    
    # ==================== ANALYTICS ====================
    
    def get_dashboard_stats(self, citizen_id=None):
        """Get statistics for dashboard"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            stats = {}
            
            if citizen_id:
                cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE citizen_id = %s", (citizen_id,))
                stats['total_complaints'] = cursor.fetchone()['count']
                
                cursor.execute(
                    "SELECT COUNT(*) as count FROM complaints WHERE citizen_id = %s AND status IN ('Registered', 'In Progress')",
                    (citizen_id,)
                )
                stats['pending_complaints'] = cursor.fetchone()['count']
                
                cursor.execute(
                    "SELECT COUNT(*) as count FROM complaints WHERE citizen_id = %s AND status = 'Resolved'",
                    (citizen_id,)
                )
                stats['resolved_complaints'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM building_plans WHERE citizen_id = %s", (citizen_id,))
                stats['total_building_plans'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM water_connections WHERE citizen_id = %s", (citizen_id,))
                stats['total_water_connections'] = cursor.fetchone()['count']
                
                stats['pending_applications'] = 0
            else:
                cursor.execute("SELECT COUNT(*) as count FROM citizens")
                stats['total_citizens'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM complaints")
                stats['total_complaints'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE status IN ('Registered', 'In Progress')")
                stats['pending_complaints'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE status = 'Resolved'")
                stats['resolved_complaints'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM building_plans")
                stats['total_building_plans'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM water_connections")
                stats['total_water_connections'] = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            return stats
        except Error as e:
            print(f"Error getting dashboard stats: {e}")
            return {}
    
    def get_complaints_by_department(self):
        """Get complaint count by department"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT department as _id, COUNT(*) as count 
                FROM complaints 
                GROUP BY department 
                ORDER BY count DESC
            """)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Error as e:
            print(f"Error getting complaints by department: {e}")
            return []
    
    def get_statistics(self):
        """Get overall statistics for dashboard"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            stats = {}
            
            cursor.execute("SELECT COUNT(*) as count FROM complaints")
            stats['total'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE status IN ('Registered', 'In Progress')")
            stats['pending'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE status = 'Resolved'")
            stats['resolved'] = cursor.fetchone()['count']
            
            stats['by_category'] = self.get_complaints_by_department()
            
            cursor.close()
            conn.close()
            return stats
        except Error as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def get_recent_activity(self, citizen_id, limit=10):
        """Get recent activity for a citizen"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # MySQL doesn't support UNION ALL in the same way, so we'll do separate queries
            activities = []
            
            cursor.execute("""
                SELECT 'Complaint' as type, complaint_id as id, description, status, created_at as date
                FROM complaints WHERE citizen_id = %s
                ORDER BY date DESC LIMIT %s
            """, (citizen_id, limit))
            activities.extend(cursor.fetchall())
            
            cursor.execute("""
                SELECT 'Building Plan' as type, plan_id as id, plan_type as description, status, submitted_at as date
                FROM building_plans WHERE citizen_id = %s
                ORDER BY date DESC LIMIT %s
            """, (citizen_id, limit))
            activities.extend(cursor.fetchall())
            
            cursor.execute("""
                SELECT 'Water Connection' as type, connection_id as id, address as description, status, applied_at as date
                FROM water_connections WHERE citizen_id = %s
                ORDER BY date DESC LIMIT %s
            """, (citizen_id, limit))
            activities.extend(cursor.fetchall())
            
            # Sort all activities by date
            activities.sort(key=lambda x: x['date'], reverse=True)
            
            cursor.close()
            conn.close()
            return activities[:limit]
        except Error as e:
            print(f"Error getting recent activity: {e}")
            return []
    
    def close_connection(self):
        """Close database connection pool"""
        # Connection pool handles connections automatically
        pass
