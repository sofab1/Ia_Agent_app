from fastapi import APIRouter, Depends, Body
from typing import Dict, Any, Optional
from app.services.ai_service import AIService
from app.models.schemas import UserQuery
from datetime import datetime
import logging
from app.core.dependencies import get_current_user

# Configuration du logging
logger = logging.getLogger("app")

router = APIRouter()
ai_service = AIService()

@router.post("/chat")
async def chat_api(
    question: str = Body(...),
    session_id: Optional[str] = Body(None),
    context: Optional[Dict[str, Any]] = Body(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """API de chat pour poser une question à l'IA"""
    try:
        # Préparer les données utilisateur avec UserQuery
        user_query = UserQuery(
            question=question,
            user_id=current_user.get("id", 0),
            name=current_user.get("name", "Anonymous"),
            email=current_user.get("email", "anonymous@example.com"),
            role=current_user.get("role", "guest")
        )
        
        # Traiter la question
        result = await ai_service.process_question(user_query)
        
        # Retourner la réponse comme un dictionnaire
        return {
            "success": True,
            "response": result.get("response", "Désolé, je n'ai pas pu traiter votre demande."),
            "type": result.get("type", "general"),
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id or f"session_{datetime.now().timestamp()}",
            "context": result.get("context", {})
        }
        
    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"An error occurred: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
