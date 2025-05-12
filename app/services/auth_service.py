from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.services.broski_db_service import BroskiDatabaseService
import os
from dotenv import load_dotenv

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY","d1c5f0e3a2b7c9d8e6f4a2b0c9d8e6f4a2b0c9d8e6f4a2b0c9d8")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    def __init__(self):
        self.db = BroskiDatabaseService()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by email and password"""
        user = self.db.get_user_by_email(email)
        if not user:
            print(f"User with email {email} not found")
            return None
        
        # For development only: check if password matches directly (no hashing)
        if user["password_hash"] == password:
            print(f"User {email} authenticated with plain password")
            return user
        
        # Regular password verification with hash
        if not self.verify_password(password, user["password_hash"]):
            print(f"Password verification failed for {email}")
            return None
        
        print(f"User {email} authenticated successfully")
        return user
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def create_user(self, name: str, email: str, role: str, password: str, is_admin: bool = False) -> bool:
        """Create a new user"""
        password_hash = self.get_password_hash(password)
        return self.db.create_user(name, email, role, password_hash, is_admin)
    
    def create_admin_if_not_exists(self):
        """Create admin user if it doesn't exist"""
        try:
            # Check if admin exists
            admin = self.db.get_user_by_email("admin@sofabi.com")
            if not admin:
                # Create admin user with default credentials
                admin_data = {
                    "name": "Admin",
                    "email": "admin@sofabi.com",
                    "password": "$2b$12$q.wPaVlNumtSZH71kO9xRe33PbMH3uf1T3AUnaRaybmzFuiCbQqLm",  # You should use a more secure password in production
                    "role": "admin",
                    "is_admin": True
                }
                self.create_user(
                    admin_data["name"],
                    admin_data["email"],
                    admin_data["role"],
                    admin_data["password"],
                    admin_data["is_admin"]
                )
                print("Admin user created successfully")
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Vérifie et décode un token JWT"""
        try:
            payload = self.decode_token(token)
            if not payload:
                return None
            
            email = payload.get("sub")
            if not email:
                return None
            
            user = self.db.get_user_by_email(email)
            if not user:
                return None
            
            # Ajouter les informations du token
            user["role"] = payload.get("role", user.get("role", "guest"))
            user["is_admin"] = payload.get("is_admin", user.get("is_admin", False))
            
            return user
        except Exception as e:
            print(f"Error verifying token: {str(e)}")
            return None




