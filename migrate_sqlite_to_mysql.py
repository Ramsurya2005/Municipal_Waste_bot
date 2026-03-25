"""
SQLite to MySQL Migration Script
Transfers all data from municipal_services.db (SQLite) to MySQL database
"""

import sqlite3
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class DatabaseMigration:
    def __init__(self):
        """Initialize both database connections"""
        # SQLite connection
        self.sqlite_db = "municipal_services.db"
        
        # MySQL connection config
        self.mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'municipal_chatbot')
        }
        
        self.stats = {
            'citizens': 0,
            'complaints': 0,
            'building_plans': 0,
            'water_connections': 0,
            'satellite_images': 0,
            'satellite_detections': 0,
            'process_logs': 0
        }
    
    def check_sqlite_exists(self):
        """Check if SQLite database exists"""
        if not os.path.exists(self.sqlite_db):
            print(f"❌ SQLite database not found: {self.sqlite_db}")
            return False
        print(f"✅ SQLite database found: {self.sqlite_db}")
        return True
    
    def test_mysql_connection(self):
        """Test MySQL connection"""
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            if conn.is_connected():
                print(f"✅ MySQL connection successful")
                conn.close()
                return True
        except Error as e:
            print(f"❌ MySQL connection failed: {e}")
            print("\n💡 Make sure:")
            print("   1. MySQL service is running (Start-Service MySQL84)")
            print("   2. Password in .env is correct")
            print("   3. Database 'municipal_chatbot' exists")
            return False
    
    def get_sqlite_table_data(self, table_name):
        """Get all data from SQLite table"""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            data = [dict(row) for row in rows]
            
            conn.close()
            return data
        except sqlite3.Error as e:
            print(f"⚠️  Error reading {table_name}: {e}")
            return []

    def _normalize_citizen_id(self, citizen_id):
        """Normalize citizen ID values from legacy data"""
        if citizen_id is None:
            return None

        normalized = str(citizen_id).strip()
        return normalized if normalized else None

    def _fetch_mysql_citizen_ids(self, cursor):
        """Fetch existing citizen IDs from MySQL for FK-safe inserts"""
        cursor.execute("SELECT citizen_id FROM citizens")
        return {row[0] for row in cursor.fetchall()}

    def _ensure_placeholder_citizen(self, cursor, citizen_id):
        """Create placeholder citizen when dependent legacy records reference unknown IDs"""
        display_suffix = citizen_id[-4:] if len(citizen_id) >= 4 else citizen_id
        cursor.execute("""
            INSERT INTO citizens (citizen_id, name, email, phone, address)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE citizen_id = VALUES(citizen_id)
        """, (
            citizen_id,
            f"Migrated Citizen {display_suffix}",
            None,
            None,
            "Address unavailable (legacy import)"
        ))
    
    def migrate_citizens(self):
        """Migrate citizens table"""
        print("\n📋 Migrating citizens...")
        data = self.get_sqlite_table_data('citizens')
        
        if not data:
            print("   No citizens to migrate")
            return
        
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            
            for row in data:
                cursor.execute("""
                    INSERT INTO citizens (citizen_id, name, email, phone, address, registered_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        email = VALUES(email),
                        phone = VALUES(phone),
                        address = VALUES(address),
                        updated_at = VALUES(updated_at)
                """, (
                    row['citizen_id'],
                    row['name'],
                    row['email'],
                    row['phone'],
                    row['address'],
                    row['registered_at'],
                    row['updated_at']
                ))
            
            conn.commit()
            self.stats['citizens'] = len(data)
            print(f"   ✅ Migrated {len(data)} citizens")
            
            cursor.close()
            conn.close()
        except Error as e:
            print(f"   ❌ Error: {e}")
    
    def migrate_complaints(self):
        """Migrate complaints table"""
        print("\n📝 Migrating complaints...")
        data = self.get_sqlite_table_data('complaints')
        
        if not data:
            print("   No complaints to migrate")
            return
        
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            valid_citizen_ids = self._fetch_mysql_citizen_ids(cursor)
            
            for row in data:
                complaint_citizen_id = self._normalize_citizen_id(row.get('citizen_id'))
                if complaint_citizen_id and complaint_citizen_id not in valid_citizen_ids:
                    self._ensure_placeholder_citizen(cursor, complaint_citizen_id)
                    valid_citizen_ids.add(complaint_citizen_id)

                cursor.execute("""
                    INSERT INTO complaints (
                        complaint_id, citizen_id, department, description, location,
                        status, remarks, latitude, longitude,
                        satellite_image_path, user_image_path,
                        satellite_detection_result, user_detection_result,
                        verification_status, verification_confidence, verification_result_json,
                        last_checked_date, last_verified_at,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        remarks = VALUES(remarks),
                        updated_at = VALUES(updated_at)
                """, (
                    row['complaint_id'],
                    complaint_citizen_id,
                    row.get('department'),
                    row.get('description'),
                    row.get('location'),
                    row.get('status', 'Registered'),
                    row.get('remarks'),
                    row.get('latitude'),
                    row.get('longitude'),
                    row.get('satellite_image_path'),
                    row.get('user_image_path'),
                    row.get('satellite_detection_result'),
                    row.get('user_detection_result'),
                    row.get('verification_status'),
                    row.get('verification_confidence'),
                    row.get('verification_result_json'),
                    row.get('last_checked_date'),
                    row.get('last_verified_at'),
                    row.get('created_at'),
                    row.get('updated_at')
                ))
            
            conn.commit()
            self.stats['complaints'] = len(data)
            print(f"   ✅ Migrated {len(data)} complaints")
            
            cursor.close()
            conn.close()
        except Error as e:
            print(f"   ❌ Error: {e}")
    
    def migrate_building_plans(self):
        """Migrate building_plans table"""
        print("\n🏗️  Migrating building plans...")
        data = self.get_sqlite_table_data('building_plans')
        
        if not data:
            print("   No building plans to migrate")
            return
        
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            valid_citizen_ids = self._fetch_mysql_citizen_ids(cursor)
            
            for row in data:
                plan_citizen_id = self._normalize_citizen_id(row.get('citizen_id'))
                if plan_citizen_id and plan_citizen_id not in valid_citizen_ids:
                    self._ensure_placeholder_citizen(cursor, plan_citizen_id)
                    valid_citizen_ids.add(plan_citizen_id)

                cursor.execute("""
                    INSERT INTO building_plans (
                        plan_id, citizen_id, plot_number, plan_type,
                        status, remarks, submitted_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        remarks = VALUES(remarks),
                        updated_at = VALUES(updated_at)
                """, (
                    row['plan_id'],
                    plan_citizen_id,
                    row.get('plot_number'),
                    row.get('plan_type'),
                    row.get('status', 'Submitted'),
                    row.get('remarks'),
                    row.get('submitted_at'),
                    row.get('updated_at')
                ))
            
            conn.commit()
            self.stats['building_plans'] = len(data)
            print(f"   ✅ Migrated {len(data)} building plans")
            
            cursor.close()
            conn.close()
        except Error as e:
            print(f"   ❌ Error: {e}")
    
    def migrate_water_connections(self):
        """Migrate water_connections table"""
        print("\n💧 Migrating water connections...")
        data = self.get_sqlite_table_data('water_connections')
        
        if not data:
            print("   No water connections to migrate")
            return
        
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            valid_citizen_ids = self._fetch_mysql_citizen_ids(cursor)
            
            for row in data:
                water_citizen_id = self._normalize_citizen_id(row.get('citizen_id'))
                if water_citizen_id and water_citizen_id not in valid_citizen_ids:
                    self._ensure_placeholder_citizen(cursor, water_citizen_id)
                    valid_citizen_ids.add(water_citizen_id)

                cursor.execute("""
                    INSERT INTO water_connections (
                        connection_id, citizen_id, address, connection_type,
                        status, remarks, applied_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        remarks = VALUES(remarks),
                        updated_at = VALUES(updated_at)
                """, (
                    row['connection_id'],
                    water_citizen_id,
                    row.get('address'),
                    row.get('connection_type'),
                    row.get('status', 'Applied'),
                    row.get('remarks'),
                    row.get('applied_at'),
                    row.get('updated_at')
                ))
            
            conn.commit()
            self.stats['water_connections'] = len(data)
            print(f"   ✅ Migrated {len(data)} water connections")
            
            cursor.close()
            conn.close()
        except Error as e:
            print(f"   ❌ Error: {e}")
    
    def migrate_satellite_tables(self):
        """Migrate satellite-related tables if they exist"""
        # Check if tables exist in SQLite
        try:
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()
            
            # Check for satellite_images table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='satellite_images'")
            if cursor.fetchone():
                print("\n🛰️  Migrating satellite images...")
                data = self.get_sqlite_table_data('satellite_images')
                if data:
                    mysql_conn = mysql.connector.connect(**self.mysql_config)
                    mysql_cursor = mysql_conn.cursor()
                    
                    for row in data:
                        mysql_cursor.execute("""
                            INSERT INTO satellite_images (
                                image_id, complaint_id, latitude, longitude, image_path,
                                image_timestamp, download_timestamp, image_size_bytes,
                                source, image_metadata
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE image_path = VALUES(image_path)
                        """, (
                            row['image_id'], row['complaint_id'], row['latitude'], row['longitude'],
                            row['image_path'], row.get('image_timestamp'), row.get('download_timestamp'),
                            row.get('image_size_bytes'), row.get('source'), row.get('image_metadata')
                        ))
                    
                    mysql_conn.commit()
                    self.stats['satellite_images'] = len(data)
                    print(f"   ✅ Migrated {len(data)} satellite images")
                    mysql_cursor.close()
                    mysql_conn.close()
            
            # Check for satellite_detections table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='satellite_detections'")
            if cursor.fetchone():
                print("\n🔍 Migrating satellite detections...")
                data = self.get_sqlite_table_data('satellite_detections')
                if data:
                    mysql_conn = mysql.connector.connect(**self.mysql_config)
                    mysql_cursor = mysql_conn.cursor()
                    
                    for row in data:
                        mysql_cursor.execute("""
                            INSERT INTO satellite_detections (
                                detection_id, complaint_id, image_id, detection_type,
                                garbage_probability, road_damage_probability,
                                water_pooling_probability, vegetation_damage_probability,
                                overall_confidence, detected_issues, detection_timestamp,
                                model_version, detection_metadata
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE overall_confidence = VALUES(overall_confidence)
                        """, (
                            row['detection_id'], row['complaint_id'], row.get('image_id'),
                            row.get('detection_type'), row.get('garbage_probability'),
                            row.get('road_damage_probability'), row.get('water_pooling_probability'),
                            row.get('vegetation_damage_probability'), row.get('overall_confidence'),
                            row.get('detected_issues'), row.get('detection_timestamp'),
                            row.get('model_version'), row.get('detection_metadata')
                        ))
                    
                    mysql_conn.commit()
                    self.stats['satellite_detections'] = len(data)
                    print(f"   ✅ Migrated {len(data)} satellite detections")
                    mysql_cursor.close()
                    mysql_conn.close()
            
            conn.close()
        except Exception as e:
            print(f"   ℹ️  Satellite tables not found or error: {e}")
    
    def run_migration(self):
        """Run complete migration"""
        print("=" * 70)
        print("🔄 SQLite to MySQL Migration")
        print("=" * 70)
        
        # Check prerequisites
        if not self.check_sqlite_exists():
            return False
        
        if not self.test_mysql_connection():
            return False
        
        print("\n🚀 Starting migration...\n")
        
        # Migrate all tables
        self.migrate_citizens()
        self.migrate_complaints()
        self.migrate_building_plans()
        self.migrate_water_connections()
        self.migrate_satellite_tables()
        
        # Summary
        print("\n" + "=" * 70)
        print("✨ Migration Summary")
        print("=" * 70)
        total = 0
        for table, count in self.stats.items():
            if count > 0:
                print(f"   {table.ljust(25)}: {count} records")
                total += count
        print("-" * 70)
        print(f"   {'TOTAL'.ljust(25)}: {total} records")
        print("=" * 70)
        
        if total > 0:
            print("\n✅ Migration completed successfully!")
            print("💡 You can now use MySQL database in your application")
            return True
        else:
            print("\n⚠️  No data found to migrate")
            print("💡 You can still use MySQL for new data")
            return True

if __name__ == "__main__":
    migrator = DatabaseMigration()
    migrator.run_migration()
