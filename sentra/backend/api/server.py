from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .database import initialize_database, get_db
import json

app = FastAPI(title="Sentra API")

# Setup CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    initialize_database()

@app.get("/agents")
def get_agents():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agents ORDER BY created_at DESC")
        agents = [dict(row) for row in cursor.fetchall()]
        # parse graph_data so it returns as JSON instead of string
        for agent in agents:
            if agent.get("graph_data"):
                try:
                    agent["graph_data"] = json.loads(agent["graph_data"])
                except Exception:
                    pass
        return agents

@app.get("/agents/{agent_id}/graph")
def get_agent_graph(agent_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT graph_data FROM agents WHERE agent_id = ?", (agent_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        graph = None
        if row["graph_data"]:
            try:
                graph = json.loads(row["graph_data"])
            except Exception:
                pass
                
        # Fallback if graph is missing, empty, or invalid for ReactFlow
        is_invalid = False
        if graph and graph.get("nodes"):
            for node in graph["nodes"]:
                if "data" not in node or "position" not in node:
                    is_invalid = True
                    break
        else:
            is_invalid = True

        if is_invalid:
            graph = {
                "nodes": [
                    {"id": "input", "data": {"label": "User Input"}, "position": {"x": 0, "y": 100}, "type": "default"},
                    {"id": "llm", "data": {"label": "LLM Reasoning"}, "position": {"x": 250, "y": 100}, "type": "default"},
                    {"id": "tool", "data": {"label": "Tool Execution"}, "position": {"x": 500, "y": 100}, "type": "default"},
                    {"id": "response", "data": {"label": "Final Response"}, "position": {"x": 750, "y": 100}, "type": "default"}
                ],
                "edges": [
                    {"id": "e0", "source": "input", "target": "llm", "animated": True},
                    {"id": "e1", "source": "llm", "target": "tool", "animated": True},
                    {"id": "e2", "source": "tool", "target": "response", "animated": True}
                ]
            }
        return graph

@app.get("/traces")
def get_traces():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM execution_traces ORDER BY timestamp DESC LIMIT 100")
        return [dict(row) for row in cursor.fetchall()]

@app.get("/traces/{agent_id}")
def get_agent_traces(agent_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM execution_traces WHERE agent_id = ? ORDER BY timestamp DESC LIMIT 100", (agent_id,))
        return [dict(row) for row in cursor.fetchall()]

@app.get("/redteam")
def get_redteam_tests():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompt_tests ORDER BY created_at DESC LIMIT 100")
        return [dict(row) for row in cursor.fetchall()]

@app.get("/vulnerabilities")
def get_vulnerabilities():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vulnerabilities ORDER BY id DESC LIMIT 100")
        return [dict(row) for row in cursor.fetchall()]

@app.get("/stats")
def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM agents")
        total_agents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM execution_traces")
        total_executions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vulnerabilities")
        total_vulnerabilities = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM prompt_tests")
        total_redteam_tests = cursor.fetchone()[0]
        
        return {
            "total_agents": total_agents,
            "total_executions": total_executions,
            "total_vulnerabilities": total_vulnerabilities,
            "total_redteam_tests": total_redteam_tests
        }
