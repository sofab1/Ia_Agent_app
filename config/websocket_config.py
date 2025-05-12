"""
Configuration des WebSockets pour l'application Sofabi IA.
"""

# Configuration de base des WebSockets
websocket_config = {
    # Taille maximale des messages WebSocket (en octets)
    "max_size": 16 * 1024 * 1024,  # 16 MB
    
    # Intervalle de ping (en secondes)
    "ping_interval": 20.0,
    
    # Délai d'attente du ping (en secondes)
    "ping_timeout": 20.0,
    
    # Activer la compression des messages
    "per_message_deflate": True,
    
    # Nombre maximum de connexions par client
    "max_connections_per_client": 5,
    
    # Délai d'inactivité avant fermeture (en secondes)
    "inactivity_timeout": 300,  # 5 minutes
    
    # Désactiver l'authentification pour les WebSockets
    "require_authentication": False,
}

