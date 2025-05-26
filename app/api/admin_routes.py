from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any, Optional

from app.services.auth_service import AuthService
from app.services.ai_service import AIService

# Services
auth_service = AuthService()
ai_service = AIService()

# Créer le router
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Fonction utilitaire pour vérifier si l'utilisateur est admin
async def verify_admin(request: Request):
    user = await auth_service.get_current_user_or_none(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        )
    if not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    return user

# Endpoint pour les statistiques du tableau de bord
@router.get("/stats")
async def get_dashboard_stats(user: Dict = Depends(verify_admin)):
    """Récupère les statistiques pour le tableau de bord admin"""
    try:
        # Dans une implémentation réelle, ces données viendraient de la base de données
        # Pour l'instant, nous générons des données fictives
        
        # Statistiques générales
        total_users = random.randint(1000, 1500)
        questions_today = random.randint(70, 100)
        response_rate = random.randint(90, 99)
        error_rate = random.randint(1, 5)
        
        # Données pour les graphiques
        current_date = datetime.now()
        last_30_days = [(current_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        last_30_days.reverse()  # Du plus ancien au plus récent
        
        questions_data = [random.randint(50, 100) for _ in range(30)]
        responses_data = [int(q * random.uniform(0.9, 1.0)) for q in questions_data]
        
        # Catégories de questions
        categories = {
            "Général": random.randint(30, 40),
            "Technique": random.randint(20, 30),
            "Produit": random.randint(15, 25),
            "Support": random.randint(10, 20),
            "Autre": random.randint(5, 10)
        }
        
        # Questions récentes
        recent_questions = [
            {
                "user": f"User{i}",
                "question": f"Question exemple #{i}",
                "status": random.choice(["Répondu", "En attente", "Erreur"]),
                "time": (current_date - timedelta(minutes=random.randint(5, 60))).strftime("%H:%M")
            }
            for i in range(1, 11)
        ]
        
        return {
            "success": True,
            "data": {
                "stats": {
                    "total_users": total_users,
                    "questions_today": questions_today,
                    "response_rate": response_rate,
                    "error_rate": error_rate
                },
                "charts": {
                    "dates": last_30_days,
                    "questions": questions_data,
                    "responses": responses_data,
                    "categories": categories
                },
                "recent_questions": recent_questions
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Une erreur s'est produite: {str(e)}"
            }
        )

# Endpoint pour récupérer la liste des utilisateurs
@router.get("/users")
async def get_users(user: Dict = Depends(verify_admin)):
    """Récupère la liste des utilisateurs pour la section Users"""
    try:
        # Simuler des données utilisateurs
        users = [
            {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "role": random.choice(["admin", "user", "guest"]),
                "status": random.choice(["active", "inactive"]),
                "last_login": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M")
            }
            for i in range(1, 21)
        ]
        
        return {
            "success": True,
            "data": {
                "users": users,
                "total": len(users),
                "active": sum(1 for u in users if u["status"] == "active")
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Une erreur s'est produite: {str(e)}"
            }
        )

# Endpoint pour récupérer les questions
@router.get("/questions")
async def get_questions(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    user: Dict = Depends(verify_admin)
):
    """Récupère la liste des questions pour la section Questions"""
    try:
        # Simuler des données de questions
        statuses = ["answered", "pending", "error"]
        if status and status in statuses:
            filtered_statuses = [status]
        else:
            filtered_statuses = statuses
            
        all_questions = [
            {
                "id": i,
                "user": f"User {random.randint(1, 20)}",
                "question": f"Question exemple #{i}",
                "status": random.choice(filtered_statuses),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M"),
                "response_time": f"{random.randint(100, 2000)}ms"
            }
            for i in range(1, 101)
        ]
        
        # Pagination simple
        start = (page - 1) * limit
        end = start + limit
        paginated_questions = all_questions[start:end]
        
        return {
            "success": True,
            "data": {
                "questions": paginated_questions,
                "total": len(all_questions),
                "page": page,
                "limit": limit,
                "pages": (len(all_questions) + limit - 1) // limit
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Une erreur s'est produite: {str(e)}"
            }
        )

# Ajouter d'autres endpoints pour les sections Responses, Errors, Analytics, Settings