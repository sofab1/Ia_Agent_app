from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from app.services.auth_service import AuthService
from app.models.schemas import UserCreate, Token, UserResponse, ApiResponse
from datetime import timedelta
import logging
from typing import Dict, Any, Optional

# Configuration du logging
logger = logging.getLogger("app")

router = APIRouter()
auth_service = AuthService()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Obtenir un token d'accès JWT (OAuth2 standard)"""
    logger.debug(f"Tentative de connexion avec username: {form_data.username}")
    
    # Authentifier l'utilisateur
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Échec d'authentification pour {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer le token
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": user["email"], "role": user["role"], "is_admin": user["is_admin"]},
        expires_delta=access_token_expires
    )
    
    logger.debug(f"Token créé avec succès pour {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login")
async def login_api(
    email: str = Body(...),
    password: str = Body(...)
):
    """Authentifier un utilisateur et créer un token d'accès (API)"""
    user = auth_service.authenticate_user(email, password)
    if not user:
        return {
            "success": False,
            "error": "Incorrect email or password"
        }
    
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": user["email"], "role": user["role"], "is_admin": user["is_admin"]},
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "is_admin": user["is_admin"]
            }
        }
    }

@router.post("/register")
async def register_user_api(user: UserCreate):
    """Créer un nouveau compte utilisateur (API)"""
    # Check if user already exists
    existing_user = auth_service.db.get_user_by_email(user.email)
    if existing_user:
        return {
            "success": False,
            "error": "Email already registered"
        }
    
    # Create new user
    success = auth_service.create_user(
        name=user.name,
        email=user.email,
        role=user.role,
        password=user.password,
        is_admin=False  # Regular users can't register as admins
    )
    
    if not success:
        return {
            "success": False,
            "error": "Failed to create user"
        }
    
    return {
        "success": True,
        "message": "User registered successfully",
        "data": {
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_admin": False
        }
    }

@router.get("/logout")
async def auth_logout(response: Response):
    """Route unique pour la déconnexion"""
    # Supprimer le cookie avec les mêmes paramètres que lors de sa création
    response.delete_cookie(
        key="access_token", 
        path="/",
        httponly=True
    )
    # Rediriger vers la page de login
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

















