import uuid
import time
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from api.database import get_db
from .vulnerability_detector import VulnerabilityDetector

def log_execution_trace(trace_data: dict):
    """
    Helper function to log execution traces to SQLite database.
    Required fields in trace_data (some can be None):
    id, timestamp, node_name, event_type, prompt, response, tool_name, latency, token_usage, error
    Note: agent_id is also added properly.
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO execution_traces 
                (id, agent_id, node_name, event_type, prompt, response, tool_name, latency, token_usage, error)
                VALUES (:id, :agent_id, :node_name, :event_type, :prompt, :response, :tool_name, :latency, :token_usage, :error)
            ''', trace_data)
            conn.commit()
            conn.commit()
            
        # Detect and log vulnerabilities automatically
        log_vulnerabilities(trace_data["id"], trace_data.get("prompt"))
        log_vulnerabilities(trace_data["id"], trace_data.get("response"))
        
    except Exception as e:
        print(f"Error logging trace: {e}")

def log_vulnerabilities(trace_id: str, text: Optional[str]):
    if not text:
        return
    vulns = VulnerabilityDetector.analyze(text)
    for v in vulns:
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO vulnerabilities 
                    (id, trace_id, vulnerability_type, severity, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (str(uuid.uuid4()), trace_id, v["vulnerability_type"], v["severity"], v["description"]))
                conn.commit()
        except Exception as e:
            print(f"Error logging vulnerability: {e}")

class SentraCallbackHandler(BaseCallbackHandler):
    """
    LangChain Callback Handler for capturing execution traces
    and storing them into the Sentra database.
    """
    
    def __init__(self, agent_id: str, api_url: str = None):
        super().__init__()
        self.agent_id = agent_id
        self.api_url = api_url
        self.runs = {}  # Store start times by run_id
        
    def _create_base_trace(self, event_type: str, run_id: str) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "agent_id": self.agent_id,
            "node_name": None,
            "event_type": event_type,
            "prompt": None,
            "response": None,
            "tool_name": None,
            "latency": 0.0,
            "token_usage": 0,
            "error": None,
            "timestamp": time.time()
        }

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        run_id = str(kwargs.get("run_id")) if kwargs else "unknown"
        self.runs[run_id] = time.time()
        
        trace = self._create_base_trace("on_chain_start", run_id)
        trace["node_name"] = serialized.get("name", "chain") if serialized else "chain"
        trace["prompt"] = str(inputs)
        
        log_execution_trace(trace)

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        run_id = str(kwargs.get("run_id")) if kwargs else "unknown"
        start_time = self.runs.pop(run_id, time.time())
        latency = time.time() - start_time
        
        trace = self._create_base_trace("on_chain_end", run_id)
        trace["response"] = str(outputs)
        trace["latency"] = latency
        
        log_execution_trace(trace)

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> Any:
        run_id = str(kwargs.get("run_id")) if kwargs else "unknown"
        start_time = self.runs.pop(run_id, time.time())
        latency = time.time() - start_time
        
        trace = self._create_base_trace("on_chain_error", run_id)
        trace["error"] = str(error)
        trace["latency"] = latency
        
        log_execution_trace(trace)

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        run_id = str(kwargs.get("run_id")) if kwargs else "unknown"
        self.runs[run_id] = time.time()
        
        trace = self._create_base_trace("on_llm_start", run_id)
        trace["node_name"] = serialized.get("name", "llm") if serialized else "llm"
        trace["prompt"] = "\\n".join(prompts)
        
        log_execution_trace(trace)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        run_id = str(kwargs.get("run_id")) if kwargs else "unknown"
        start_time = self.runs.pop(run_id, time.time())
        latency = time.time() - start_time
        
        outputs = []
        for gen in response.generations:
            for g in gen:
                outputs.append(g.text)
                
        token_usage = 0
        if response.llm_output and "token_usage" in response.llm_output:
            token_usage = response.llm_output["token_usage"].get("total_tokens", 0)
            
        trace = self._create_base_trace("on_llm_end", run_id)
        trace["response"] = "\\n".join(outputs)
        trace["latency"] = latency
        trace["token_usage"] = token_usage
        
        log_execution_trace(trace)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        run_id = str(kwargs.get("run_id")) if kwargs else "unknown"
        self.runs[run_id] = time.time()
        
        trace = self._create_base_trace("on_tool_start", run_id)
        trace["node_name"] = serialized.get("name", "tool") if serialized else "tool"
        trace["tool_name"] = serialized.get("name", "tool") if serialized else "tool"
        trace["prompt"] = input_str
        
        log_execution_trace(trace)

    def on_tool_end(self, output: Any, **kwargs: Any) -> Any:
        run_id = str(kwargs.get("run_id")) if kwargs else "unknown"
        start_time = self.runs.pop(run_id, time.time())
        latency = time.time() - start_time
        
        trace = self._create_base_trace("on_tool_end", run_id)
        trace["response"] = str(output)
        trace["latency"] = latency
        
        log_execution_trace(trace)
