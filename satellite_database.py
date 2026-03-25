"""
Satellite Database Schema Enhancement
Adds satellite-specific tables and columns to existing database
Maintains backward compatibility with existing schema
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class SatelliteDatabaseSetup:
    """
    Sets up satellite-related tables and schema enhancements
    Can be run on existing database without losing data
    """
    
    def __init__(self, db_path="municipal_services.db"):
        """Initialize setup"""
        self.db_path = db_path
    
    def setup(self):
        """Run all schema enhancements"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Add satellite columns to complaints table
            self._add_satellite_columns(cursor, conn)
            
            # 2. Create satellite_images table
            self._create_satellite_images_table(cursor, conn)
            
            # 3. Create satellite_detections table
            self._create_satellite_detections_table(cursor, conn)
            
            # 4. Create satellite_alerts table
            self._create_satellite_alerts_table(cursor, conn)
            
            # 5. Create verification_results table
            self._create_verification_results_table(cursor, conn)
            
            # 6. Create process_logs table
            self._create_process_logs_table(cursor, conn)
            
            conn.close()
            
            print("✅ Database schema enhanced successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            return False
    
    def _add_satellite_columns(self, cursor, conn):
        """Add satellite columns to existing complaints table"""
        try:
            # Get existing columns
            cursor.execute("PRAGMA table_info(complaints)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # List of satellite columns to add
            columns_to_add = [
                ('latitude', 'REAL'),
                ('longitude', 'REAL'),
                ('satellite_image_path', 'TEXT'),
                ('user_image_path', 'TEXT'),
                ('satellite_detection_result', 'TEXT'),  # JSON
                ('user_detection_result', 'TEXT'),  # JSON
                ('verification_status', 'TEXT'),  # verified, partial_match, needs_manual_review, verified_by_proximity, verified_uncertain, verified_auto
                ('verification_confidence', 'REAL'),  # 0-1 score
                ('verification_result_json', 'TEXT'),  # Full verification JSON
                ('last_checked_date', 'TIMESTAMP'),
                ('last_verified_at', 'TIMESTAMP')
            ]
            
            # Add only missing columns
            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    alter_sql = f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"
                    cursor.execute(alter_sql)
                    print(f"✓ Added column: {col_name}")
            
            conn.commit()
            
        except Exception as e:
            print(f"⚠️ Error adding satellite columns: {e}")
    
    def _create_satellite_images_table(self, cursor, conn):
        """Create table for satellite image metadata"""
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_images (
                    image_id TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    image_path TEXT NOT NULL,
                    image_timestamp TIMESTAMP,
                    download_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    image_size_bytes INTEGER,
                    source TEXT DEFAULT 'google_maps_api',
                    image_metadata TEXT,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
                )
            """)
            conn.commit()
            print("✓ Created satellite_images table")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"⚠️ Error creating satellite_images table: {e}")
    
    def _create_satellite_detections_table(self, cursor, conn):
        """Create table for AI detection results"""
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_detections (
                    detection_id TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    image_id TEXT,
                    detection_type TEXT DEFAULT 'satellite',
                    garbage_probability REAL,
                    road_damage_probability REAL,
                    water_pooling_probability REAL,
                    vegetation_damage_probability REAL,
                    overall_confidence REAL,
                    detected_issues TEXT,
                    detection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    model_version TEXT,
                    detection_metadata TEXT,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
                    FOREIGN KEY (image_id) REFERENCES satellite_images(image_id)
                )
            """)
            conn.commit()
            print("✓ Created satellite_detections table")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"⚠️ Error creating satellite_detections table: {e}")
    
    def _create_satellite_alerts_table(self, cursor, conn):
        """Create table for monitoring alerts"""
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_alerts (
                    alert_id TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    alert_type TEXT,
                    severity TEXT,
                    change_percentage REAL,
                    alert_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    action_taken TEXT,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
                )
            """)
            conn.commit()
            print("✓ Created satellite_alerts table")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"⚠️ Error creating satellite_alerts table: {e}")
    
    def _create_verification_results_table(self, cursor, conn):
        """Create table for verification results"""
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verification_results (
                    verification_id TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    satellite_detection_id TEXT,
                    user_detection_id TEXT,
                    matched_issues TEXT,
                    unmatched_issues TEXT,
                    nearby_complaints TEXT,
                    verification_status TEXT,
                    confidence_score REAL,
                    final_status TEXT,
                    recommendation TEXT,
                    tracking_history TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
                )
            """)
            conn.commit()
            print("✓ Created verification_results table")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"⚠️ Error creating verification_results table: {e}")
    
    def _create_process_logs_table(self, cursor, conn):
        """Create table for process tracking"""
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_logs (
                    process_id TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    process_type TEXT,
                    steps TEXT,
                    status TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    error_message TEXT,
                    process_data TEXT,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
                )
            """)
            conn.commit()
            print("✓ Created process_logs table")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"⚠️ Error creating process_logs table: {e}")
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            indexes = [
                ("CREATE INDEX IF NOT EXISTS idx_complaints_location ON complaints(latitude, longitude)",
                 "complaints location index"),
                ("CREATE INDEX IF NOT EXISTS idx_complaints_verification_status ON complaints(verification_status)",
                 "complaints verification status index"),
                ("CREATE INDEX IF NOT EXISTS idx_satellite_images_complaint ON satellite_images(complaint_id)",
                 "satellite_images complaint index"),
                ("CREATE INDEX IF NOT EXISTS idx_satellite_detections_complaint ON satellite_detections(complaint_id)",
                 "satellite_detections complaint index"),
                ("CREATE INDEX IF NOT EXISTS idx_satellite_alerts_status ON satellite_alerts(status, severity)",
                 "satellite_alerts status index"),
                ("CREATE INDEX IF NOT EXISTS idx_process_logs_complaint ON process_logs(complaint_id)",
                 "process_logs complaint index"),
            ]
            
            for index_sql, desc in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            conn.close()
            
            print("✅ Database indexes created")
            return True
            
        except Exception as e:
            print(f"⚠️ Error creating indexes: {e}")
            return False

# ==================== Helper Functions ====================

def initialize_satellite_database(db_path="municipal_services.db"):
    """
    One-time initialization of satellite features
    Call once when setting up the system
    """
    setup = SatelliteDatabaseSetup(db_path)
    if setup.setup():
        setup.create_indexes()
        return True
    return False

def check_database_version(db_path="municipal_services.db"):
    """Check if database has satellite schema"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if satellite tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='satellite_images'
        """)
        
        has_satellite_schema = cursor.fetchone() is not None
        conn.close()
        
        return {
            'has_satellite_schema': has_satellite_schema,
            'db_path': db_path
        }
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    # Auto-run setup when module is executed
    print("🛰️ Satellite Database Setup Utility")
    print("="*60)
    
    status = initialize_satellite_database()
    
    if status:
        print("✨ Satellite system is ready!")
    else:
        print("❌ Setup failed. Please check errors above.")
