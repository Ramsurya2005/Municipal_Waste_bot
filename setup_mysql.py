"""
MySQL Database Setup Script
Run this to initialize the MySQL database for the municipal chatbot
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect without specifying database
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '')
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            db_name = os.getenv('MYSQL_DATABASE', 'municipal_chatbot')
            
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"✅ Database '{db_name}' created successfully")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Error: {e}")
        return False

def test_connection():
    """Test MySQL connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'municipal_chatbot')
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ Successfully connected to MySQL Server version {db_info}")
            
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print(f"✅ You're connected to database: {record[0]}")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure MySQL is installed and running")
        print("   2. Check your credentials in .env file")
        print("   3. Verify MySQL port (default: 3306)")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 MySQL Database Setup for Municipal Chatbot")
    print("=" * 60)
    print()
    
    print("📝 Configuration:")
    print(f"   Host: {os.getenv('MYSQL_HOST', 'localhost')}")
    print(f"   Port: {os.getenv('MYSQL_PORT', 3306)}")
    print(f"   User: {os.getenv('MYSQL_USER', 'root')}")
    print(f"   Database: {os.getenv('MYSQL_DATABASE', 'municipal_chatbot')}")
    print()
    
    # Create database
    print("Step 1: Creating database...")
    if create_database():
        print()
        
        # Test connection
        print("Step 2: Testing connection...")
        if test_connection():
            print()
            print("✨ Setup complete! You can now run the application.")
            print("   Run: streamlit run app.py")
        else:
            print()
            print("⚠️ Connection test failed. Please check your configuration.")
    else:
        print()
        print("⚠️ Database creation failed. Please check your MySQL installation.")
