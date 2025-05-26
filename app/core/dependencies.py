from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.services.auth_service import AuthService
from typing import Dict, Any, Optional
import logging

# Configuration du logging
logger = logging.getLogger("app")

# Créer une instance de OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
auth_service = AuthService()

# Fonction pour obtenir l'utilisateur actuel
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Récupère l'utilisateur actuel à partir du token d'authentification"""
    try:
        logger.debug(f"Vérification du token: {token[:10]}...")
        user = auth_service.verify_token(token)
        if not user:
            logger.warning("Token invalide ou utilisateur non trouvé")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug(f"Utilisateur authentifié: {user.get('email')}")
        return user
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Fonction pour obtenir l'utilisateur actuel ou None si non authentifié
async def get_current_user_or_none(request: Request):
    """Récupère l'utilisateur actuel à partir du token d'authentification ou None si non authentifié"""
    # Essayer d'abord de récupérer le token du cookie
    token = request.cookies.get("access_token")
    
    # Si pas de token dans le cookie, essayer le header Authorization
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    if not token:
        logger.debug("Aucun token trouvé, utilisateur non authentifié")
        return None
    
    try:
        user = auth_service.verify_token(token)
        if user:
            logger.debug(f"Utilisateur authentifié: {user.get('email')}")
        return user
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token: {str(e)}", exc_info=True)
        return None

