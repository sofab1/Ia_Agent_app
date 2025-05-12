import psycopg2
import os
from dotenv import load_dotenv
import sys

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Load environment variables
print("Loading environment variables...")
load_dotenv(verbose=True)

def test_connection():
    # Get database credentials from environment variables
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    print(f"Environment variables:")
    print(f"DB_HOST: {db_host}")
    print(f"DB_NAME: {db_name}")
    print(f"DB_USER: {db_user}")
    print(f"DB_PASSWORD: {'*****' if db_password else 'Not set'}")
    
    # If any of the required variables are missing, use hardcoded values
    if not db_host or not db_name or not db_user or not db_password:
        print("Using hardcoded database credentials...")
        db_host = "localhost"
        db_name = "broski"
        db_user = "postgres"
        db_password = "your_actual_password"  # Replace with your actual password
    
    print(f"Connecting to PostgreSQL database:")
    print(f"Host: {db_host}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Password: {'*****' if db_password else 'Not set'}")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=5
        )
        
        # Create a cursor
        with conn.cursor() as cur:
            # Check if users table exists
            cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
            """)
            users_exists = cur.fetchone()[0]
            
            if users_exists:
                print("Users table exists.")
                
                # Count users
                cur.execute("SELECT COUNT(*) FROM users")
                user_count = cur.fetchone()[0]
                print(f"Number of users: {user_count}")
                
                # Check for admin user
                cur.execute("SELECT * FROM users WHERE email = 'admin@sofabi.com'")
                admin = cur.fetchone()
                if admin:
                    print("Admin user exists.")
                else:
                    print("Admin user does not exist.")
            else:
                print("Users table does not exist.")
        
        print("Database connection successful!")
        conn.close()
        
    except Exception as e:
        print(f"Database connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection()

