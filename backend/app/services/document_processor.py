import fitz  # PyMuPDF
import uuid
import os
from typing import List, Dict, Tuple
import re
from collections import Counter
import numpy as np

class DocumentProcessor:
    def __init__(self):
        self.chunk_size = 800  # Increased for better context
        self.chunk_overlap = 100
        
    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, int, List[Dict]]:
        """Extract text from PDF with accurate page information"""
        try:
            doc = fitz.open(file_path)
            full_text = ""
            page_texts = []
            
            print(f"DEBUG: PDF has {len(doc)} pages")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                print(f"DEBUG: Page {page_num + 1} - Text length: {len(text)}")
                
                # Clean up text
                text = text.strip()
                
                if text:  # Only add non-empty pages
                    page_texts.append({
                        "page_number": page_num + 1,
                        "text": text,
                        "char_start": len(full_text),
                        "char_end": len(full_text) + len(text)
                    })
                    full_text += f"\n{text}\n"
                else:
                    print(f"DEBUG: Page {page_num + 1} is empty or contains no extractable text")
            
            doc.close()
            
            if not page_texts:
                print("WARNING: No text could be extracted from PDF. This might be a scanned document.")
                # Try to get at least some basic info
                doc = fitz.open(file_path)
                page_count = len(doc)
                doc.close()
                return "", page_count, []
            
            print(f"DEBUG: Successfully extracted text from {len(page_texts)} pages")
            return full_text, len(page_texts), page_texts
            
        except Exception as e:
            print(f"ERROR: Failed to extract text from PDF: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_txt(self, file_path: str) -> Tuple[str, int, List[Dict]]:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Split by paragraphs for page-like structure
        paragraphs = text.split('\n\n')
        page_texts = []
        char_pos = 0
        
        for i, para in enumerate(paragraphs):
            if para.strip():
                page_texts.append({
                    "page_number": i + 1,
                    "text": para,
                    "char_start": char_pos,
                    "char_end": char_pos + len(para)
                })
                char_pos += len(para) + 2  # +2 for \n\n
        
        return text, len(page_texts), page_texts
    
    def chunk_text(self, text: str, page_texts: List[Dict]) -> List[Dict]:
        """Chunk text with accurate page tracking"""
        words = text.split()
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate character position of this chunk
            char_start = len(' '.join(words[:i]))
            char_end = char_start + len(chunk_text)
            
            # Find which page this chunk belongs to
            page_num = self._find_page_for_chunk(char_start, char_end, page_texts)
            
            # Get a snippet for better context matching
            snippet = chunk_text[:100] if len(chunk_text) > 100 else chunk_text
            
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "page_number": page_num,
                "start_index": i,
                "end_index": i + len(chunk_words),
                "char_start": char_start,
                "char_end": char_end,
                "snippet": snippet
            })
            chunk_id += 1
        
        return chunks
    
    def _find_page_for_chunk(self, char_start: int, char_end: int, page_texts: List[Dict]) -> int:
        """Find which page a chunk belongs to based on character position"""
        # Find the page that contains the majority of this chunk
        for page_info in page_texts:
            page_start = page_info.get("char_start", 0)
            page_end = page_info.get("char_end", float('inf'))
            
            # Check if chunk overlaps with this page
            overlap_start = max(char_start, page_start)
            overlap_end = min(char_end, page_end)
            
            if overlap_end > overlap_start:
                # This page contains part of the chunk
                overlap_ratio = (overlap_end - overlap_start) / (char_end - char_start)
                
                if overlap_ratio > 0.3:  # If >30% of chunk is in this page
                    return page_info["page_number"]
        
        # Fallback: find closest page
        chunk_midpoint = (char_start + char_end) / 2
        closest_page = 1
        min_distance = float('inf')
        
        for page_info in page_texts:
            page_midpoint = (page_info.get("char_start", 0) + page_info.get("char_end", 0)) / 2
            distance = abs(chunk_midpoint - page_midpoint)
            
            if distance < min_distance:
                min_distance = distance
                closest_page = page_info["page_number"]
        
        return closest_page
    
    def generate_summary(self, text: str) -> str:
        """Generate a quick extractive summary"""
        sentences = re.split(r'[.!?]+', text)
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 50][:3]
        return '. '.join(meaningful) + '.' if meaningful else "Document uploaded successfully."
    
    def extract_key_topics(self, text: str, top_n: int = 10) -> List[str]:
        """Extract key topics using simple frequency analysis"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                     'this', 'that', 'these', 'those', 'it', 'its', 'which', 'who', 'what',
                     'have', 'has', 'had', 'will', 'would', 'can', 'could', 'may', 'might'}
        
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        filtered_words = [w for w in words if w not in stop_words]
        
        counter = Counter(filtered_words)
        return [word for word, count in counter.most_common(top_n)]
    
    def calculate_complexity_score(self, text: str) -> float:
        """Calculate document complexity (0-1 scale)"""
        words = text.split()
        if not words:
            return 0.0
        
        avg_word_length = sum(len(w) for w in words) / len(words)
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = len(words) / max(len(sentences), 1)
        
        complexity = min((avg_word_length / 10 + avg_sentence_length / 30) / 2, 1.0)
        return round(complexity, 2)
    
    def estimate_reading_time(self, text: str) -> int:
        """Estimate reading time in minutes (assuming 200 words/min)"""
        word_count = len(text.split())
        return max(1, word_count // 200)
    
    async def process_document(self, file_path: str, filename: str) -> Dict:
        """Main processing pipeline"""
        try:
            doc_id = str(uuid.uuid4())
            
            print(f"DEBUG: Processing {filename}")
            
            # Extract text based on file type
            if filename.endswith('.pdf'):
                full_text, total_pages, page_texts = self.extract_text_from_pdf(file_path)
            else:
                full_text, total_pages, page_texts = self.extract_text_from_txt(file_path)
            
            # Check if we got any text
            if not full_text.strip():
                raise Exception(f"No text could be extracted from {filename}. This might be a scanned PDF or corrupted file.")
            
            # Chunk the text with accurate page tracking
            chunks = self.chunk_text(full_text, page_texts)
            
            if not chunks:
                raise Exception(f"No chunks could be created from {filename}. The document might be too short or contain no meaningful text.")
            
            print(f"Processed {filename}: {total_pages} pages, {len(chunks)} chunks")
            
            # Debug: Print first few chunks with their page numbers
            for chunk in chunks[:5]:
                print(f"Chunk {chunk['chunk_id']}: Page {chunk['page_number']}")
            
            # Generate metadata
            summary = self.generate_summary(full_text)
            key_topics = self.extract_key_topics(full_text)
            complexity = self.calculate_complexity_score(full_text)
            reading_time = self.estimate_reading_time(full_text)
            
            return {
                "doc_id": doc_id,
                "filename": filename,
                "full_text": full_text,
                "chunks": chunks,
                "total_pages": total_pages,
                "page_texts": page_texts,
                "metadata": {
                    "summary": summary,
                    "key_topics": key_topics,
                    "complexity_score": complexity,
                    "estimated_reading_time": reading_time,
                    "total_chunks": len(chunks)
                }
            }
            
        except Exception as e:
            print(f"ERROR: Failed to process {filename}: {e}")
            raise Exception(f"Failed to process document {filename}: {str(e)}")