from typing import List, Dict, Tuple
import re

class CitationEngine:
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
            'this', 'that', 'these', 'those', 'it', 'its', 'which', 'who', 'what',
            'have', 'has', 'had', 'will', 'would', 'can', 'could', 'may', 'might',
            'should', 'shall', 'must', 'do', 'does', 'did', 'not', 'no', 'nor',
            'am', 'were', 'been', 'being', 'you', 'your', 'we', 'our', 'they', 'their'
        }
    
    def create_citations(self, chunks: List[Dict], answer_text: str) -> List[Dict]:
        """
        Create citations by matching answer text with source chunks
        """
        citations = []
        
        for idx, chunk in enumerate(chunks):
            # Calculate multiple relevance metrics
            word_overlap = self._calculate_word_overlap(chunk["text"], answer_text)
            semantic_score = chunk.get("confidence", 0.5)  # From embedding similarity
            position_bonus = (len(chunks) - idx) / len(chunks) * 0.2  # Earlier results slightly favored
            
            # Combined relevance score
            relevance_score = (word_overlap * 0.5) + (semantic_score * 0.3) + position_bonus
            
            citation = {
                "citation_id": idx + 1,
                "text": self._extract_relevant_snippet(chunk["text"], answer_text),
                "full_text": chunk["text"][:500],
                "doc_id": chunk["doc_id"],
                "chunk_id": chunk["chunk_id"],
                "page_number": chunk.get("page_number", 1),
                "confidence": semantic_score,
                "relevance_score": round(relevance_score, 3),
                "word_overlap": round(word_overlap, 3)
            }
            
            citations.append(citation)
        
        # Sort by combined relevance
        citations.sort(key=lambda x: (-x["relevance_score"], -x["confidence"]))
        
        return citations[:5]
    
    def _calculate_word_overlap(self, source_text: str, answer_text: str) -> float:
        """
        Calculate meaningful word overlap between source and answer
        """
        # Extract meaningful words (longer than 3 chars, not stop words)
        source_words = set(
            word.lower() for word in re.findall(r'\b\w+\b', source_text)
            if len(word) > 3 and word.lower() not in self.stop_words
        )
        
        answer_words = set(
            word.lower() for word in re.findall(r'\b\w+\b', answer_text)
            if len(word) > 3 and word.lower() not in self.stop_words
        )
        
        if not answer_words:
            return 0.0
        
        # Calculate overlap
        intersection = len(source_words.intersection(answer_words))
        
        # Normalize by answer length (how much of answer is supported)
        overlap_score = intersection / len(answer_words)
        
        return min(1.0, overlap_score)
    
    def _extract_relevant_snippet(self, source_text: str, answer_text: str, context_window: int = 200) -> str:
        """
        Extract the most relevant snippet from source text
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', source_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return source_text[:context_window] + "..."
        
        # Extract meaningful words from answer
        answer_words = set(
            word.lower() for word in re.findall(r'\b\w{4,}\b', answer_text)
            if word.lower() not in self.stop_words
        )
        
        # Find best matching sentence
        best_sentence = sentences[0]
        best_score = 0
        
        for sentence in sentences:
            sentence_words = set(
                word.lower() for word in re.findall(r'\b\w{4,}\b', sentence)
            )
            overlap = len(answer_words.intersection(sentence_words))
            
            if overlap > best_score:
                best_score = overlap
                best_sentence = sentence
        
        # Return snippet with ellipsis
        snippet = best_sentence[:context_window]
        if len(best_sentence) > context_window:
            snippet += "..."
        
        return snippet
    
    def _calculate_relevance(self, source_text: str, answer_text: str) -> float:
        """Calculate relevance score"""
        return self._calculate_word_overlap(source_text, answer_text)
    
    def verify_citation_accuracy(self, answer: str, citations: List[Dict]) -> Dict:
        """
        Verify that citations actually support the answer
        """
        total_citations = len(citations)
        
        if total_citations == 0:
            return {
                "total_citations": 0,
                "relevant_citations": 0,
                "average_confidence": 0.0,
                "average_relevance": 0.0,
                "pages_cited": [],
                "citation_quality": "none"
            }
        
        # Count highly relevant citations (relevance > 0.3)
        relevant_citations = sum(1 for c in citations if c.get("relevance_score", 0) > 0.3)
        
        avg_confidence = sum(c.get("confidence", 0) for c in citations) / total_citations
        avg_relevance = sum(c.get("relevance_score", 0) for c in citations) / total_citations
        
        # Determine quality based on both metrics
        if avg_relevance > 0.5 and avg_confidence > 0.5:
            quality = "high"
        elif avg_relevance > 0.3 and avg_confidence > 0.3:
            quality = "medium"
        elif avg_relevance > 0.15 or avg_confidence > 0.15:
            quality = "acceptable"
        else:
            quality = "low"
        
        return {
            "total_citations": total_citations,
            "relevant_citations": relevant_citations,
            "average_confidence": round(avg_confidence, 2),
            "average_relevance": round(avg_relevance, 2),
            "pages_cited": sorted(set(c["page_number"] for c in citations)),
            "citation_quality": quality
        }