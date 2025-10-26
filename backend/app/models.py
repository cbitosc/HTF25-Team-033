from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    total_chunks: int
    file_size: int
    summary: str
    key_topics: List[str]
    estimated_reading_time: int
    complexity_score: float

class QuestionRequest(BaseModel):
    question: str
    doc_ids: List[str]
    conversation_history: Optional[List[Dict[str, str]]] = []

class Citation(BaseModel):
    text: str
    doc_id: str
    chunk_id: int
    page_number: Optional[int]
    confidence: float

class Answer(BaseModel):
    answer: str
    citations: List[Citation]
    confidence_score: float
    suggested_questions: List[str]
    processing_time: float
    answer_type: Optional[str] = "document_only"  

class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    upload_time: datetime
    total_pages: int
    total_chunks: int
    summary: str
    key_topics: List[str]

class ComparisonRequest(BaseModel):
    doc_ids: List[str]
    question: str