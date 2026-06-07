# HR MCP Agent Demo
---

A demonstration project showing how to build an AI-powered HR assistant using a custom MCP (Model Context Protocol) server, an autonomous agent, and a PostgreSQL-backed HR system.

The goal of this project is to illustrate how enterprise business systems can be exposed as AI tools (via a custom MCP server) and consumed by an agent capable of performing HR workflows through natural language interactions.

This demostrates the concept that:

> **AI is the new UI for applications**

---

## Overview

This demo consists of five main components:

<img width="1536" height="1024" alt="ChatGPT Image Jun 6, 2026, 09_47_05 AM" src="https://github.com/user-attachments/assets/309d75fd-6b32-4554-8fae-68857a7204f9" />


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

You can see tables like employees:
```
employees = Table(
    "employees",
    metadata,
    # Business identity (PRIMARY KEY NOW)
    Column("employee_code", String(50), primary_key=True),
    Column("full_name", String(200), nullable=False),
    Column("sex", String(20)),
    Column("birthdate", Date),
    Column("marital_status", String(50)),
    Column("nationality", String(100)),
    # Business relationship (no FK constraint by design)
    Column("manager_code", String(50), nullable=True),
    Column("created_at", DateTime),
    Column("updated_at", DateTime)
)
```

### 2. Database Service Layer

This layer exposes the database functionality in the file db_service.py.
It exposes the needed CRUD operations  for all tables transactions and enforce some rules as well:

```
def get_employee_profile(employee_code: str):
    with engine.begin() as conn:
        emp = _get_employee(conn, employee_code)
        return dict(emp) if emp else None

```

The database is configured in the file db.py and it inherit the value from config file which get these values from .env file.
You can update that file .env it to point to your database:

```
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL or "postgresql+psycopg2://postgres:postgres@localhost:5432/hrdb",
    echo=False
)
```
---

### 3. Custom HR MCP Server

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

You can see function like:
```
import db_service as db

# =========================================================
# EMPLOYEE PROFILE (ROLE: ANY EMPLOYEE)
# =========================================================
@mcp.tool(
    description="""
ROLE: ANY EMPLOYEE

Get basic employee profile using employee_code
"""
)
def get_employee_profile(employee_code: str):
    return db.get_employee_profile(employee_code)
```
That's very simple and easy way to build pluggable integration layer for AI that exposes your internal system functionality.
Without MCP, the LLM would need custom integration code for every business system. MCP standardizes tool access, allowing any MCP-compatible client or agent to discover and invoke enterprise functionality through a common protocol.

The good level of tool description is essential to let the LLM understand the use of that function very well and its input parameters and if there is any constraints like required role.

You can change the mcp_server configurations especially if you plan to run many and need different ports for execution, to do this change the .env file: 

```
from config import MCP_HOST, MCP_PORT, MCP_TRANSPORT

if __name__ == "__main__":
    print("REGISTERED TOOLS:", mcp.list_tools())

    mcp.run(
        transport=MCP_TRANSPORT,
        host=MCP_HOST,
        port=MCP_PORT
    )
```

As you can see, we are using the SSE protocol, The SSE (Server-Sent Events) is a lightweight HTTP-based protocol that allows a server to continuously push real-time updates to a client over a single long-lived connection.

This allow the client to send requests and receive responses without repeatedly opening new HTTP connections.

SSE Key characteristics:

- Built on standard HTTP
- Simple to deploy and firewall-friendly
- Supports streaming responses from server to client
- Lightweight compared to WebSockets
- Well-suited for MCP server communication and AI tool interactions

The MCP server acts as a secure abstraction layer between the agent and the HR system.

---

### 4. HR Agent 

We have 2 HR AGent: 
First: A custom AI agent powered by a local LLM through Ollama named: "hr_agent.py"
Second: A LangGrapgh agent also powered by a local LLM through Ollama named: "lang-graph-hr-agent"

The agent:

* Understands user requests
* Discovers available MCP tools
* Selects the appropriate tool
* Executes multi-step workflows
* Maintains conversational context
* Produces user-friendly responses

This is a simple built agent, but you can still customize its configurations as following:

```python
# For the Python agent:

agent = HRAgent(
    AgentConfig(
        debug=False,
        max_steps=9,
        mcp_endpoint="http://127.0.0.1:8000/sse",
        model_name="llama3.1"
    )
)

# if you called in of them without any configurations, the defaults are resolved from environment variables via .env file through config.py.

from config import MODEL_NAME, DEBUG, MAX_STEPS, MCP_ENDPOINT

# for the LangGeaph agent:

class Config:
    model_name = "llama3.1"
    mcp_url = "http://127.0.0.1:8000/sse"
    debug = False
    max_steps= = 5

# And it also get these values from the .env file through config.py
```

Example requests:

* "What is my leave balance for Osama Oransa?"
* "Show my full profile for EMP001?"
* "Give me the policy for remote work?"
* "Show all my leave requests for Osama Oransa."
* "Give me my basic salary and allowance for EMP002"

Alternatively, you can use any ChatClient and configure the model and the mcp server to convert it to HR Agent (as we well see in the following section).

### 5. LLM Models

In this demo, we used local Ollama models such as llama3.1.

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

This project demostrates:

* Building custom MCP servers
* Tool-based AI agents
* LangGraph orchestration Agent
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
* Multi-agent workflows
* RAG-enabled
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
python init_db.py
```

---

### 5. Seed test data

```bash
python seed_init_data.py
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

Run all cells and interact with the HR Agent the way you want.

<img width="1173" height="681" alt="Screenshot 2026-06-06 at 11 21 08 AM" src="https://github.com/user-attachments/assets/42f27d64-9ed0-472e-b6da-912ef6e2f33b" />

Or you can run it directly from the command line: 

```bash

source .venv/bin/activate
python3 hr_agent.py

```

<img width="1253" height="250" alt="Screenshot 2026-06-06 at 11 22 04 AM" src="https://github.com/user-attachments/assets/bb371168-22eb-496a-bd5d-603c9a7f3fe4" />

Or you can run the LangGraph Agent directly from the command line: 

```bash

source .venv/bin/activate
python3 lang-graph-hr-agent.py

```

<img width="1493" height="740" alt="Screenshot 2026-06-07 at 10 38 42 AM" src="https://github.com/user-attachments/assets/7305e746-a836-42f9-afbf-5771b8f3f8da" />

You can sse the LangGraph agent is much more mature, and all these agents can be solid if it uses a better LLM model.

---

## Using a Chat UI (Optional)

The other way is to integrate the system with a chat interface such as Open WebUI or any MCP-compatible client.

- Add the required model: e.g. Ollama
- Add MCP_SERVER and name it as HR MCP_SERVER

Here I am using ChatBox: https://github.com/chatboxai/chatbox

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


