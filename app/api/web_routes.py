from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any
from app.services.auth_service import AuthService
from app.services.ai_service import AIService
from datetime import timedelta, datetime
import logging
from config.app_config import get_config
from app.models.schemas import UserCreate, UserQuery, ApiResponse
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from app.core.dependencies   import get_current_user
from app.core.dependencies import get_current_user_or_none  # Importer depuis dependencies.py

# Configuration
config = get_config()
logger = logging.getLogger("app")

# Templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Services
auth_service = AuthService()
ai_service = AIService()

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Créer le router
router = APIRouter()

# Page d'accueil
@router.get("/")
@router.get("/home")
async def home(request: Request):
    """Page d'accueil de l'application"""
    user = await get_current_user_or_none(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if user.get("is_admin", False):
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    
    return RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)

# Route pour la page de chat
@router.get("/chat")
async def chat_page(request: Request):
    """Page de chat pour les utilisateurs authentifiés"""
    user = await get_current_user_or_none(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "chat.html", 
        {
            "request": request, 
            "user": user,
            "current_year": datetime.now().year,
            "chat_history": []
        }
    )

# Route POST pour le chat
@router.post("/chat")
async def chat_post(
    request: Request,
    question: str = Form(...)
):
    """Traitement du formulaire de chat pour les utilisateurs authentifiés"""
    user = await get_current_user_or_none(request)
    
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )
    
    try:
        user_query = UserQuery(
            question=question,
            user_id=user.get("id", 0),
            name=user.get("name", ""),
            email=user.get("email", ""),
            role=user.get("role", "")
        )
        
        result = await ai_service.process_question(user_query)
        
        # Retourner la réponse comme JSON
        return JSONResponse(content={
            "success": True,
            "response": result.get("response", "Désolé, je n'ai pas pu traiter votre demande."),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in chat POST: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Une erreur s'est produite: {str(e)}"
            }
        )

# Route pour la page d'administration
@router.get("/admin")
async def admin_page(request: Request):
    """Page d'administration pour les admins"""
    user = await get_current_user_or_none(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
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
    user = await get_current_user_or_none(request)
    if user:
        if user.get("is_admin", False):
            return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
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
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,
            expires=1800,
            path="/",
        )
        
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
    user = await get_current_user_or_none(request)
    if user:
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
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    """Traitement du formulaire d'inscription"""
    try:
        existing_user = auth_service.get_user_by_email(email)
        if existing_user:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "current_year": datetime.now().year,
                    "error": "Cet email est déjà utilisé"
                },
                status_code=400
            )
        
        success = auth_service.create_user(
            name=name,
            email=email,
            role=role,
            password=password,
            is_admin=False
        )
        
        if not success:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "current_year": datetime.now().year,
                    "error": "Erreur lors de la création du compte"
                },
                status_code=500
            )
        
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "current_year": datetime.now().year,
                "success": "Compte créé avec succès. Vous pouvez maintenant vous connecter."
            }
        )
        
    except Exception as e:
        logger.error(f"Error in register POST: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "current_year": datetime.now().year,
                "error": f"Une erreur s'est produite: {str(e)}"
            },
            status_code=500
        )

# Route pour la déconnexion
@router.get("/logout")
async def logout(response: Response):
    """Déconnexion de l'utilisateur"""
    response.delete_cookie(key="access_token", path="/")
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)










