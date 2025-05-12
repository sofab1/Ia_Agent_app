from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Dict, List, Tuple
import logging
import time
from config.websocket_config import websocket_config

# Configuration du logging
logger = logging.getLogger("app")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[Tuple[WebSocket, float]]] = {}
        self.config = websocket_config
        logger.info("WebSocket ConnectionManager initialized with config: %s", self.config)

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        logger.info(f"WebSocket connection attempt from client {client_id}")
        
        # Vérifier si le client a trop de connexions
        if client_id in self.active_connections and \
           len(self.active_connections[client_id]) >= self.config["max_connections_per_client"]:
            logger.warning(f"Client {client_id} has too many connections")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False
        
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for client {client_id}")
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        
        self.active_connections[client_id].append((websocket, time.time()))
        logger.info(f"Client {client_id} added to active connections")
        
        return True

    def disconnect(self, websocket: WebSocket, client_id: str):
        logger.info(f"Disconnecting client {client_id}")
        if client_id in self.active_connections:
            self.active_connections[client_id] = [
                (ws, last_activity) for ws, last_activity in self.active_connections[client_id]
                if ws is not websocket
            ]
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
            logger.info(f"Client {client_id} connection removed")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        logger.info(f"Sending personal message: {message[:30]}...")
        try:
            await websocket.send_text(message)
            # Mettre à jour l'heure de la dernière activité
            for client_id, connections in self.active_connections.items():
                for i, (ws, _) in enumerate(connections):
                    if ws is websocket:
                        self.active_connections[client_id][i] = (ws, time.time())
                        return
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)

    async def broadcast(self, message: str, client_id: str = None):
        logger.info(f"Broadcasting message to {'all clients' if client_id is None else f'client {client_id}'}")
        targets = self.active_connections.get(client_id, []) if client_id else [
            ws for conns in self.active_connections.values() for ws in conns
        ]
        for ws, _ in targets:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {str(e)}", exc_info=True)

    async def cleanup_inactive_connections(self):
        current_time = time.time()
        inactive_timeout = self.config["inactivity_timeout"]
        
        for client_id in list(self.active_connections.keys()):
            active = []
            for ws, last_activity in self.active_connections[client_id]:
                if current_time - last_activity < inactive_timeout:
                    active.append((ws, last_activity))
                else:
                    logger.info(f"Closing inactive connection for client {client_id}")
                    try:
                        await ws.close(code=status.WS_1000_NORMAL_CLOSURE)
                    except Exception as e:
                        logger.error(f"Error closing inactive connection: {str(e)}", exc_info=True)
            if active:
                self.active_connections[client_id] = active
            else:
                del self.active_connections[client_id]
