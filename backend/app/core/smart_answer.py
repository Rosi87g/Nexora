# app/smart_answer.py - PROFESSIONAL AI 1.0 (Enhanced for various tasks)
from app.data_processing.learning_system import learning_system
from app.core.answer_refiner import refine_answer

class AI1SmartAnswer:
    def __init__(self):
        self.detail_levels = {
            "short": "short",
            "medium": "medium", 
            "detailed": "detailed",
            "10marks": "10marks"
        }
    
    def detect_detail_level(self, question: str) -> str:
        """Smart detail level detection"""
        question_lower = question.lower()
        
        # Exam patterns (highest priority)
        if "10 marks" in question_lower or "10marks" in question_lower:
            return "10marks"
        if any(word in question_lower for word in ["exam", "test", "marks", "20 marks", "answer in detail"]):
            return "detailed"
        
        # Quick patterns
        if any(word in question_lower for word in ["quick", "brief", "short", "fast", "simple"]):
            return "short"
        
        return "medium"
    
    def generate_response(self, user_id: str, question: str) -> str:
        # 1. Check internal knowledge FIRST (instant)
        internal_results = learning_system.search_internal_knowledge(question, top_k=3)
        
        if internal_results:
            best_match = internal_results[0]
            return f"🧠 **From Memory**\n\n{best_match['answer']}"
        
        # 2. Original pipeline with PROFESSIONAL refinement
        try:
            from app.core.chat_logic import generate_chat_response_original
            raw_response = generate_chat_response_original(question)
            
            # Apply professional structure
            detail_level = self.detect_detail_level(question)
            professional_response = raw_response.strip()
            
            # Learn this interaction
            learning_system.learn_from_interaction(user_id, question, professional_response)
            
            return professional_response
            
        except Exception as e:
            return f"💡 **{question}**\n\nI found information but need more context. Try: 'Explain {question} in detail'"

# Global instance
smart_answer = AI1SmartAnswer()