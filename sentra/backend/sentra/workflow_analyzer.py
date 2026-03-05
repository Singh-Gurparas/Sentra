class WorkflowAnalyzer:
    """
    Extracts nodes and edges from a LangChain or LangGraph workflow
    to generate a graph structure for the frontend ReactFlow visualization.
    """
    def __init__(self, workflow):
        self.workflow = workflow

    def extract_graph(self) -> dict:
        """
        Returns graph data in format:
        { nodes: [{ id, data: { label }, position: { x, y } }], edges: [{ id, source, target }] }
        """
        nodes_raw = []
        edges_raw = []
        
        # Simple extraction logic based on hasattr for demonstration
        if hasattr(self.workflow, "nodes") and hasattr(self.workflow, "edges"):
            # LangGraph style graph
            for node_name in self.workflow.nodes.keys():
                nodes_raw.append({
                    "id": node_name,
                    "label": node_name
                })
            
            for edge in self.workflow.edges:
                source = getattr(edge, "source", None) or (edge[0] if isinstance(edge, tuple) else None)
                target = getattr(edge, "target", None) or (edge[1] if isinstance(edge, tuple) else None)
                if source and target:
                    edges_raw.append({
                        "source": source,
                        "target": target
                    })
                    
        elif hasattr(self.workflow, "steps"):
            # LangChain SequentialChain style
            for i, step in enumerate(self.workflow.steps):
                step_name = getattr(step, "name", f"step_{i}")
                nodes_raw.append({
                    "id": step_name,
                    "label": step_name
                })
                if i > 0:
                    prev_name = getattr(self.workflow.steps[i-1], "name", f"step_{i-1}")
                    edges_raw.append({
                        "source": prev_name,
                        "target": step_name
                    })
        
        # If no nodes extracted, use a fallback workflow
        if not nodes_raw:
            nodes_raw = [
                {"id": "input", "label": "User Input"},
                {"id": "llm", "label": "LLM Reasoning"},
                {"id": "tool", "label": "Tool Execution"},
                {"id": "response", "label": "Final Response"}
            ]
            edges_raw = [
                {"source": "input", "target": "llm"},
                {"source": "llm", "target": "tool"},
                {"source": "tool", "target": "response"}
            ]

        # Convert to ReactFlow format with layout
        nodes = []
        for i, n in enumerate(nodes_raw):
            nodes.append({
                "id": n["id"],
                "data": {"label": n["label"]},
                "position": {"x": i * 250, "y": 100},
                "type": "default"
            })

        edges = []
        for i, e in enumerate(edges_raw):
            edges.append({
                "id": f"e{i}",
                "source": e["source"],
                "target": e["target"],
                "animated": True
            })
            
        return {
            "nodes": nodes,
            "edges": edges
        }
