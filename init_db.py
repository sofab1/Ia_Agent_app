import psycopg2
from psycopg2 import sql
import getpass

def init_db():
    # Get PostgreSQL superuser password
    pg_password = getpass.getpass("Enter PostgreSQL superuser password: ")
    
    # Connect as superuser
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password=pg_password
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Check if broski database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'broski'")
            if not cur.fetchone():
                # Create database
                cur.execute(sql.SQL("CREATE DATABASE broski"))
                print("Database 'broski' created.")
            
            # Check if samsam user exists
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'samsam'")
            if not cur.fetchone():
                # Create user
                cur.execute(sql.SQL("CREATE USER samsam WITH PASSWORD 'root'"))
                print("User 'samsam' created.")
            
            # Grant privileges
            cur.execute(sql.SQL("ALTER USER samsam WITH SUPERUSER"))
            print("User 'samsam' granted superuser privileges.")
    finally:
        conn.close()
    
    # Connect to broski database
    conn = psycopg2.connect(
        host="localhost",
        database="broski",
        user="postgres",
        password=pg_password
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Check if tables exist
            cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
            """)
            users_exists = cur.fetchone()[0]
            
            cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'interactions'
            )
            """)
            interactions_exists = cur.fetchone()[0]
            
            # Create sequence if it doesn't exist
            cur.execute("CREATE SEQUENCE IF NOT EXISTS user_id_seq START 1001")
            
            # Create users table if it doesn't exist
            if not users_exists:
                cur.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE DEFAULT nextval('user_id_seq'),
                    name VARCHAR(255),
                    email VARCHAR(255) UNIQUE,
                    role VARCHAR(100),
                    password_hash VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                print("Users table created.")
            
            # Create interactions table if it doesn't exist
            if not interactions_exists:
                cur.execute("""
                CREATE TABLE interactions (
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
                print("Interactions table created.")
            
            # Grant privileges
            cur.execute("GRANT ALL PRIVILEGES ON DATABASE broski TO samsam")
            cur.execute("GRANT ALL PRIVILEGES ON SCHEMA public TO samsam")
            cur.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO samsam")
            cur.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO samsam")
            
            # Change ownership
            cur.execute("ALTER TABLE users OWNER TO samsam")
            cur.execute("ALTER TABLE interactions OWNER TO samsam")
            cur.execute("ALTER SEQUENCE user_id_seq OWNER TO samsam")
            
            print("Permissions granted.")
            
            # Check if admin user exists
            cur.execute("SELECT 1 FROM users WHERE email = 'admin@sofabi.com'")
            if not cur.fetchone():
                # Create admin user
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                password_hash = pwd_context.hash("admin123")
                
                cur.execute("""
                INSERT INTO users (name, email, role, password_hash, is_admin)
                VALUES (%s, %s, %s, %s, %s)
                """, ("Admin", "admin@sofabi.com", "admin", password_hash, True))
                
                print("Admin user created.")
            else:
                print("Admin user already exists.")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()