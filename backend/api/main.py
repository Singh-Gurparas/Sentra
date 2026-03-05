from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import List
from .database import initialize_database, get_db

app = FastAPI(title="Sentra API")

# Setup CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    initialize_database()

# --- WebSocket Manager for Real-time Logs ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # We will dispatch messages to all connected clients
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass  # Ignore disconnects during broadcast

manager = ConnectionManager()

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Just keep the connection open, we don't expect messages from client
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Rest of the routes will be imported and included
from .routes import logs, agent_code, vulnerabilities
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(agent_code.router, prefix="/api/agents", tags=["Agents"])
app.include_router(vulnerabilities.router, prefix="/api/vulnerabilities", tags=["Vulnerabilities"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
