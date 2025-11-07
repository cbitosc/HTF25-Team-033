import google.generativeai as genai
from typing import List, Dict
import os
import time
import re
from app.services.citation_engine import CitationEngine

class QAEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            api_key = "AIzaSyCJpRGChWlmchjCx4dLjY_xe5F8kSvds9M"
        
        genai.configure(api_key=api_key)
        
        self.generation_config = {
            'temperature': 0.7,
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
            context = self._build_context(context_chunks)
            history_text = self._build_history(conversation_history)
            is_general_question = self._is_general_knowledge_question(question, context_chunks)
            
            if is_general_question:
                prompt = self._create_hybrid_prompt(question, context, history_text)
            else:
                prompt = self._create_prompt(question, context, history_text)
            
            print(f"\n=== Generating answer for: {question} ===")
            print(f"Question type: {'Hybrid' if is_general_question else 'Document-only'}")
            print(f"Using {len(context_chunks)} chunks from pages: {[c.get('page_number') for c in context_chunks]}")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    answer_text = response.text
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(1)
            
            citations = self.citation_engine.create_citations(context_chunks, answer_text)
            citation_report = self.citation_engine.verify_citation_accuracy(answer_text, citations)
            
            print(f"Citation quality: {citation_report['citation_quality']}")
            print(f"Pages cited: {citation_report['pages_cited']}")
            
            suggested_questions = self._generate_suggestions(question, answer_text, is_general_question)
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
            import traceback
            traceback.print_exc()
            
            processing_time = time.time() - start_time
            
            return {
                "answer": f"I encountered an error processing your question: {str(e)}. Please try rephrasing.",
                "citations": [],
                "confidence_score": 0.0,
                "suggested_questions": [
                    "Can you rephrase your question?",
                    "What specific aspect would you like to know about?"
                ],
                "processing_time": round(processing_time, 2),
                "answer_type": "error"
            }
    
    def _is_general_knowledge_question(self, question: str, context_chunks: List[Dict]) -> bool:
        """Determine if question needs general knowledge"""
        question_lower = question.lower()
        
        general_keywords = [
            'how to', 'how can', 'how do', 'ways to', 'methods to', 'techniques to',
            'improve', 'optimize', 'better', 'efficient', 'best practice', 'best way',
            'explain', 'what is', 'what are', 'define', 'describe', 'tell me about',
            'compare', 'difference between', 'vs', 'versus', 'contrast',
            'advantages', 'disadvantages', 'pros', 'cons', 'benefits', 'drawbacks',
            'alternative', 'option', 'approach', 'strategy', 'solution'
        ]
        
        is_general = any(keyword in question_lower for keyword in general_keywords)
        
        if context_chunks:
            avg_confidence = sum(c.get('confidence', 0) for c in context_chunks) / len(context_chunks)
            if avg_confidence < 0.5:
                is_general = True
        
        return is_general
    
    def _create_hybrid_prompt(self, question: str, context: str, history: str) -> str:
        """Create prompt combining document and general knowledge"""
        prompt = f"""You are an expert AI assistant specializing in computer science, algorithms, and technical documentation.

{history}

**Document Context (with page numbers):**
{context}

**User Question:** {question}

**Instructions:**
Provide a comprehensive, well-structured answer combining document information with general expertise.

**Format Guidelines:**
1. Use ## for main headings, ### for subheadings
2. Use **bold** for key terms, `code` for technical terms
3. Use bullet points (-) and numbered lists (1., 2., 3.)
4. Start with brief 2-3 sentence overview
5. Break into logical sections
6. Cite pages: "According to page X..." for document info
7. Mark general knowledge: "Based on standard practices..."
8. Include code examples in code blocks if relevant
9. End with Key Takeaways section
10. Aim for 300-500 words

**Structure Example:**

## Overview
[Brief summary]

## [Main Section]
[Detailed explanation with formatting]

### [Subsection]
[Specific details]

**From the Document:**
- **Page X**: [Finding]

**Additional Context:**
[General knowledge]

## Key Takeaways
- [Point 1]
- [Point 2]

Now answer the question:"""
        
        return prompt
    
    def _create_prompt(self, question: str, context: str, history: str) -> str:
        """Create prompt for document-only questions"""
        prompt = f"""You are an intelligent document analysis assistant.

{history}

**Context from documents (with page numbers):**
{context}

**Question:** {question}

**Instructions:**
1. Use markdown: ## headings, ### subheadings, **bold**, `code`, bullets, lists
2. Start with brief overview (2-3 sentences)
3. Organize into clear sections
4. Always cite page numbers: "According to page X..."
5. Keep paragraphs short (3-4 sentences)
6. Aim for 200-400 words
7. If limited info, state what IS in document, mention what isn't

**Example format:**

## Overview
[Summary]

## [Main Topic]
Page X shows...

## Summary
- [Key point 1]
- [Key point 2]

Answer:"""
        
        return prompt
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context from chunks"""
        if not chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(chunks):
            page_num = chunk.get('page_number', 'Unknown')
            text = chunk['text'][:800] + "..." if len(chunk['text']) > 800 else chunk['text']
            context_parts.append(f"[Source {i+1} - Page {page_num}]:\n{text}\n")
        return "\n".join(context_parts)
    
    def _build_history(self, history: List[Dict]) -> str:
        """Build conversation history"""
        if not history:
            return ""
        
        history_parts = ["**Previous Conversation:**"]
        for item in history[-3:]:
            if item.get('question'):
                history_parts.append(f"Q: {item['question']}")
            if item.get('answer'):
                answer = item['answer'][:300] + "..." if len(item['answer']) > 300 else item['answer']
                history_parts.append(f"A: {answer}\n")
        
        return "\n".join(history_parts)
    
    def _generate_suggestions(self, question: str, answer: str, is_general: bool) -> List[str]:
        """Generate follow-up questions"""
        suggestions = []
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        if is_general:
            suggestions.append("What specific examples are in the document?")
            suggestions.append("Are there related concepts covered?")
        
        if "optimize" in question_lower or "improve" in question_lower:
            suggestions.append("What trade-offs should I consider?")
            suggestions.append("What are practical implications?")
        elif "what" in question_lower:
            suggestions.append("How is this implemented?")
            suggestions.append("Can you explain in more detail?")
        elif "how" in question_lower:
            suggestions.append("What are advantages and disadvantages?")
            suggestions.append("Are there alternatives?")
        elif "why" in question_lower:
            suggestions.append("What are the implications?")
            suggestions.append("How does this compare?")
        else:
            suggestions.append("Can you provide examples?")
            suggestions.append("What are key takeaways?")
        
        suggestions.append("What other related topics are covered?")
        
        if "algorithm" in answer_lower:
            suggestions.insert(0, "What's the time complexity?")
        elif "data structure" in answer_lower:
            suggestions.insert(0, "What are the use cases?")
        
        return suggestions[:3]
    
    def generate_comparison(self, question: str, doc_chunks_map: Dict[str, List[Dict]]) -> str:
        """Generate comparison across documents"""
        try:
            prompt_parts = [
                "Compare multiple documents. Provide comprehensive comparative analysis.\n",
                f"**Question:** {question}\n"
            ]
            
            for doc_id, chunks in doc_chunks_map.items():
                prompt_parts.append(f"\n**Document {doc_id[:8]}:**")
                for chunk in chunks[:3]:
                    page = chunk.get('page_number', 'Unknown')
                    text = chunk['text'][:400] + "..." if len(chunk['text']) > 400 else chunk['text']
                    prompt_parts.append(f"- Page {page}: {text}")
            
            prompt_parts.append("\n**Instructions:**")
            prompt_parts.append("1. Use markdown: ## headings, bullets")
            prompt_parts.append("2. Sections: Similarities, Differences, Analysis")
            prompt_parts.append("3. Cite page numbers")
            prompt_parts.append("\n**Analysis:**")
            
            prompt = "\n".join(prompt_parts)
            response = self.model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            print(f"Comparison error: {e}")
            return f"## Error\n\nComparison failed: {str(e)}"