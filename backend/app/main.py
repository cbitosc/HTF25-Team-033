from app.utils.chromadb_patch import patch_chromadb_telemetry
patch_chromadb_telemetry()

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import os
import shutil
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from app.models import *
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import EmbeddingService
from app.services.qa_engine import QAEngine
from app.services.auth import auth_service, get_current_user, get_current_user_optional
from app.services.database import db_service

# Initialize FastAPI app
app = FastAPI(title="Document QA System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
doc_processor = DocumentProcessor()
embedding_service = EmbeddingService()
qa_engine = QAEngine()

# Database collections
documents_collection = None
chat_history_collection = None

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# JWT settings
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        await db_service.connect()
        await auth_service.initialize()
        
        # Initialize collections
        global documents_collection, chat_history_collection
        documents_collection = db_service.get_collection("documents")
        chat_history_collection = db_service.get_collection("chat_history")
        
        print("🚀 Application started successfully")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    await db_service.disconnect()
    print("🛑 Application shutdown complete")

@app.get("/")
async def root():
    return {"message": "Document QA System API", "version": "1.0.0"}

# Authentication endpoints
@app.post("/api/auth/signup")
async def signup(user: UserCreate):
    """Create a new user account"""
    try:
        new_user = await auth_service.create_user(user)
        
        # Create access token for the new user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": new_user.email}, expires_delta=access_token_expires
        )
        
        return {
            "user": new_user,
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error creating user: {str(e)}")

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return access token"""
    try:
        user = await auth_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error during login: {str(e)}")

@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.post("/api/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload and process a document"""
    try:
        # Validate file
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(400, "Only PDF and TXT files are supported")
        
        # Check file size (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"File size exceeds 50MB limit. Current size: {len(file_content) / (1024*1024):.1f}MB")
        
        # Reset file pointer for processing
        await file.seek(0)
        
        # Save file
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        result = await doc_processor.process_document(file_path, file.filename)
        
        # Embed chunks
        embedding_service.embed_chunks(result["chunks"], result["doc_id"])
        
        # Store document in MongoDB
        document_doc = {
            "doc_id": result["doc_id"],
            "user_id": current_user.id,
            "filename": result["filename"],
            "file_path": file_path,
            "upload_time": datetime.utcnow(),
            "total_pages": result["total_pages"],
            "metadata": result["metadata"]
        }
        
        await documents_collection.insert_one(document_doc)
        
        return DocumentUploadResponse(
            doc_id=result["doc_id"],
            filename=result["filename"],
            total_chunks=result["metadata"]["total_chunks"],
            file_size=os.path.getsize(file_path),
            summary=result["metadata"]["summary"],
            key_topics=result["metadata"]["key_topics"],
            estimated_reading_time=result["metadata"]["estimated_reading_time"],
            complexity_score=result["metadata"]["complexity_score"]
        )
    
    except Exception as e:
        raise HTTPException(500, f"Error processing document: {str(e)}")

@app.post("/api/ask", response_model=Answer)
async def ask_question(request: QuestionRequest, current_user: User = Depends(get_current_user)):
    """Ask a question about uploaded documents"""
    try:
        # Validate documents exist and belong to user
        for doc_id in request.doc_ids:
            doc_doc = await documents_collection.find_one({
                "doc_id": doc_id,
                "user_id": current_user.id
            })
            if not doc_doc:
                raise HTTPException(404, f"Document {doc_id} not found")
        
        # Search for relevant chunks
        relevant_chunks = embedding_service.search_similar(
            request.question,
            doc_ids=request.doc_ids,
            top_k=10
        )
        
        if not relevant_chunks:
            raise HTTPException(404, "No relevant information found")
        
        # Generate answer
        result = qa_engine.generate_answer(
            request.question,
            relevant_chunks,
            request.conversation_history
        )
        
        return Answer(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error generating answer: {str(e)}")

@app.get("/api/documents", response_model=List[DocumentMetadata])
async def list_documents(current_user: User = Depends(get_current_user)):
    """List all uploaded documents for the current user"""
    try:
        # Query documents for the current user
        cursor = documents_collection.find({"user_id": current_user.id}).sort("upload_time", -1)
        documents = []
        
        async for doc in cursor:
            documents.append(DocumentMetadata(
                doc_id=doc["doc_id"],
                filename=doc["filename"],
                upload_time=doc["upload_time"],
                total_pages=doc["total_pages"],
                total_chunks=doc["metadata"]["total_chunks"],
                summary=doc["metadata"]["summary"],
                key_topics=doc["metadata"]["key_topics"],
                estimated_reading_time=doc["metadata"]["estimated_reading_time"],
                complexity_score=doc["metadata"]["complexity_score"]
            ))
        
        return documents
    except Exception as e:
        raise HTTPException(500, f"Error loading documents: {str(e)}")

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: User = Depends(get_current_user)):
    """Delete a document"""
    try:
        # Find document in MongoDB
        doc_doc = await documents_collection.find_one({
            "doc_id": doc_id,
            "user_id": current_user.id
        })
        
        if not doc_doc:
            raise HTTPException(404, "Document not found")
        
        # Delete from vector store
        embedding_service.delete_document(doc_id)
        
        # Delete file
        file_path = doc_doc["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from MongoDB
        await documents_collection.delete_one({
            "doc_id": doc_id,
            "user_id": current_user.id
        })
        
        return {"message": "Document deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error deleting document: {str(e)}")

@app.post("/api/compare")
async def compare_documents(request: ComparisonRequest):
    """Compare multiple documents"""
    try:
        # Get chunks from each document
        doc_chunks_map = {}
        for doc_id in request.doc_ids:
            chunks = embedding_service.search_similar(
                request.question,
                doc_ids=[doc_id],
                top_k=3
            )
            doc_chunks_map[doc_id] = chunks
        
        # Generate comparison
        comparison = qa_engine.generate_comparison(request.question, doc_chunks_map)
        
        return {"comparison": comparison, "documents": list(doc_chunks_map.keys())}
    
    except Exception as e:
        raise HTTPException(500, f"Error comparing documents: {str(e)}")

@app.get("/api/suggestions/{doc_id}")
async def get_question_suggestions(doc_id: str, current_user: User = Depends(get_current_user)):
    """Get suggested questions for a document"""
    try:
        # Find document in MongoDB
        doc_doc = await documents_collection.find_one({
            "doc_id": doc_id,
            "user_id": current_user.id
        })
        
        if not doc_doc:
            raise HTTPException(404, "Document not found")
        
        topics = doc_doc["metadata"]["key_topics"]
        filename = doc_doc["filename"]
        
        # Generate better questions based on document content
        suggestions = [
            f"What are the main topics covered in {filename}?",
            f"Can you summarize the key points about {topics[0] if topics else 'this document'}?",
            "What are the most important findings or conclusions?",
            f"Explain the concept of {topics[1] if len(topics) > 1 else 'the main topic'} in detail.",
            f"How does {topics[2] if len(topics) > 2 else 'this document'} relate to {topics[0] if topics else 'the main theme'}?"
        ]
        
        return {"suggestions": suggestions}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error getting suggestions: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)