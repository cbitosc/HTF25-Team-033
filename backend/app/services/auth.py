import os
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.models import User, UserCreate, UserLogin, TokenData
from app.services.database import db_service

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__min_rounds=4,
    bcrypt__max_rounds=31
)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.users_collection = None
    
    async def initialize(self):
        """Initialize the auth service"""
        self.users_collection = db_service.get_collection("users")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        # Truncate password to 72 bytes for bcrypt compatibility
        truncated_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(truncated_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        # Debug: Check password length
        password_bytes = password.encode('utf-8')
        print(f"DEBUG: Password length: {len(password)} chars, {len(password_bytes)} bytes")
        
        try:
            # Simple approach - just hash the password as-is
            return pwd_context.hash(password)
        except Exception as e:
            print(f"DEBUG: Bcrypt error: {e}")
            # Fallback: truncate if needed
            truncated_password = password_bytes[:72].decode('utf-8', errors='ignore')
            return pwd_context.hash(truncated_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        if self.users_collection is None:
            await self.initialize()
        
        user_doc = await self.users_collection.find_one({"email": email})
        if not user_doc:
            return None
        
        if not self.verify_password(password, user_doc["hashed_password"]):
            return None
        
        return User(
            id=str(user_doc["_id"]),
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            created_at=user_doc["created_at"],
            is_active=user_doc.get("is_active", True)
        )
    
    async def create_user(self, user: UserCreate) -> User:
        """Create a new user"""
        if self.users_collection is None:
            await self.initialize()
        
        # Check if user already exists
        existing_user = await self.users_collection.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user document
        user_doc = {
            "email": user.email,
            "full_name": user.full_name,
            "hashed_password": self.get_password_hash(user.password),
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = await self.users_collection.insert_one(user_doc)
        
        return User(
            id=str(result.inserted_id),
            email=user.email,
            full_name=user.full_name,
            created_at=user_doc["created_at"],
            is_active=True
        )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        if self.users_collection is None:
            await self.initialize()
        
        user_doc = await self.users_collection.find_one({"email": email})
        if not user_doc:
            return None
        
        return User(
            id=str(user_doc["_id"]),
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            created_at=user_doc["created_at"],
            is_active=user_doc.get("is_active", True)
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        if self.users_collection is None:
            await self.initialize()
        
        try:
            user_doc = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                return None
            
            return User(
                id=str(user_doc["_id"]),
                email=user_doc["email"],
                full_name=user_doc["full_name"],
                created_at=user_doc["created_at"],
                is_active=user_doc.get("is_active", True)
            )
        except Exception:
            return None

# Global auth service instance
auth_service = AuthService()

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await auth_service.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return user

# Optional dependency for endpoints that can work with or without authentication
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
