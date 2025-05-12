import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

logger = logging.getLogger("app")

class DebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        request_type = request.scope["type"]

        # Log détaillé pour les requêtes WebSocket
        if request_type == "websocket":
            logger.debug(f"WebSocket request to {path}")
            logger.debug(f"WebSocket headers: {dict(request.headers)}")
            logger.debug(f"WebSocket scope: {request.scope}")
            
            # Pour les WebSockets, nous devons simplement passer la requête
            # sans interférer avec le protocole de mise à niveau
            return await call_next(request)

        # Traitement normal pour les requêtes HTTP
        logger.debug(f"Request: {method} {path} (Type: {request_type})")
        
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            status_code = getattr(response, "status_code", "N/A")
            logger.debug(f"Response: {status_code} (Time: {process_time:.3f}s)")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Error during request processing: {str(e)} (Time: {process_time:.3f}s)")
            raise

