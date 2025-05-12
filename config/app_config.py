"""
Configuration de l'application Sofabi IA.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Obtenir le chemin absolu du répertoire racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Chemin vers le fichier .env
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Charger les variables d'environnement depuis le fichier .env
print(f"Tentative de chargement du fichier .env depuis: {ENV_FILE}")
if os.path.exists(ENV_FILE):
    print(f"Fichier .env trouvé à {ENV_FILE}")
    load_dotenv(ENV_FILE)
    print("Variables d'environnement chargées depuis .env")
else:
    print(f"Fichier .env non trouvé à {ENV_FILE}")
    print("Utilisation des valeurs par défaut")

# Ajouter le répertoire racine au PYTHONPATH
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
    print(f"Ajout de {BASE_DIR} au PYTHONPATH")

class Config:
    """Configuration de base"""
    APP_NAME = "Sofabi IA"
    APP_VERSION = "1.0.0"
    DEBUG = False
    
    # Chemins des dossiers
    TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
    STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
    
    # Configuration de l'API
    API_PREFIX = "/api"
    
    # Configuration de la base de données
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "broski")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "your_actual_password")
    
    # Configuration de l'authentification
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "d1c5f0e3a2b7c9d8e6f4a2b0c9d8e6f4a2b0c9d8e6f4a2b0c9d8e6f4a2b0c9d8")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True
    HOST = "127.0.0.1"
    PORT = 8000

class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))

class TestingConfig(Config):
    """Configuration de test"""
    DEBUG = True
    TESTING = True

# Dictionnaire des configurations disponibles
config_by_name = {
    "dev": DevelopmentConfig,
    "prod": ProductionConfig,
    "test": TestingConfig
}

def get_config():
    """Obtenir la configuration active"""
    env = os.getenv("ENVIRONMENT", "dev")
    print(f"Environnement actif: {env}")
    return config_by_name.get(env, DevelopmentConfig)
