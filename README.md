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

Here is a simplified view of the sample HR DB:

<img width="1536" height="1024" alt="hr_erd_diagram" src="https://github.com/user-attachments/assets/e811de46-bcb9-48ba-a43d-f0ea3fe8a758" />


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

A custom MCP server built using FastMCP that exposes HR operations as tools, FastMCP is a Python framework for building and exposing tools through the Model Context Protocol (MCP). 
It simplifies the creation of AI-accessible services by providing a lightweight way to define, register, and serve tools that can be discovered and invoked by MCP-compatible agents and clients.

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
# EMPLOYEE PROFILE
# SKILL: employee_profile
# =========================================================
@mcp.tool(
    annotations={"skill": "employee_profile"},
    description="""
ROLE: ANY EMPLOYEE

Get basic employee basic profile information using employee_code
"""
)
def get_employee_basic_profile(employee_code: str):
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

We used initially SSE protocol but then switched to HTTP, The SSE (Server-Sent Events) is a lightweight HTTP-based protocol that allows a server to continuously push real-time updates to a client over a single long-lived connection, it becomes a legacy now and most of the modern mcp are using http (or streamable_http).

The MCP server acts as a secure abstraction layer between the agent and the HR system.

---

### 4. HR Agent 

## HR Agent Examples

We have built four HR agent examples:

### First: Custom Python Agent

A custom Python AI agent powered by a local LLM through Ollama, named **`hr_agent.py`**.

### Second: Level-1 LangGraph Agent

A Level-1 LangGraph agent, also powered by a local LLM through Ollama, named **`lang-graph-hr-agent.py`**. This version sends all MCP server tools to the LLM for planning and execution.

**LangGraph** is a framework for building stateful, multi-step AI agents using graph-based workflows. It enables developers to model complex reasoning, planning, tool-calling, and decision-making processes as interconnected nodes, making agent execution more controllable, observable, and maintainable than traditional prompt chains.

### Third: Level-2 LangGraph Agent

A Level-2 LangGraph agent named **`lang-graph-hr-agent-v2.py`**. This version is skill-based, filtering MCP server tools by skill (virtual grouping) and sending only the relevant tool groups required by the LLM to complete the requested task.

#### Skill-Based Tool Routing

The agent uses a lightweight skill-selection layer to identify the minimum set of MCP tool categories required for a user request. By filtering available tools before planning, the agent reduces prompt size, improves tool-selection accuracy, and keeps reasoning focused on the relevant domain capabilities.

### Fourth: Level-3 LangGraph Agent

A Level-3 LangGraph agent named **`lang-graph-hr-agent-v3.py`**. This version builds on the skill-based architecture and externalizes prompts into dedicated template files.

#### Prompt Externalization with Jinja2

The agent uses Jinja2 templates to externalize all LLM prompts from the application code. This separates prompt engineering from business logic, making prompts easier to maintain, version, test, and update without modifying the agent implementation. Runtime context (such as user input, tool schemas, and execution history) is injected into templates to generate the final prompts sent to the model.

Jinja is a fast, expressive, extensible templating engine. Special placeholders in the template allow writing code similar to Python syntax. Then the template is passed data to render the final document, e.g. {{ variable }} place holders, while {% %} is control flow syntax.
Read more: https://jinja.palletsprojects.com/en/stable/


For Example: response.jinja2 
```
You are a helpful HR Assistant.

Answer the user's original request using the provided history of tool execution steps.
Be concise, professional, and do not mention the technical tool names.

User Request: {{ user_input }}

Execution History Data:
{{ history }}
```
And we seed these placeholders with the corresponding values for the agent.

The agent main functions:

* Understands user requests
* Discovers available MCP tools
* Selects the appropriate tool
* Executes multi-step workflows
* Maintains conversational context
* Produces user-friendly responses

You can still customize agent(s) configurations as following:

```python
# For the custom Python agent:

agent = HRAgent(
    AgentConfig(
        debug=False,
        max_steps=9,
        mcp_endpoint="http://127.0.0.1:8000/mcp",
        model_name="llama3.1"
    )
)

# if you called in of them without any configurations, the defaults are resolved from environment variables via .env file through config.py.

from config import MODEL_NAME, DEBUG, MAX_STEPS, MCP_ENDPOINT

# for both LangGraph agent(s):

class Config:
    model_name = "llama3.1"
    mcp_url = "http://127.0.0.1:8000/mcp"
    debug = False
    max_steps= = 5

# And it also get these values from the .env file through config.py
```

Example requests:

* "leave balance for Osama Oransa?"
* "basic profile for Sara Ali"
* "Show my full profile for EMP001?"
* "policy for remote work?"
* "leave requests for Osama Oransa."
* "basic profile for EMP002"

Alternatively, you can use any ChatClient and configure the model and the mcp server to convert it to HR Agent (as we well see in the following section).

### 5. LLM Models

In this demo, we used local Ollama models such as llama3.1.

---

## Technologies Used

* Python, FastMCP, MCP (Model Context Protocol), Ollama, Llama 3.1, PostgreSQL, SQLAlchemy, AsyncIO, Langgraph and others.

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
* Natural language interfaces for business systems.

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
Then edit the .env file for any changes you need to do.<img width="1244" height="648" alt="Screenshot 2026-06-11 at 7 04 37 AM" src="https://github.com/user-attachments/assets/98cee584-46ca-49b8-8c12-22858bb85d51" />


---

### 3. Start PostgreSQL DB & Create 'hrdb' database

```sql
CREATE DATABASE hrdb;
```

---

### 4. Initialize database schema

```bash
python3 init_db.py
```

---

### 5. Seed test data

```bash
python3 seed_init_data.py
```

---

### 6. Run MCP server

```bash
python3 mcp_server.py
```

If successful, you will see:

```
Starting MCP server 'hr-system-v2' with transport 'http' on transport.py:304 http://0.0.0.0:8000/mcp
```

---

### MCP Server Screenshot

<img width="1247" height="657" alt="Screenshot 2026-06-11 at 7 05 07 AM" src="https://github.com/user-attachments/assets/f875de39-2905-4571-abf8-8593b1435e49" />


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

<img width="1091" height="676" alt="Screenshot 2026-06-11 at 7 08 33 AM" src="https://github.com/user-attachments/assets/94757f11-b500-40a0-a8ef-b2e473b70f83" />


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

You can then use the better quality agent, that filter the mcp tools based on the needed skills to respond to customer specific request, using:
```bash

source .venv/bin/activate
python3 lang-graph-hr-agent-v2.py

```
<img width="1250" height="722" alt="Screenshot 2026-06-08 at 5 04 50 PM" src="https://github.com/user-attachments/assets/7ed577c0-b13f-43d6-8180-2ae7f4f5c61a" />

Finally, the more dynamic agent, that filter the mcp tools and load the prompt from templates, using:
```bash

source .venv/bin/activate
python3 lang-graph-hr-agent-v3.py
```

You can see the LangGraph agent is much more mature and more accurate. 

Note: The performance of all these agents can be more solid if they use a better and strong LLM.

---

## Using a Chat UI (Optional)

The other way is to integrate the system with a chat interface such as Open WebUI or any MCP-compatible client.

- Add the required model: e.g. Ollama
- Add MCP_SERVER and name it as HR MCP_SERVER

Here I am using for example: ChatBox: https://github.com/chatboxai/chatbox

<img width="1013" height="748" alt="Screenshot 2026-06-05 at 11 21 45 PM" src="https://github.com/user-attachments/assets/73cc0c46-d293-4f11-a38f-9a6bdf6cfb1c" />
<img width="588" height="598" alt="Screenshot 2026-06-05 at 11 21 53 PM" src="https://github.com/user-attachments/assets/2ce138ac-2d6e-4841-825d-7e7f4b39d88e" />

<img width="761" height="674" alt="Screenshot 2026-06-11 at 7 10 08 AM" src="https://github.com/user-attachments/assets/7356d14f-f09d-43ef-a9ea-1566dc87a1f7" />


This allows a more natural chat-based experience instead of running the Python agent directly.

<img width="1013" height="752" alt="Screenshot 2026-06-05 at 11 26 53 PM" src="https://github.com/user-attachments/assets/55acf1d6-c844-412f-a150-590bb40694a9" />
<img width="1021" height="747" alt="Screenshot 2026-06-05 at 11 28 10 PM" src="https://github.com/user-attachments/assets/e18dd63c-3c90-4cff-8a74-69423b9376ce" />
<img width="1015" height="751" alt="Screenshot 2026-06-05 at 11 31 04 PM" src="https://github.com/user-attachments/assets/6ef78f77-4f49-4178-8a22-1cd51d8d2e09" />
<img width="1015" height="742" alt="Screenshot 2026-06-05 at 11 40 24 PM" src="https://github.com/user-attachments/assets/3417c472-eda4-4bc9-a3b1-403e4d9f2c02" />

---

## How to Run the Demo on OpenShift Environment

### 1) Create Project and Configurations

After login to OpenShift cluster, follow these steps:

```bash
# Create new project
oc new-project hr-mcp

# Create ConfigMap
oc create configmap hr-mcp-config \
--from-literal=DATABASE_USER=postgres \
--from-literal=DATABASE_HOST=postgresql.hr-mcp.svc.cluster.local \
--from-literal=DATABASE_PORT=5432 \
--from-literal=DATABASE_NAME=hrdb \
--from-literal=MCP_SCHEME=http \
--from-literal=MCP_HOST=0.0.0.0 \
--from-literal=MCP_PORT=8080 \
--from-literal=MCP_PATH=/mcp \
--from-literal=MCP_TRANSPORT=http \
--from-literal=DEBUG=true \
-n hr-mcp

# Create Secret
oc create secret generic hr-mcp-secret \
  --from-literal=DATABASE_USER=postgres \
  --from-literal=DATABASE_PASSWORD=postgres \
  -n hr-mcp

```

### 2) Deploy Our HR DB and initialize it

Execute the following command (or you can provision it from the OCP GUI):

```
oc new-app postgresql-persistent \
  --param=POSTGRESQL_USER=postgres \
  --param=POSTGRESQL_PASSWORD=postgres \
  --param=POSTGRESQL_DATABASE=hrdb \
  --name=postgresql -n hr-mcp
```

Login to the DB Pod and run the following commands: 

```
psql -U postgres

CREATE DATABASE hrdb;

\q
```

Then install the DB schema and test data from inside the Pod:

```
curl -s https://raw.githubusercontent.com/osa-ora/hr-mcp-agent-demo/refs/heads/main/db_scripts/schema.sql \
| psql -U postgres -d hrdb

curl -s https://raw.githubusercontent.com/osa-ora/hr-mcp-agent-demo/refs/heads/main/db_scripts/load_sample_data.sql \
| psql -U postgres -d hrdb
```

### 3) Provision the mcp_server using S2I

Provision it and attach the configMap and Secret
```

oc new-app python:3.12-minimal-ubi10~https://github.com/osa-ora/hr-mcp-agent-demo --name=hr-mcp-server -n hr-mcp

oc set env deployment/hr-mcp-server --from=configmap/hr-mcp-config
oc set env deployment/hr-mcp-server --from=secret/hr-mcp-secret
oc rollout restart deployment/hr-mcp-server

```

if started successfully, check the logs to confirm that no issues and end points are correctly mapped: 
<img width="1169" height="570" alt="Screenshot 2026-06-11 at 12 11 33 AM" src="https://github.com/user-attachments/assets/744a4fa9-a9ae-487a-9f5c-49b0d163e686" />

### 4) Testing the MCP Server:

If you want to test it remotely then expose a route:

```
oc expose svc/hr-mcp-server -n hr-mcp
```

if you need to test it from inside OpenShift using the playground, then go to project redhat-ods-applications and edit the ConfigMap: gen-ai-aa-mcp-servers by adding the following section:

```
kind: ConfigMap
apiVersion: v1
metadata:
  name: gen-ai-aa-mcp-servers
  namespace: redhat-ods-applications
  ....
  ....
data:
  HR-MCP-Server: |
    {
      "url": "http://hr-mcp-server.hr-mcp.svc.cluster.local:8080/mcp",
      "description": "An MCP server for interacting with our HR DB tools."
    }
```
Or you can create MCPServer to auto-discovered using the OpenShift AI MCP server section

Something like this: 
```
oc apply -f - <<EOF
apiVersion: mcp.opendatahub.io/v1alpha1
kind: MCPServer
metadata:
  name: my-hr-mcp-server
  namespace: hr-mcp
spec:
  image: image-registry.openshift-image-registry.svc:5000/test/hr-mcp-server@sha256:549f50c109f4c6d040e948edf3169fc811be7559ec171f66062fa06f0ad60929
  transportType: sse
  port: 8000
  envFrom:
    - configMapRef:
        name: hr-mcp-config
    - secretRef:
        name: hr-mcp-secret
EOF
```
But i didn't tested it, as i don't have the MCP Operstor enabled in my environment.

Now go to OpenShift UI, check the MCP Servers section:

<img width="1466" height="704" alt="Screenshot 2026-06-11 at 12 05 18 AM" src="https://github.com/user-attachments/assets/19924c77-fde4-4593-87ae-412bae7c7dcb" />

Then create a playground for the MCP server and one of the existing models, and enjoy chatting to it: 

<img width="1477" height="721" alt="Screenshot 2026-06-11 at 12 04 44 AM" src="https://github.com/user-attachments/assets/1c8f1742-cf05-439d-8dd9-acf3e00e55d7" />

To connect to it remotely from ChatBox for example, follow the same steps using the Route:

```

```
Add the http prefix and the path configured /mcp at the end, as the following: 

<img width="767" height="682" alt="Screenshot 2026-06-11 at 12 07 04 AM" src="https://github.com/user-attachments/assets/2e7f2a26-11d7-4a40-97e9-bf27a714ae4a" />

And enjoy chatting with our HR MCP Server.


## License

This project is for educational and demonstration purposes only.


