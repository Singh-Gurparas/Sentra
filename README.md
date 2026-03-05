# Sentra

Sentra is an AI agent observability and security platform. It provides developers with tools to monitor agent execution, detect vulnerabilities, test adversarial robustness, and visualize execution traces in real time.

## System Architecture

1. **Python Instrumentation Library**: Wraps around LangChain/LangGraph agents.
2. **FastAPI Backend**: Processes logs, detects vulnerabilities, handles database storage.
3. **Next.js Dashboard**: Visualizes execution flow, metrics, vulnerabilities, and red-team tests.
4. **SQLite Database**: Lightweight local storage for all execution data.

## Installation

### 1. Backend Setup

Create a virtual environment and install dependencies:
```bash
cd sentra
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install fastapi uvicorn langchain langchain-openai sqlite3 requests pydantic
```

*(Note: Install `langgraph` if you want to trace advanced LangGraph setups, `sqlite3` is built-in to Python).*

### 2. Frontend Setup

Navigate to the frontend folder and install dependencies:
```bash
cd sentra/frontend
npm install
```

## Running the Platform

You need to run the backend and frontend simultaneously.

### Start the Backend API Server
This will automatically initialize the database schema.
```bash
cd sentra/backend
uvicorn api.server:app --reload --port 8000
```

### Start the Frontend Dashboard
```bash
cd sentra/frontend
npm run dev
```

Open your browser to `http://localhost:3000` to view the dashboard.

### Run an Example Agent
Run the example script to simulate agent activity, generate execution traces, and perform red-teaming tests:
```bash
cd sentra/backend
python -m examples.example_agent
```

Check the dashboard to see the traces, red-team results, and agent graph appear live.

## Features

- **Agent Execution Graph**: Visualizes the workflow of the agent using ReactFlow.
- **Trace Logging**: Captures LLM inputs, tool executions, latencies, and token usage.
- **Vulnerability Detection**: Identifies prompt injections, command injections, hardcoded secrets, etc.
- **Adversarial Red-Teaming**: Automatically runs test prompts against the system prompt to check for leakage.
- **Real-Time Dashboard**: See metrics, executions, and security posture instantly.
