import psycopg2
import contextlib
from psycopg2 import OperationalError
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BroskiDatabaseError(Exception):
    """Exception for Broski database errors"""
    pass

class BroskiDatabaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        """Initialize database connection settings"""
        # Try to load from environment variables
        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        # Print environment variables for debugging
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
        
        self.config = {
            "host": db_host,
            "database": db_name,
            "user": db_user,
            "password": db_password,
            "connect_timeout": 5
        }
        
        # Try to connect to the database to verify credentials
        try:
            with self._get_connection() as conn:
                print("Database connection successful!")
        except Exception as e:
            print(f"Database connection failed: {str(e)}")
            
        self._ensure_tables_exist()
    
    @contextlib.contextmanager
    def _get_connection(self):
        """Secure connection manager"""
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            conn.autocommit = False
            yield conn
        except OperationalError as e:
            raise BroskiDatabaseError(f"Connection failed: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def _ensure_tables_exist(self):
        """Create tables if they don't exist"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Users table with password field
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255),
                        email VARCHAR(255) UNIQUE,
                        role VARCHAR(100),
                        password_hash VARCHAR(255),
                        is_admin BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                    
                    # Interactions table
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS interactions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        question TEXT,
                        response TEXT,
                        query_type VARCHAR(50),
                        sql_query TEXT,
                        error_message TEXT,
                        error_code VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                    
                conn.commit()
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
    
    def log_interaction(self, user_data: Dict[str, Any], question: str, 
                        response: Dict[str, Any]) -> int:
        """Log a complete interaction"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Ensure user exists
                    user_id = self._ensure_user_exists(cur, user_data)
                    
                    # Extract data from response
                    query_type = response.get("type", "unknown")
                    error_message = None
                    error_code = None
                    sql_query = None
                    response_text = None
                    
                    if "error" in response:
                        error_message = response["error"].get("message", "Unknown error")
                        error_code = response["error"].get("code", "unknown_error")
                    else:
                        response_text = response.get("response", "")
                        if query_type == "sql" and "metadata" in response:
                            sql_query = response.get("metadata", {}).get("sql_query", "")
                    
                    # Insert interaction
                    cur.execute("""
                    INSERT INTO interactions 
                    (user_id, question, response, query_type, sql_query, error_message, error_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """, (user_id, question, response_text, query_type, sql_query, 
                          error_message, error_code))
                    
                    interaction_id = cur.fetchone()[0]
                    conn.commit()
                    return interaction_id
                    
        except Exception as e:
            print(f"Error logging interaction: {str(e)}")
            return -1
    
    def _ensure_user_exists(self, cursor, user_data: Dict[str, Any]) -> int:
        """Ensure user exists and return user ID"""
        cursor.execute(
            "SELECT id FROM users WHERE email = %s", 
            (user_data.get("email"),)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Insert new user
        cursor.execute("""
        INSERT INTO users (name, email, role)
        VALUES (%s, %s, %s)
        RETURNING id
        """, (
            user_data.get("name"), 
            user_data.get("email"),
            user_data.get("role")
        ))
        
        return cursor.fetchone()[0]
        
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, name, email, role, password_hash, is_admin FROM users WHERE email = %s",
                        (email,)
                    )
                    result = cur.fetchone()
                    
                    if not result:
                        return None
                    
                    return {
                        "id": result[0],
                        "name": result[1],
                        "email": result[2],
                        "role": result[3],
                        "password_hash": result[4],
                        "is_admin": result[5]
                    }
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None
            
    def create_user(self, name: str, email: str, role: str, password_hash: str, is_admin: bool = False) -> bool:
        """Create a new user with password"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (name, email, role, password_hash, is_admin) VALUES (%s, %s, %s, %s, %s)",
                        (name, email, role, password_hash, is_admin)
                    )
                    conn.commit()
                    return True
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return False
            
    def get_user_interactions(self, user_id=None, limit=100):
        """
        Get interactions from the database.
        If user_id is provided, get interactions for that user only.
        Otherwise, get all interactions up to the limit.
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    if user_id:
                        cur.execute(
                            """
                            SELECT id, user_id, question, response, created_at
                            FROM interactions
                            WHERE user_id = %s
                            ORDER BY created_at DESC
                            LIMIT %s
                            """,
                            (user_id, limit)
                        )
                    else:
                        cur.execute(
                            """
                            SELECT id, user_id, question, response, created_at
                            FROM interactions
                            ORDER BY created_at DESC
                            LIMIT %s
                            """,
                            (limit,)
                        )
                    
                    interactions = []
                    for row in cur.fetchall():
                        interactions.append({
                            "id": row[0],
                            "user_id": row[1],
                            "question": row[2],
                            "response": row[3],
                            "created_at": row[4]
                        })
                    
                    return interactions
        except Exception as e:
            print(f"Error getting interactions: {str(e)}")
            return []
            
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, name, email, role, password_hash, is_admin FROM users WHERE id = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    
                    if not result:
                        return None
                    
                    return {
                        "id": result[0],
                        "name": result[1],
                        "email": result[2],
                        "role": result[3],
                        "password_hash": result[4],
                        "is_admin": result[5]
                    }
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None










