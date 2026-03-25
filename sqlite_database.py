"""
SQLite Database Module - No Installation Required!
Professional SQL database with zero setup
"""

import sqlite3
import json
from datetime import datetime
import random
import string
from pathlib import Path

class MunicipalDatabase:
    def __init__(self, db_path="municipal_services.db"):
        """Initialize SQLite database"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.create_tables()
        print(f"✅ Connected to SQLite database: {db_path}")
    
    def create_tables(self):
        """Create all necessary tables"""
        cursor = self.conn.cursor()
        
        # Citizens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citizens (
                citizen_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT UNIQUE,
                address TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Complaints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id TEXT PRIMARY KEY,
                citizen_id TEXT,
                department TEXT,
                description TEXT,
                location TEXT,
                status TEXT DEFAULT 'Registered',
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (citizen_id) REFERENCES citizens(citizen_id)
            )
        """)
        

        
        # Building Plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS building_plans (
                plan_id TEXT PRIMARY KEY,
                citizen_id TEXT,
                plot_number TEXT,
                plan_type TEXT,
                status TEXT DEFAULT 'Submitted',
                remarks TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (citizen_id) REFERENCES citizens(citizen_id)
            )
        """)
        
        # Water Connections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_connections (
                connection_id TEXT PRIMARY KEY,
                citizen_id TEXT,
                address TEXT,
                connection_type TEXT,
                status TEXT DEFAULT 'Applied',
                remarks TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (citizen_id) REFERENCES citizens(citizen_id)
            )
        """)
        
        self.conn.commit()
    
    def generate_id(self, prefix):
        """Generate unique ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{timestamp}{random_str}"
    
    # ==================== CITIZEN MANAGEMENT ====================
    
    def register_citizen(self, citizen_data):
        """Register a new citizen"""
        citizen_id = self.generate_id('CIT')
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO citizens (citizen_id, name, email, phone, address)
            VALUES (?, ?, ?, ?, ?)
        """, (citizen_id, citizen_data.get('name'), citizen_data.get('email'),
              citizen_data.get('phone'), citizen_data.get('address')))
        self.conn.commit()
        return citizen_id
    
    def get_citizen(self, citizen_id=None, phone=None, email=None):
        """Get citizen by ID, phone, or email"""
        cursor = self.conn.cursor()
        if citizen_id:
            cursor.execute("SELECT * FROM citizens WHERE citizen_id = ?", (citizen_id,))
        elif phone:
            cursor.execute("SELECT * FROM citizens WHERE phone = ?", (phone,))
        elif email:
            cursor.execute("SELECT * FROM citizens WHERE email = ?", (email,))
        else:
            return None
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_citizen(self, citizen_id, updates):
        """Update citizen information"""
        cursor = self.conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [citizen_id]
        cursor.execute(f"UPDATE citizens SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE citizen_id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ==================== COMPLAINTS ====================
    
    def save_complaint(self, complaint_data):
        """Save a new complaint"""
        complaint_id = self.generate_id('CMP')
        cursor = self.conn.cursor()
        urgency = complaint_data.get('urgency', 'medium')
        priority_note = complaint_data.get('priority_note', '')
        remarks = f"Priority: {urgency.upper()}"
        if priority_note:
            remarks = f"{remarks} | {priority_note}"
        cursor.execute("""
            INSERT INTO complaints (complaint_id, citizen_id, department, description, location, remarks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (complaint_id, complaint_data.get('citizen_id'), complaint_data.get('department'),
              complaint_data.get('description'), complaint_data.get('location'), remarks))
        self.conn.commit()
        return complaint_id
    
    def get_complaint(self, complaint_id):
        """Get complaint by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_complaints_by_citizen(self, citizen_id):
        """Get all complaints by a citizen"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM complaints WHERE citizen_id = ? ORDER BY created_at DESC", (citizen_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_complaint_status(self, complaint_id, status, remarks=None):
        """Update complaint status"""
        cursor = self.conn.cursor()
        if remarks:
            cursor.execute("""
                UPDATE complaints SET status = ?, remarks = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE complaint_id = ?
            """, (status, remarks, complaint_id))
        else:
            cursor.execute("""
                UPDATE complaints SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE complaint_id = ?
            """, (status, complaint_id))
        self.conn.commit()
        return cursor.rowcount > 0
    

    # ==================== ANALYTICS ====================
    
    def get_dashboard_stats(self, citizen_id=None):
        """Get statistics for dashboard"""
        cursor = self.conn.cursor()
        if citizen_id:
            stats = {}
            cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE citizen_id = ?", (citizen_id,))
            stats['total_complaints'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE citizen_id = ? AND status IN ('Registered', 'In Progress')", (citizen_id,))
            stats['pending_complaints'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE citizen_id = ? AND status = 'Resolved'", (citizen_id,))
            stats['resolved_complaints'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM building_plans WHERE citizen_id = ?", (citizen_id,))
            stats['total_building_plans'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM water_connections WHERE citizen_id = ?", (citizen_id,))
            stats['total_water_connections'] = cursor.fetchone()['count']
            stats['pending_applications'] = 0  # For sidebar compatibility
            return stats
        else:
            stats = {}
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
            return stats
    
    def get_complaints_by_department(self):
        """Get complaint count by department"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT department as _id, COUNT(*) as count 
            FROM complaints 
            GROUP BY department 
            ORDER BY count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self):
        """Get overall statistics for dashboard"""
        cursor = self.conn.cursor()
        stats = {}
        
        # Total complaints
        cursor.execute("SELECT COUNT(*) as count FROM complaints")
        stats['total'] = cursor.fetchone()['count']
        
        # Pending complaints
        cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE status IN ('Registered', 'In Progress')")
        stats['pending'] = cursor.fetchone()['count']
        
        # Resolved complaints
        cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE status = 'Resolved'")
        stats['resolved'] = cursor.fetchone()['count']
        
        # By category
        stats['by_category'] = self.get_complaints_by_department()
        
        return stats
    
    def get_recent_activity(self, citizen_id, limit=10):
        """Get recent activity for a citizen"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 'Complaint' as type, complaint_id as id, description, status, created_at as date
            FROM complaints WHERE citizen_id = ?
            UNION ALL
            SELECT 'Building Plan' as type, plan_id as id, plan_type as description, status, submitted_at as date
            FROM building_plans WHERE citizen_id = ?
            UNION ALL
            SELECT 'Water Connection' as type, connection_id as id, address as description, status, applied_at as date
            FROM water_connections WHERE citizen_id = ?
            ORDER BY date DESC LIMIT ?
        """, (citizen_id, citizen_id, citizen_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def close_connection(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    

