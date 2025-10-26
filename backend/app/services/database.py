import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import asyncio

class DatabaseService:
    def __init__(self):
        # MongoDB connection string - you can set this in environment variables
        self.mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "documind")
        
        # Async client for FastAPI
        self.async_client: Optional[AsyncIOMotorClient] = None
        self.async_db = None
        
        # Sync client for initialization
        self.sync_client: Optional[MongoClient] = None
        self.sync_db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.async_client = AsyncIOMotorClient(self.mongo_url)
            self.async_db = self.async_client[self.database_name]
            
            # Test connection
            await self.async_client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {self.database_name}")
            
            # Create indexes
            await self.create_indexes()
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.async_client:
            self.async_client.close()
            print("🔌 Disconnected from MongoDB")
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            await self.async_db.users.create_index("email", unique=True)
            await self.async_db.users.create_index("created_at")
            
            # Documents collection indexes
            await self.async_db.documents.create_index("user_id")
            await self.async_db.documents.create_index("upload_time")
            await self.async_db.documents.create_index([("user_id", 1), ("upload_time", -1)])
            
            # Chat history collection indexes
            await self.async_db.chat_history.create_index("user_id")
            await self.async_db.chat_history.create_index([("user_id", 1), ("doc_ids", 1)])
            await self.async_db.chat_history.create_index("created_at")
            
            print("📊 Database indexes created successfully")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        if self.async_db is None:
            raise Exception("Database not connected. Call connect() first.")
        return self.async_db[collection_name]

# Global database instance
db_service = DatabaseService()
