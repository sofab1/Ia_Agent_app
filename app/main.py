from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.middleware import DebugMiddleware
import logging
import os
from pathlib import Path
from datetime import datetime

# Obtenir le chemin absolu du répertoire racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Importer la configuration
from config.app_config import get_config
config = get_config()

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG if getattr(config, "DEBUG", False) else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# Création de l'application principale
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    debug=getattr(config, "DEBUG", False)
)

# Ajouter le middleware de débogage
app.add_middleware(DebugMiddleware)

# Configurer CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des fichiers statiques et des templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# Importer les routeurs
from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router
from app.api.web_routes import router as web_router

# Inclure les routeurs
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(web_router)

# Gestionnaire d'erreur 404 personnalisé
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    """Gestionnaire d'erreur 404 personnalisé"""
    # Utiliser directement datetime.now().year au lieu de config.CURRENT_YEAR
    return templates.TemplateResponse(
        "404.html", 
        {
            "request": request,
            "current_year": datetime.now().year  # Solution simple et directe
        }, 
        status_code=404
    )

# Redirection racine
@app.get("/")
async def root_redirect():
    """Redirection de la racine vers la page d'accueil"""
    return RedirectResponse(url="/home")

if __name__ == "__main__":
    print("=== DÉMARRAGE DE L'APPLICATION ===")
    print(f"Routes définies : {[route.path for route in app.routes]}")
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host=getattr(config, "HOST", "127.0.0.1"),
        port=getattr(config, "PORT", 8000),
        reload=getattr(config, "DEBUG", False)
    )
