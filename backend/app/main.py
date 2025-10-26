from app.utils.chromadb_patch import patch_chromadb_telemetry
patch_chromadb_telemetry()

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil
from typing import List
import uuid
from datetime import datetime

from app.models import *
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import EmbeddingService
from app.services.qa_engine import QAEngine

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

# In-memory storage (for demo - use DB in production)
documents_store = {}
conversations_store = {}

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Document QA System API", "version": "1.0.0"}

@app.post("/api/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Validate file
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(400, "Only PDF and TXT files are supported")
        
        # Save file
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        result = await doc_processor.process_document(file_path, file.filename)
        
        # Embed chunks
        embedding_service.embed_chunks(result["chunks"], result["doc_id"])
        
        # Store metadata
        documents_store[result["doc_id"]] = {
            "filename": result["filename"],
            "upload_time": datetime.now(),
            "file_path": file_path,
            "metadata": result["metadata"],
            "total_pages": result["total_pages"]
        }
        
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
async def ask_question(request: QuestionRequest):
    """Ask a question about uploaded documents"""
    try:
        # Validate documents exist
        for doc_id in request.doc_ids:
            if doc_id not in documents_store:
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
async def list_documents():
    """List all uploaded documents"""
    documents = []
    for doc_id, doc_info in documents_store.items():
        documents.append(DocumentMetadata(
            doc_id=doc_id,
            filename=doc_info["filename"],
            upload_time=doc_info["upload_time"],
            total_pages=doc_info["total_pages"],
            total_chunks=doc_info["metadata"]["total_chunks"],
            summary=doc_info["metadata"]["summary"],
            key_topics=doc_info["metadata"]["key_topics"]
        ))
    return documents

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    if doc_id not in documents_store:
        raise HTTPException(404, "Document not found")
    
    # Delete from vector store
    embedding_service.delete_document(doc_id)
    
    # Delete file
    file_path = documents_store[doc_id]["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove from store
    del documents_store[doc_id]
    
    return {"message": "Document deleted successfully"}

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
async def get_question_suggestions(doc_id: str):
    """Get suggested questions for a document"""
    if doc_id not in documents_store:
        raise HTTPException(404, "Document not found")
    
    doc_info = documents_store[doc_id]
    topics = doc_info["metadata"]["key_topics"]
    filename = doc_info["filename"]
    
    # Generate better questions based on document content
    suggestions = [
        f"What are the main topics covered in {filename}?",
        f"Can you summarize the key points about {topics[0] if topics else 'this document'}?",
        "What are the most important findings or conclusions?",
        f"Explain the concept of {topics[1] if len(topics) > 1 else 'the main topic'} in detail.",
        f"How does {topics[2] if len(topics) > 2 else 'this document'} relate to {topics[0] if topics else 'the main theme'}?"
    ]
    
    return {"suggestions": suggestions}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)