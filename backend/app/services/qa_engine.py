import google.generativeai as genai
from typing import List, Dict
import os
import time
import re
from app.services.citation_engine import CitationEngine

class QAEngine:
    def __init__(self):
        # api_key = os.getenv("GEMINI_API_KEY")
        # if not api_key:
        #     raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key="AIzaSyCJpRGChWlmchjCx4dLjY_xe5F8kSvds9M")
        
        self.generation_config = {
            'temperature': 0.9,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 8192,
        }
        
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=self.generation_config
        )
        
        self.citation_engine = CitationEngine()
    
    def generate_answer(self, question: str, context_chunks: List[Dict], 
                       conversation_history: List[Dict] = []) -> Dict:
        """Generate answer using Gemini with enhanced citations"""
        start_time = time.time()
        
        try:
            # Build context from chunks
            context = self._build_context(context_chunks)
            
            # Build conversation history
            history_text = self._build_history(conversation_history)
            
            # Determine if this is a general knowledge question
            is_general_question = self._is_general_knowledge_question(question, context_chunks)
            
            # Create appropriate prompt
            if is_general_question:
                prompt = self._create_hybrid_prompt(question, context, history_text)
            else:
                prompt = self._create_prompt(question, context, history_text)
            
            print(f"\n=== Generating answer for: {question} ===")
            print(f"Question type: {'Hybrid (document + general knowledge)' if is_general_question else 'Document-only'}")
            print(f"Using {len(context_chunks)} context chunks from pages: {[c.get('page_number') for c in context_chunks]}")
            
            # Generate response with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    answer_text = response.text
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(1)
            
            # Use citation engine to create enhanced citations
            citations = self.citation_engine.create_citations(context_chunks, answer_text)
            
            # Get citation verification
            citation_report = self.citation_engine.verify_citation_accuracy(answer_text, citations)
            
            print(f"Citation quality: {citation_report['citation_quality']}")
            print(f"Pages cited: {citation_report['pages_cited']}")
            
            # Generate follow-up questions
            suggested_questions = self._generate_suggestions(question, answer_text, is_general_question)
            
            # Calculate overall confidence
            confidence = citation_report['average_confidence']
            
            processing_time = time.time() - start_time
            
            return {
                "answer": answer_text,
                "citations": citations,
                "confidence_score": confidence,
                "suggested_questions": suggested_questions,
                "processing_time": round(processing_time, 2),
                "citation_report": citation_report,
                "answer_type": "hybrid" if is_general_question else "document_only"
            }
        
        except Exception as e:
            print(f"Error generating answer: {e}")
            processing_time = time.time() - start_time
            
            return {
                "answer": f"I encountered an error processing your question: {str(e)}. Please try rephrasing or check if the API key is valid.",
                "citations": [],
                "confidence_score": 0.0,
                "suggested_questions": [
                    "Can you rephrase your question?",
                    "What specific aspect would you like to know about?"
                ],
                "processing_time": round(processing_time, 2)
            }
    
    def _is_general_knowledge_question(self, question: str, context_chunks: List[Dict]) -> bool:
        """
        Determine if the question asks for general knowledge that might not be in the document
        """
        question_lower = question.lower()
        
        # Keywords that suggest the user wants general explanations
        general_keywords = [
            'how to', 'how can', 'ways to', 'methods to', 'techniques to',
            'improve', 'optimize', 'better', 'efficient', 'best practice',
            'explain', 'what is', 'what are', 'define', 'describe',
            'compare', 'difference between', 'vs', 'versus'
        ]
        
        # Check if question contains general knowledge indicators
        is_general = any(keyword in question_lower for keyword in general_keywords)
        
        # Also check if context seems limited
        if context_chunks:
            # If confidence scores are low, it might need general knowledge
            avg_confidence = sum(c.get('confidence', 0) for c in context_chunks) / len(context_chunks)
            if avg_confidence < 0.5:
                is_general = True
        
        return is_general
    
    def _create_hybrid_prompt(self, question: str, context: str, history: str) -> str:
        """
        Create a prompt that combines document context with general knowledge
        """
        prompt = f"""You are an intelligent document analysis assistant with expertise in computer science and algorithms.

{history}

Context from the document (with page numbers):
{context}

Question: {question}

Instructions:
1. FIRST, check what information is available in the provided document context
2. If the document contains relevant information, cite it with page numbers
3. THEN, supplement with your general knowledge to give a complete, helpful answer
4. Clearly distinguish between:
   - What comes from the document (cite pages)
   - What comes from general knowledge (say "Based on general knowledge of [topic]...")
5. Provide a comprehensive answer that helps the user, even if the exact answer isn't in the document
6. Be educational and practical

Format your answer like this:
[Your comprehensive answer here, mixing document citations and general knowledge]

**From the document:** [What you found in the document with page numbers]
**Additional context:** [General knowledge that helps answer the question fully]

Answer:"""
        
        return prompt
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context from retrieved chunks with page numbers"""
        if not chunks:
            return "No relevant context found in the document."
        
        context_parts = []
        for i, chunk in enumerate(chunks):
            page_num = chunk.get('page_number', 'Unknown')
            context_parts.append(
                f"[Source {i+1} - Page {page_num}]:\n{chunk['text']}\n"
            )
        return "\n".join(context_parts)
    
    def _build_history(self, history: List[Dict]) -> str:
        """Build conversation history"""
        if not history:
            return ""
        
        history_parts = ["Previous Conversation:"]
        for item in history[-3:]:
            if item.get('question'):
                history_parts.append(f"Q: {item['question']}")
            if item.get('answer'):
                history_parts.append(f"A: {item['answer'][:200]}...\n")
        
        return "\n".join(history_parts)
    
    def _create_prompt(self, question: str, context: str, history: str) -> str:
        """Create the full prompt for document-only questions"""
        prompt = f"""You are an intelligent document analysis assistant. Answer the question based on the provided context.

{history}

Context from documents (with page numbers):
{context}

Question: {question}

Instructions:
1. Answer based on the context provided
2. When referencing information, mention which page it comes from
3. If the context doesn't contain enough information, say so clearly but briefly
4. Be precise and factual
5. Keep your answer focused and well-structured

Answer:"""
        
        return prompt
    
    def _generate_suggestions(self, question: str, answer: str, is_general: bool) -> List[str]:
        """Generate contextual follow-up questions"""
        suggestions = []
        
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        if is_general:
            # For general questions, suggest both document-specific and conceptual follow-ups
            suggestions.append("What specific examples are shown in the document?")
            suggestions.append("Are there any related concepts covered?")
        
        # Context-aware suggestions
        if "optimize" in question_lower or "improve" in question_lower:
            suggestions.append("What trade-offs should I consider?")
            suggestions.append("What are the practical applications?")
        elif "what" in question_lower:
            suggestions.append("How is this implemented?")
            suggestions.append("Can you explain this in more detail?")
        elif "how" in question_lower:
            suggestions.append("What are the advantages and disadvantages?")
            suggestions.append("Are there alternative approaches?")
        else:
            suggestions.append("Can you provide more examples?")
            suggestions.append("What are the key takeaways?")
        
        suggestions.append("What else should I know about this topic?")
        
        return suggestions[:3]
    
    def generate_comparison(self, question: str, doc_chunks_map: Dict[str, List[Dict]]) -> str:
        """Generate comparison across multiple documents"""
        try:
            prompt_parts = [
                "Compare the following documents and answer the question:",
                f"\nQuestion: {question}\n"
            ]
            
            for doc_id, chunks in doc_chunks_map.items():
                prompt_parts.append(f"\nDocument {doc_id[:8]}:")
                for chunk in chunks[:3]:
                    page = chunk.get('page_number', 'Unknown')
                    prompt_parts.append(f"- Page {page}: {chunk['text'][:300]}...")
            
            prompt_parts.append("\nProvide a comparative analysis highlighting similarities and differences:")
            
            prompt = "\n".join(prompt_parts)
            response = self.model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            return f"Error generating comparison: {str(e)}"