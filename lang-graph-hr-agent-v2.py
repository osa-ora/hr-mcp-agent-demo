import asyncio
import json
import re
from typing import TypedDict, Optional, Any, Dict, List

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import MODEL_NAME, DEBUG, MAX_STEPS, MCP_ENDPOINT, MCP_SCHEME


# =========================================================
# CONFIG
# =========================================================
class Config:
    model_name = MODEL_NAME
    mcp_url = MCP_ENDPOINT
    debug = DEBUG
    max_steps = MAX_STEPS


class Cache:
    tools = []
    skill_map = {}
    valid_skills = set()


CACHE = Cache()


# -----------------------------------------------------
# DEBUG HELPER
# -----------------------------------------------------
def debug(msg: str):
    if Config.debug:
        print(msg)


# =========================================================
# STATE DEFINITION (100% LangGraph Serializable)
# =========================================================
class HRState(TypedDict):
    user_input: str
    tools: List[Any]

    tool_schemas: Optional[Dict[str, Any]]

    # NEW: skill selection layer
    selected_skills: Optional[List[str]]

    plan: Optional[Dict[str, Any]]
    tool_result: Optional[Any]
    final_answer: Optional[str]

    steps: int
    last_tool: Optional[str]
    visited_tools: List[str]
    history: List[Dict[str, Any]]


# =========================================================
# LLM & CLIENT INITIALIZATION
# =========================================================
llm = ChatOllama(model=Config.model_name, temperature=0, format="json")

mcp_client = MultiServerMCPClient({
    "hr": {"transport": MCP_SCHEME, "url": Config.mcp_url}
})


# =========================================================
# CACHE LOADING
# =========================================================
async def load_tool_cache():
    CACHE.tools = await mcp_client.get_tools()
    debug(f"[CACHE] Loaded {len(CACHE.tools)} MCP tools")

    CACHE.skill_map = build_skill_map(CACHE.tools)
    debug(f"[CACHE] Loaded {len(CACHE.skill_map)} Skills")

    CACHE.valid_skills = set(CACHE.skill_map.keys())
    debug(f"[CACHE] Valid Skills: {list(CACHE.valid_skills)}")


def build_skill_map(tools):
    skill_map = {}

    for t in tools:
        metadata = getattr(t, "metadata", None) or {}
        skill = metadata.get("skill", "unknown")

        args_schema = getattr(t, "args_schema", None) or {}

        tool_spec = {
            "name": t.name,
            "description": t.description.strip(),
            "parameters": args_schema
        }

        skill_map.setdefault(skill, []).append(tool_spec)

    return skill_map


# =========================================================
# SKILL SELECTION STEP (NEW)
# =========================================================
async def select_skills(state: HRState):
    debug(f"\n[STEP 0] Skill selection")

    prompt = f"""
You are a skill router for an HR system.

Your job:
Extract ONLY the minimal set of skills required to answer the request.

Available skills:
{list(CACHE.valid_skills)}

User request:
{state["user_input"]}

Return STRICT JSON:
{{
  "skills": ["skill1", "skill2"]
}}

Rules:
- Only use existing skills
- If unsure, return ["general"]
- No explanation
"""

    debug(f"\n[LLM PROMPT SENT including Skills]:\n{prompt}\n{'-'*40}")
    result = llm.invoke(prompt)
    debug(f"[RAW SKILLS] {result.content}")

    try:
        data = json.loads(result.content)
        skills = data.get("skills", ["general"])
    except:
        skills = ["general"]

    filtered = [s for s in skills if s in CACHE.valid_skills]

    if not filtered:
        filtered = ["general"] if "general" in CACHE.valid_skills else list(CACHE.valid_skills)

    state["selected_skills"] = filtered
    debug(f"[SELECTED SKILLS] {filtered}")

    return state

# =========================================================
# PLANNER UTILITIES & MODULAR SUB-FUNCTIONS
# =========================================================

def filter_allowed_tools(selected_skills: list) -> list:
    """Maps selected skills down to a flat list of allowed tool names."""
    filtered_tools = []
    for skill in selected_skills:
        filtered_tools.extend(CACHE.skill_map.get(skill, []))
    return [t["name"] for t in filtered_tools]


def build_filtered_schemas(allowed_tool_names: list) -> dict:
    """Builds structural schemas only for tools present in the allowed list."""
    tool_schemas = {}
    for t in CACHE.tools:
        if t.name in allowed_tool_names:
            pydantic_schema = getattr(t, "args_schema", None)
            json_schema = {}

            if pydantic_schema:
                if isinstance(pydantic_schema, dict):
                    json_schema = pydantic_schema
                elif hasattr(pydantic_schema, "model_json_schema"):
                    json_schema = pydantic_schema.model_json_schema()
                elif hasattr(pydantic_schema, "schema"):
                    json_schema = pydantic_schema.schema()

            tool_schemas[t.name] = {
                "description": t.description,
                "parameters": json_schema
            }
    return tool_schemas


def sanitize_arguments(raw_args: Any) -> dict:
    """Removes keys with None values, blank text, or literal 'null'/'none' strings."""
    proposed_args = {}
    if isinstance(raw_args, dict):
        for k, v in raw_args.items():
            if v is not None and str(v).lower() not in ["null", "none", ""]:
                proposed_args[k] = v
    return proposed_args


def build_planner_prompt(user_input: str, tool_names: list, tool_schemas: dict, history: list) -> str:
    """Constructs a context-ordered prompt that natively resolves prerequisites and prevents loops."""
    
    prompt = f"""You are an HR Goal Evaluator. Your primary job is to determine if the 'History of executed steps' already contains the complete answer to the User Request.

[CRITICAL STOPPING RULES]
1. Review the 'History of executed steps' log at the bottom.
2. If ANY tool in the history has already successfully executed and returned the target data payload (such as an employee profile, a manager name, or a leave balance), your goal is complete! You must immediately STOP and return exactly:
{{
  "tool": "FINAL",
  "arguments": {{}}
}}
3. ABSOLUTE REPETITION BAN: Never select a tool name if it already appears in the history log below with the exact same arguments. Repeating an execution means failure.

[PREREQUISITE RULE]
- If you need an 'employee_code' to run a tool, but the User Request only provides a name, you CANNOT call profile or leave tools yet. You must first get employee_code with that name to find their employee_code.

[AVAILABLE TOOLS]
Only if the history below is missing the required final data, select the next logical tool from this list:
Allowed Names: {tool_names}
Schemas:
{json.dumps(tool_schemas, indent=2)}

[OUTPUT FORMAT]
You must reply with ONLY a raw JSON block matching this schema:
{{
  "tool": "TOOL_NAME_OR_FINAL",
  "arguments": {{
    "parameter_name": "value"
  }}
}}
No explanations, no markdown blocks, no commentary.

[CURRENT SESSION STATE]
User Request: "{user_input}"
"""

    if history:
        prompt += f"\nHistory of executed steps (Review this to see if you should stop):\n"
        prompt += json.dumps(history, indent=2)
    else:
        prompt += "\nHistory of executed steps:\n[] (No steps taken yet. Evaluate if you need to fetch an employee_code first.)"
        
    return prompt


# =========================================================
# MAIN COHESIVE PLANNER NODE
# =========================================================
async def planner(state: HRState):
    debug(f"\n[STEP 1] Planning (Turn {state.get('steps', 0) + 1})")
    state["steps"] = state.get("steps", 0) + 1
    
    if "history" not in state or state["history"] is None:
        state["history"] = []

    # 1. Filter out permitted names and schemas
    tool_names = filter_allowed_tools(state.get("selected_skills", []))
    state["tool_schemas"] = build_filtered_schemas(tool_names)

    # 2. Build the specialized prompt and execute
    prompt = build_planner_prompt(
        user_input=state["user_input"],
        tool_names=tool_names,
        tool_schemas=state["tool_schemas"],
        history=state["history"]
    )
    debug(f"\n[LLM PROMPT For Planner]:\n{prompt}\n{'-'*40}")
    result = llm.invoke(prompt)
    debug(f"[RAW PLAN] {result.content}")

    try:
        plan = parse_json(result.content)
    except:
        plan = {"tool": "FINAL", "arguments": {}}

    # 3. Sanitize out the null / empty tokens
    proposed_tool = plan.get("tool")
    plan["arguments"] = sanitize_arguments(plan.get("arguments", {}))

    # 4. Enforce strict back-to-back repetition breaking logic
    if state.get("history") and proposed_tool != "FINAL":
        last_step = state["history"][-1]
        if last_step.get("tool") == proposed_tool and last_step.get("arguments") == plan["arguments"]:
            debug(f"[GUARD TRIGGERED] Forcing FINAL. Tool '{proposed_tool}' cannot be called back-to-back with identical arguments.")
            plan = {"tool": "FINAL", "arguments": {}}

    state["plan"] = plan
    return state

# =========================================================
# Parse Helper
# =========================================================

def parse_json(text: str) -> dict:
    """Safely extracts and parses JSON from LLM text responses."""
    # Remove markdown code blocks if present
    cleaned = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()
    return json.loads(cleaned)

# =========================================================
# EXECUTION
# =========================================================
async def execute_tool(state: HRState):
    debug("\n[STEP 2] Tool execution")

    tool_name = state["plan"]["tool"]
    args = state["plan"].get("arguments", {})

    # --------------------------------------------------------
    # FIX: Clean out null/None arguments before execution & history
    # --------------------------------------------------------
    if isinstance(args, dict):
        cleaned_args = {k: v for k, v in args.items() if v is not None}
    else:
        cleaned_args = args

    tool = next((t for t in CACHE.tools if t.name == tool_name), None)

    if not tool:
        state["tool_result"] = {"error": f"Tool {tool_name} not found"}
        return state

    try:
        # Run using cleaned arguments
        result = await tool.ainvoke(cleaned_args)

        if isinstance(result, list) and result:
            result_content = result[0].content if hasattr(result[0], 'content') else result[0].get("text", result[0])
        elif hasattr(result, 'content'):
            result_content = result.content
        elif isinstance(result, dict):
            result_content = result.get("text", result)
        else:
            result_content = str(result)

        state["tool_result"] = result_content
        
        current_history = list(state.get("history", []))
        current_history.append({
            "tool": tool_name,
            "arguments": cleaned_args,  # Save clean arguments to history
            "result": result_content
        })
        state["history"] = current_history

    except Exception as e:
        state["tool_result"] = {"error": str(e)}
        current_history = list(state.get("history", []))
        current_history.append({"tool": tool_name, "arguments": cleaned_args, "error": str(e)})
        state["history"] = current_history

    return state


# =========================================================
# ROUTER (FIXED)
# =========================================================
def route(state: HRState):
    if state.get("plan", {}).get("tool") == "FINAL":
        return "final"   # FIXED (was "end")
    if state.get("steps", 0) >= Config.max_steps:
        return "final"   # FIXED (was "end")
    return "execute"


# =========================================================
# RESPONSE
# =========================================================
#def generate_response(state: HRState):
#    result = state.get("tool_result", "No data")
#    state["final_answer"] = json.dumps(result, indent=2)
#    return state

# =========================================================
# RESPONSE (REMOVED OVERWRITE BUG)
# =========================================================
def generate_response(state: HRState):
    # Pass the ENTIRE history log to the response generator, not just the last execution data
    history_data = state.get("history", [])
    
    prompt = f"""
    You are a helpful HR Assistant. 
    Answer the user's original request using the provided history of tool execution steps.
    Be concise, professional, and do not mention the technical tool names.
    
    User Request: {state["user_input"]}
    Execution History Data:
    {json.dumps(history_data, indent=2)}
    """
    
    friendly_llm = ChatOllama(model=Config.model_name, temperature=0.5) 
    response = friendly_llm.invoke(prompt)
    
    state["final_answer"] = response.content
    return state


# =========================================================
# GRAPH
# =========================================================
def build_graph():
    g = StateGraph(HRState)

    g.add_node("skill", select_skills)
    g.add_node("plan", planner)
    g.add_node("exec", execute_tool)
    g.add_node("final", generate_response)

    g.set_entry_point("skill")

    g.add_edge("skill", "plan")

    g.add_conditional_edges(
        "plan",
        route,
        {
            "execute": "exec",
            "final": "final"
        }
    )

    g.add_edge("exec", "plan")
    g.add_edge("final", END)

    return g.compile()

graph = build_graph()

# =========================================================
# RUNNER
# =========================================================
async def run_agent(query: str):

    result = await graph.ainvoke({
        "user_input": query,
        "tools": CACHE.tools,
        "tool_schemas": None,
        "selected_skills": None,
        "plan": None,
        "tool_result": None,
        "final_answer": None,
        "steps": 0,
        "last_tool": None,
        "visited_tools": [],
        "history": []
    })

    return result["final_answer"]


# =========================================================
# MAIN
# =========================================================
async def main():
    await load_tool_cache()
    print("\nHR AGENT READY\n")

    while True:
        q = input(">>>>> Ask HR: ")

        if q.lower() in ["exit", "quit"]:
            break

        if not q.strip():
            continue

        ans = await run_agent(q)
        print("\n================ OUTPUT ================\n")
        print(ans)


if __name__ == "__main__":
    asyncio.run(main())