import uuid
import requests
import json
import threading
from .callback_handler import SentraCallbackHandler
from .workflow_analyzer import WorkflowAnalyzer
from .redteam_engine import RedTeamEngine
from api.database import get_db, initialize_database

class Sentra:
    def __init__(self, workflow=None, api_url="http://localhost:8000", system_prompt=None):
        self.api_url = api_url
        self.agent_id = str(uuid.uuid4())
        self.workflow = workflow
        self.system_prompt = system_prompt
        
        # Ensure database is initialized with correct schema
        initialize_database()
        
        # 1. Register callback handler (handles 5. logs execution traces)
        self.callback_handler = SentraCallbackHandler(
            api_url=self.api_url, 
            agent_id=self.agent_id
        )
        
        if self.workflow:
            # 2. Register agent metadata
            self._register_agent()
            
            # 3. Analyze workflow graph
            self._analyze_workflow()
            
    def _register_agent(self):
        # Insert agent directly to SQLite to avoid needing API to be running for core tracking
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO agents (agent_id, name, framework, node_count)
                    VALUES (?, ?, ?, ?)
                ''', (
                    self.agent_id, 
                    getattr(self.workflow, "name", "Unnamed Agent"),
                    "LangGraph/LangChain",
                    0
                ))
                conn.commit()
        except Exception as e:
            print(f"Failed to register agent in DB: {e}")

    def _analyze_workflow(self):
        # Extract nodes and edges and update agent
        try:
            analyzer = WorkflowAnalyzer(self.workflow)
            graph_data = analyzer.extract_graph()
            if graph_data:
                node_count = len(graph_data.get("nodes", []))
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE agents 
                        SET graph_data = ?, node_count = ?
                        WHERE agent_id = ?
                    ''', (
                        json.dumps(graph_data),
                        node_count,
                        self.agent_id
                    ))
                    conn.commit()
        except Exception as e:
            print(f"Failed to analyze workflow: {e}")

    def run_redteam(self, llm_callable):
        # 4. Enables red team testing
        try:
            engine = RedTeamEngine(self.agent_id, self.system_prompt)
            results = engine.run_tests(llm_callable)
            return results
        except Exception as e:
            print(f"Failed to run redteam tests: {e}")
            return []

    def monitor(self):
        """
        Attaches callbacks to the workflow if possible.
        For LangGraph/LangChain, this returns the callbacks list to be used in invoke().
        """
        return [self.callback_handler]

    def get_callbacks(self):
        return [self.callback_handler]
