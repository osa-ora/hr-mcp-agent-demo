# HR MCP Agent Demo
---

A demonstration project showing how to build an AI-powered HR assistant using a custom MCP (Model Context Protocol) server, an autonomous agent, and a PostgreSQL-backed HR system.

The goal of this project is to illustrate how enterprise business systems can be exposed as AI tools (via a custom MCP server) and consumed by an agent capable of performing HR workflows through natural language interactions.

This demonstrates the concept that:

> **AI is the new UI for applications**

---

## Overview

This demo consists of three main components:

### 1. HR Database

A PostgreSQL database containing HR-related information such as:

* Employee profiles
* Managers and reporting structures
* Employee contacts
* Employment information
* Leave balances
* Leave requests
* Leave types
* Compensation information
* HR policies

---

### 2. Custom MCP Server

A custom MCP server built using FastMCP that exposes HR operations as tools.

Example capabilities include:

* Employee profile lookup
* Detailed employee information retrieval
* Manager lookup
* Leave balance inquiries
* Leave request creation
* Leave request approval and rejection
* Policy search
* Leave type discovery

The MCP server acts as a secure abstraction layer between the agent and the HR system.

---

### 3. HR Agent

A custom AI agent powered by a local LLM through Ollama.

The agent:

* Understands user requests
* Discovers available MCP tools
* Selects the appropriate tool
* Executes multi-step workflows
* Maintains conversational context
* Produces user-friendly responses

Example requests:

* "What is my leave balance for Osama Oransa?"
* "Show my full profile?"
* "ive me the policy that contains info about Hybrid work?"
* "Show all my leave requests."
* "Give me my basic salary and allowance"

---

## Technologies Used

* Python
* FastMCP
* MCP (Model Context Protocol)
* Ollama
* Llama 3.1
* PostgreSQL
* SQLAlchemy
* AsyncIO

---

## Learning Objectives

This project demonstrates:

* Building custom MCP servers
* Tool-based AI agents
* Enterprise system integration
* Multi-step agent workflows
* Database-backed AI applications
* Agent-to-tool orchestration
* Natural language interfaces for business systems

---

## Future Enhancements

Potential extensions include:

* Authentication and authorization
* Role-based access control
* LangGraph orchestration
* Multi-agent workflows
* RAG-enabled HR policy search
* Open WebUI integration
* Kubernetes / OpenShift deployment
* Human approval and notifications workflows
* Audit logging

---

## How to Run the Demo

After cloning the repository, follow these steps:

### 1. Setup environment

```bash
./setup_venv.sh
```

This will create a Python 3.12 virtual environment and install all required dependencies.

---

### 2. Activate environment

```bash
source .venv/bin/activate
```

---

### 3. Create PostgreSQL database

```sql
CREATE DATABASE hrdb;
```

---

### 4. Initialize database schema

```bash
python ./init/init_db.py
```

---

### 5. Seed test data

```bash
python ./init/seed_init_data.py
```

---

### 6. Run MCP server

```bash
python mcp_server.py
```

If successful, you will see:

```
Starting MCP server 'hr-system' with transport 'sse' on http://127.0.0.1:8000/sse
```

---

### MCP Server Screenshot

<img width="1251" height="577" alt="MCP Server Screenshot" src="https://github.com/user-attachments/assets/39420ef3-e76d-4df2-8698-b1bf7814d8a3" />

---

## Run the Local LLM

Install and start Ollama:

```bash
ollama pull llama3.1
ollama serve
```

You can also use other compatible models if needed.

---

## Run the Python Agent

You can test the agent using the provided notebook:

```text
test-agent.ipynb
```

Run all cells and interact with the HR system.
You can customzie the agent configurations as following:


```python
agent = HRAgent(
    AgentConfig(
        debug=False,
        max_steps=9,
        mcp_endpoint="http://127.0.0.1:8000/sse",
        model_name="llama3.1"
    )
)
```

---

## Using a Chat UI (Optional)

You can also integrate the system with a chat interface such as Open WebUI or any MCP-compatible client.

- Add the rquired model: e.g. Ollama
- Add MCP_SERVER and name it as HR MCP_SERVER

<img width="1013" height="748" alt="Screenshot 2026-06-05 at 11 21 45 PM" src="https://github.com/user-attachments/assets/73cc0c46-d293-4f11-a38f-9a6bdf6cfb1c" />
<img width="588" height="598" alt="Screenshot 2026-06-05 at 11 21 53 PM" src="https://github.com/user-attachments/assets/2ce138ac-2d6e-4841-825d-7e7f4b39d88e" />
<img width="608" height="662" alt="Screenshot 2026-06-05 at 11 22 15 PM" src="https://github.com/user-attachments/assets/c4801341-0675-4fb3-b8fb-fe48da36d567" />

This allows a more natural chat-based experience instead of running the Python agent directly.

<img width="1013" height="752" alt="Screenshot 2026-06-05 at 11 26 53 PM" src="https://github.com/user-attachments/assets/55acf1d6-c844-412f-a150-590bb40694a9" />
<img width="1021" height="747" alt="Screenshot 2026-06-05 at 11 28 10 PM" src="https://github.com/user-attachments/assets/e18dd63c-3c90-4cff-8a74-69423b9376ce" />
<img width="1015" height="751" alt="Screenshot 2026-06-05 at 11 31 04 PM" src="https://github.com/user-attachments/assets/6ef78f77-4f49-4178-8a22-1cd51d8d2e09" />
<img width="1015" height="742" alt="Screenshot 2026-06-05 at 11 40 24 PM" src="https://github.com/user-attachments/assets/3417c472-eda4-4bc9-a3b1-403e4d9f2c02" />

---

## Notes

* The MCP server is the core backend of this system.
* The agent is a reference implementation for tool orchestration.
* You can replace the agent layer with LangChain, LangGraph, or any MCP-compatible client.
* The system is designed for experimentation and demos, not production.

---

## License

This project is for educational and demonstration purposes only.


