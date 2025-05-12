from fastapi import WebSocket, WebSocketDisconnect
import logging
import time

logger = logging.getLogger("app")

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Point de terminaison WebSocket sans authentification
    """
    logger.debug(f"WebSocket connection request from client {client_id}")
    
    try:
        # Accepter la connexion directement
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for client {client_id}")
        
        # Envoyer un message de test
        await websocket.send_text("Connexion WebSocket établie avec succès!")
        logger.debug(f"Test message sent to client {client_id}")
        
        # Boucle de réception des messages
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from client {client_id}: {data}")
            
            # Simplement renvoyer le message reçu
            await websocket.send_text(f"Vous avez dit: {data}")
            logger.debug(f"Echo message sent to client {client_id}")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}", exc_info=True)