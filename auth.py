"""
User Authentication Module
Handles user registration, login, and credential management
"""

import json
import os
import hashlib
from datetime import datetime

class UserAuth:
    def __init__(self):
        """Initialize authentication system"""
        self.users_file = "users_data.json"
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Create users file if it doesn't exist"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({"users": []}, f, indent=4)
    
    def _hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self):
        """Load all users from file"""
        try:
            with open(self.users_file, 'r') as f:
                data = json.load(f)
            return data.get("users", [])
        except Exception as e:
            print(f"Error loading users: {e}")
            return []
    
    def _save_users(self, users):
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump({"users": users}, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False
    
    def signup(self, username, email, password, phone, full_name):
        """
        Register a new user
        
        Args:
            username (str): Username for login
            email (str): User email
            password (str): User password (will be hashed)
            phone (str): Phone number
            full_name (str): Full name of user
            
        Returns:
            dict: Status and message
        """
        # Validate inputs
        if not all([username, email, password, phone, full_name]):
            return {"success": False, "message": "All fields are required"}
        
        if len(password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters"}
        
        users = self._load_users()
        
        # Check if user already exists
        if any(u["username"] == username for u in users):
            return {"success": False, "message": "Username already exists"}
        
        if any(u["email"] == email for u in users):
            return {"success": False, "message": "Email already registered"}
        
        # Create new user
        new_user = {
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password),
            "phone": phone,
            "full_name": full_name,
            "created_at": datetime.now().isoformat(),
            "citizen_id": f"CITIZEN_{len(users) + 1:04d}"
        }
        
        users.append(new_user)
        
        if self._save_users(users):
            # Also register in MySQL citizens table
            try:
                from mysql_database import MunicipalDatabase
                db = MunicipalDatabase()
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT IGNORE INTO citizens (citizen_id, name, email, phone)
                    VALUES (%s, %s, %s, %s)
                """, (new_user["citizen_id"], full_name, email, phone))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"⚠️ Could not register citizen in MySQL: {e}")
            
            return {
                "success": True, 
                "message": "Account created successfully! Please login.",
                "citizen_id": new_user["citizen_id"]
            }
        else:
            return {"success": False, "message": "Failed to create account"}
    
    def login(self, username, password):
        """
        Authenticate user
        
        Args:
            username (str): Username
            password (str): Password (will be hashed and compared)
            
        Returns:
            dict: Status, message, and user info if successful
        """
        users = self._load_users()
        
        # Find user
        user = next((u for u in users if u["username"] == username), None)
        
        if not user:
            return {"success": False, "message": "Username not found"}
        
        # Check password
        if user["password_hash"] != self._hash_password(password):
            return {"success": False, "message": "Incorrect password"}
        
        # Return user info (excluding password hash)
        return {
            "success": True,
            "message": "Login successful!",
            "user": {
                "username": user["username"],
                "email": user["email"],
                "phone": user["phone"],
                "full_name": user["full_name"],
                "citizen_id": user["citizen_id"]
            }
        }
    
    def get_user(self, username):
        """Get user information by username"""
        users = self._load_users()
        user = next((u for u in users if u["username"] == username), None)
        
        if user:
            return {
                "username": user["username"],
                "email": user["email"],
                "phone": user["phone"],
                "full_name": user["full_name"],
                "citizen_id": user["citizen_id"]
            }
        return None
    
    def update_user_phone(self, username, new_phone):
        """Update user phone number"""
        users = self._load_users()
        user = next((u for u in users if u["username"] == username), None)
        
        if user:
            user["phone"] = new_phone
            self._save_users(users)
            return {"success": True, "message": "Phone updated"}
        
        return {"success": False, "message": "User not found"}


# Initialize auth system
auth = UserAuth()
