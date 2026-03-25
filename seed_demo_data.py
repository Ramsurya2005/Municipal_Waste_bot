import random
import time
from datetime import datetime, timedelta
from auth import auth
from mysql_database import MunicipalDatabase

def seed_data():
    print("Seeding demo data...")
    db = MunicipalDatabase()
    
    # 1. Create Demo Users via auth.py (which now also writes to MySQL)
    demo_users = [
        ("demo_user1", "demo1@example.com", "password123", "9876543210", "Rajesh Kumar"),
        ("demo_user2", "demo2@example.com", "password123", "9876543211", "Priya Sharma"),
        ("demo_user3", "demo3@example.com", "password123", "9876543212", "Anjali Gupta")
    ]
    
    citizen_ids = []
    for username, email, pwd, phone, name in demo_users:
        if not auth.get_user(username):
            res = auth.signup(username, email, pwd, phone, name)
            if res["success"]:
                citizen_ids.append(res["citizen_id"])
                print(f"Created user: {username} ({res['citizen_id']})")
            else:
                print(f"Failed to create {username}: {res['message']}")
        else:
            user = auth.get_user(username)
            citizen_ids.append(user["citizen_id"])
            print(f"User {username} already exists ({user['citizen_id']})")

    if not citizen_ids:
        print("No citizens available to seed complaints.")
        return

    # 2. Create Demo Complaints
    conn = db.get_connection()
    cursor = conn.cursor()
    
    demo_complaints = [
        {
            "dept": "roads",
            "desc": "Large pothole on the main crossroad causing traffic slowdowns.",
            "loc": "MG Road Intersection",
            "lat": 13.0827, "lon": 80.2707,
            "status": "Registered",
            "remarks": "Priority: HIGH | Reported by citizen"
        },
        {
            "dept": "sanitation",
            "desc": "Garbage not collected for 3 days near the park.",
            "loc": "Central Park East Gate",
            "lat": 13.0835, "lon": 80.2715,
            "status": "In Progress",
            "remarks": "Priority: MEDIUM | Assigned to sanitation team"
        },
        {
            "dept": "water",
            "desc": "Pipeline leakage wasting clean water on the street.",
            "loc": "Street 14, Anna Nagar",
            "lat": 13.0850, "lon": 80.2750,
            "status": "Resolved",
            "remarks": "Priority: URGENT | Fixed by Team B on 23rd"
        },
        {
            "dept": "electricity",
            "desc": "Street light has been dead for a week.",
            "loc": "T Nagar North",
            "lat": 13.0400, "lon": 80.2300,
            "status": "In Progress",
            "remarks": "Priority: LOW | Scheduled for repair"
        },
        {
            "dept": "traffic",
            "desc": "Traffic signal is malfunctioning, stuck on red.",
            "loc": "OMR Toll Plaza",
            "lat": 12.9600, "lon": 80.2400,
            "status": "Registered",
            "remarks": "Priority: HIGH | Alerted traffic police"
        }
    ]

    for c in demo_complaints:
        complaint_id = db.generate_id('CMP')
        cit_id = random.choice(citizen_ids)
        
        # Calculate a random date in the last 7 days
        days_ago = random.randint(0, 7)
        created_date = datetime.now() - timedelta(days=days_ago)
        
        try:
            cursor.execute("""
                INSERT INTO complaints 
                (complaint_id, citizen_id, department, description, location, status, remarks, latitude, longitude, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                complaint_id, cit_id, c["dept"], c["desc"], c["loc"], 
                c["status"], c["remarks"], c["lat"], c["lon"], created_date
            ))
            
            # also insert a fake satellite verification for some
            if random.choice([True, False]):
                cursor.execute("""
                    UPDATE complaints 
                    SET verification_status = 'verified_auto', 
                        verification_confidence = %s,
                        satellite_detection_result = 'Detected issues match description'
                    WHERE complaint_id = %s
                """, (random.uniform(0.70, 0.99), complaint_id))
                
        except Exception as e:
            print(f"Error inserting complaint: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Demo data seeded successfully! You can now log in with demo_user1 / password123.")

if __name__ == "__main__":
    seed_data()
