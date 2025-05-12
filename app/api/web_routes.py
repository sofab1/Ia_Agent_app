from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any
from app.services.auth_service import AuthService
from app.services.ai_service import AIService
from datetime import timedelta, datetime
import logging
from config.app_config import get_config
from app.models.schemas import UserCreate, UserQuery, ApiResponse
from pydantic import BaseModel

# Configuration
config = get_config()
logger = logging.getLogger("app")

# Templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

router = APIRouter()
auth_service = AuthService()
ai_service = AIService()

# Fonction pour obtenir l'utilisateur actuel
async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Récupère l'utilisateur actuel à partir du token d'authentification"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        user = auth_service.verify_token(token)
        if not user:
            return None
        return user
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}", exc_info=True)
        return None

# Routes de redirection pour la compatibilité
@router.get("/logout")
async def redirect_logout():
    """Redirection pour les liens de déconnexion"""
    return RedirectResponse(url="/auth/logout", status_code=status.HTTP_302_FOUND)

@router.get("/user/logout")
async def redirect_user_logout():
    """Redirection pour les anciens liens de déconnexion"""
    return RedirectResponse(url="/auth/logout", status_code=status.HTTP_302_FOUND)

@router.get("/user/chat")
async def redirect_user_chat():
    """Redirection pour les anciens liens de chat"""
    return RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)

@router.get("/admin/dashboard")
async def redirect_admin_dashboard():
    """Redirection pour les liens de dashboard admin"""
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

# Page d'accueil
@router.get("/home")
async def home(request: Request, user=Depends(get_current_user)):
    """Page d'accueil de l'application"""
    # Si l'utilisateur n'est pas connecté, rediriger vers la page de login
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Si l'utilisateur est connecté et est admin, afficher le dashboard
    if user.get("is_admin", False):
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    
    # Si l'utilisateur est connecté mais n'est pas admin, rediriger vers le chat
    return RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)

# Route pour la page de chat
@router.get("/chat")
async def chat_page(request: Request, user=Depends(get_current_user)):
    """Page de chat pour les utilisateurs"""
    # Si l'utilisateur n'est pas connecté, rediriger vers la page de login
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "chat.html", 
        {
            "request": request, 
            "user": user,
            "current_year": datetime.now().year,
            "chat_history": []  # Historique vide ou à remplir depuis la base de données
        }
    )

# Route POST pour le chat
@router.post("/chat")
async def chat_post(
    request: Request,
    question: str = Form(...),
    user=Depends(get_current_user)
):
    """Traitement du formulaire de chat"""
    if not user:
        return RedirectResponse(url="/login")
    
    try:
        # Créer un objet UserQuery
        user_query = UserQuery(
            question=question,
            user_id=user.get("id", 0),
            name=user.get("name", "Anonymous"),
            email=user.get("email", "anonymous@example.com"),
            role=user.get("role", "guest")
        )
        
        # Traiter la question avec l'objet UserQuery
        result = await ai_service.process_question(user_query)
        
        return templates.TemplateResponse(
            "chat.html", 
            {
                "request": request, 
                "user": user,
                "current_year": datetime.now().year,
                "response": result.get("response", "Désolé, je n'ai pas pu traiter votre demande."),
                "chat_history": []
            }
        )
    except Exception as e:
        logger.error(f"Error in chat POST: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "chat.html", 
            {
                "request": request, 
                "user": user,
                "current_year": datetime.now().year,
                "error": f"Une erreur s'est produite: {str(e)}",
                "chat_history": []
            }
        )

# Route pour la page d'administration
@router.get("/admin")
async def admin_page(request: Request, user=Depends(get_current_user)):
    """Page d'administration pour les admins"""
    # Si l'utilisateur n'est pas connecté, rediriger vers la page de login
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Si l'utilisateur n'est pas admin, rediriger vers la page de chat
    if not user.get("is_admin", False):
        return RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "user": user,
            "current_year": datetime.now().year
        }
    )

# Route pour la page de login
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Page de connexion"""
    # Vérifier si l'utilisateur est déjà connecté
    user = await get_current_user(request)
    if user:
        # Si l'utilisateur est admin, rediriger vers la page d'accueil
        if user.get("is_admin", False):
            return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
        # Sinon, rediriger vers la page de chat
        return RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

# Route POST pour le login
@router.post("/login")
async def login_form(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...)
):
    """Traitement du formulaire de connexion"""
    try:
        user = auth_service.authenticate_user(email, password)
        if not user:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "current_year": datetime.now().year,
                    "error": "Email ou mot de passe incorrect"
                },
                status_code=401
            )
        
        access_token_expires = timedelta(minutes=30)
        access_token = auth_service.create_access_token(
            data={"sub": user["email"], "role": user["role"], "is_admin": user["is_admin"]},
            expires_delta=access_token_expires
        )
        
        # Set cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,
            expires=1800,
            path="/",  # Important: cookie disponible sur tout le site
        )
        
        # Retourner une réponse JSON pour le client JavaScript
        return {
            "success": True,
            "is_admin": user.get("is_admin", False),
            "name": user.get("name", ""),
            "email": user.get("email", "")
        }
        
    except Exception as e:
        logger.error(f"Error in login POST: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "current_year": datetime.now().year,
                "error": f"Une erreur s'est produite: {str(e)}"
            },
            status_code=500
        )

# Route pour la page d'inscription
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Page d'inscription"""
    # Vérifier si l'utilisateur est déjà connecté
    user = await get_current_user(request)
    if user:
        # Si l'utilisateur est connecté, rediriger vers la page appropriée
        if user.get("is_admin", False):
            return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "register.html", 
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

# Route POST pour l'inscription
@router.post("/register")
async def register_user_form(
    request: Request,
    user: dict
):
    """Traitement du formulaire d'inscription"""
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = auth_service.db.get_user_by_email(user.email)
        if existing_user:
            return {
                "success": False,
                "detail": "Cet email est déjà utilisé"
            }
        
        # Créer le nouvel utilisateur
        success = auth_service.create_user(
            name=user.name,
            email=user.email,
            role=user.role,
            password=user.password,
            is_admin=False  # Les utilisateurs normaux ne peuvent pas être admin
        )
        
        if not success:
            return {
                "success": False,
                "detail": "Erreur lors de la création du compte"
            }
        
        # Retourner une réponse JSON pour le client JavaScript
        return {
            "success": True,
            "detail": "Compte créé avec succès"
        }
        
    except Exception as e:
        logger.error(f"Error in register POST: {str(e)}", exc_info=True)
        return {
            "success": False,
            "detail": f"Une erreur s'est produite: {str(e)}"
        }












