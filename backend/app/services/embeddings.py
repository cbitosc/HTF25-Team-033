import os
import sys
import logging
import warnings

# Suppress all warnings
warnings.filterwarnings('ignore')

# Set environment variables BEFORE any imports
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False'

# Disable all ChromaDB related logging
logging.getLogger('chromadb').setLevel(logging.CRITICAL)
logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)
logging.getLogger('posthog').setLevel(logging.CRITICAL)

# Create a dummy stderr that ignores telemetry messages
class FilteredStderr:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
    
    def write(self, message):
        # Filter out telemetry messages
        if 'telemetry' not in message.lower() and 'capture()' not in message:
            self.original_stderr.write(message)
    
    def flush(self):
        self.original_stderr.flush()

# Uncomment the next line to filter stderr (aggressive but effective)
# sys.stderr = FilteredStderr(sys.stderr)

from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Dict
import numpy as np

# Additional telemetry patch after import
try:
    import chromadb.telemetry.posthog as posthog
    
    # Replace all telemetry methods with no-ops
    class NoOpTelemetry:
        def __init__(self, *args, **kwargs):
            pass
        
        def capture(self, *args, **kwargs):
            pass
        
        def __call__(self, *args, **kwargs):
            pass
    
    posthog.Posthog = NoOpTelemetry
except:
    pass

class EmbeddingService:
    def __init__(self):
        print("⚙️  Initializing embedding service...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB with EphemeralClient
        self.client = chromadb.EphemeralClient()
        
        # Create or get collection
        try:
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            print("✓ ChromaDB collection ready")
        except Exception as e:
            print(f"✗ Collection creation error: {e}")
            self.collection = self.client.create_collection(name="documents")
    
    def embed_chunks(self, chunks: List[Dict], doc_id: str):
        """Embed and store document chunks"""
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        
        # Store in ChromaDB
        ids = [f"{doc_id}_{chunk['chunk_id']}" for chunk in chunks]
        metadatas = [
            {
                "doc_id": doc_id,
                "chunk_id": str(chunk["chunk_id"]),
                "page_number": str(chunk.get("page_number", 1)),
                "snippet": chunk.get("snippet", chunk["text"][:100])
            }
            for chunk in chunks
        ]
        
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✓ Embedded {len(chunks)} chunks for document {doc_id[:8]}")
    
    def search_similar(self, query: str, doc_ids: List[str] = None, top_k: int = 10) -> List[Dict]:
        """Search for similar chunks"""
        query_embedding = self.model.encode([query])[0]
        
        where_filter = None
        if doc_ids:
            where_filter = {"doc_id": {"$in": doc_ids}}
        
        try:
            # Suppress individual operation telemetry
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                if where_filter:
                    try:
                        available_docs = self.collection.get(where=where_filter)
                        available_count = len(available_docs['ids']) if available_docs.get('ids') else 0
                    except:
                        available_count = top_k
                else:
                    try:
                        available_count = self.collection.count()
                    except:
                        available_count = top_k
                
                n_results = min(top_k, max(1, available_count))
                
                results = self.collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=n_results,
                    where=where_filter
                )
            
            print(f"✓ Found {len(results['documents'][0])} relevant chunks")
            
        except Exception as e:
            print(f"✗ Search error: {e}")
            return []
        
        # Format results
        chunks = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                
                page_num = int(metadata.get("page_number", 1))
                confidence = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
                
                chunks.append({
                    "text": doc,
                    "doc_id": metadata["doc_id"],
                    "chunk_id": int(metadata["chunk_id"]),
                    "page_number": page_num,
                    "confidence": float(confidence),
                    "raw_distance": float(distance)
                })
        
        chunks.sort(key=lambda x: -x['confidence'])
        return chunks
    
    def delete_document(self, doc_id: str):
        """Delete all chunks of a document"""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                results = self.collection.get(where={"doc_id": doc_id})
                if results.get('ids'):
                    self.collection.delete(ids=results['ids'])
                    print(f"✓ Deleted document {doc_id[:8]}")
        except Exception as e:
            print(f"✗ Delete error: {e}")