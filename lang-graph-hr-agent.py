import asyncio
import json
import re
from typing import TypedDict, Optional, Any, Dict, List

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import MODEL_NAME, DEBUG, MAX_STEPS, MCP_ENDPOINT


# =========================================================
# CONFIG
# =========================================================
class Config:
    model_name = MODEL_NAME
    mcp_url = MCP_ENDPOINT
    debug = DEBUG
    max_steps = MAX_STEPS


# -----------------------------------------------------
# DEBUG HELPER
# -----------------------------------------------------
def debug(msg: str):
    if Config.debug:
        print(msg)


# =========================================================
# STATE
# =========================================================
class HRState(TypedDict):
    user_input: str
    tools: List[Any]

    plan: Optional[Dict[str, Any]]
    tool_result: Optional[Any]
    final_answer: Optional[str]

    steps: int

    last_tool: Optional[str]
    visited_tools: Optional[set]
    history: List[Dict[str, Any]]


# =========================================================
# LLM
# =========================================================
llm = ChatOllama(model=Config.model_name, temperature=0, format="json")


# =========================================================
# MCP CLIENT
# =========================================================
mcp_client = MultiServerMCPClient({
    "hr": {"transport": "sse", "url": Config.mcp_url}
})


# =========================================================
# INIT TOOLS
# =========================================================
async def init_tools():
    tools = await mcp_client.get_tools()
    debug(f"[INIT] Loaded {len(tools)} MCP tools")
    return tools


# =========================================================
# JSON PARSER
# =========================================================
def parse_json(text: str):
    try:
        return json.loads(text)
    except:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise
        return json.loads(m.group())


# =========================================================
# TOOL SCHEMA EXTRACTOR
# =========================================================
def get_tool_schema(tools):
    schema = {}
    for t in tools:
        schema[t.name] = getattr(t, "args_schema", None)
    return schema


# =========================================================
# FIX MEMORY CACHE
# =========================================================
NAME_TO_CODE_CACHE = {}


# =========================================================
# STEP 1: PLANNER
# =========================================================
async def planner(state: HRState):
    debug("\n[STEP 1] Planning")

    state["steps"] = state.get("steps", 0) + 1
    if "history" not in state or state["history"] is None:
        state["history"] = []

    tool_names = [t.name for t in state["tools"]]
    tool_schema = get_tool_schema(state["tools"])

    prompt = f"""You are an HR tool planner. Your only job is to select the next single tool or finish.

Available tools:
{tool_names}

STRICT Tool argument schemas (Verify parameter names carefully):
{tool_schema}

CRITICAL EXECUTION RULES:
1. Never try to get the profile twice
2. Review the history of tools called and their results before making a decision.
3. If previous tool outputs already returned the required data to answer the user request, you MUST finish immediately by returning: {{"tool": "FINAL", "arguments": {{}}}}
4. If a tool doesn't explicitly exist for a single item (e.g., getting a single leave request by ID), use a list or broader retrieval tool that can contain that ID instead. Do not invent tool names.
5. If a tool requires an 'employee_code' or 'manager_code' argument and the user provided a name (e.g. 'Osama Oransa', 'Sara'), you must call `get_employee_code` first. Do not try to guess a code or supply a blank string.
6. Never pass a raw dictionary or a nested function call string as an argument value.
7. Omit optional arguments if you don't have their values. Do not pass null values.
8. Do not repeat a tool execution if it has already returned valid data for your parameters.
9. If an action requires an 'employee_code' or 'manager_code' and no specific name or code is specified in the prompt text, look up the target request context using history tools or ask for clarification. 
10. NEVER invent or pass placeholder strings like "user provided name", "result of Step 1", or "leave request 25" as tool arguments. If you don't have a valid code, you must halt execution immediately.
11. If a tool execution returns a valid list or structure containing data or explicitly empty results, do not re-run it or alter arguments to find combinations.
12. Omit optional arguments if you don't have their values. Do not pass null values or invent arguments.

OUTPUT FORMAT:
- You must reply with a single valid JSON object containing "tool" and "arguments" keys.
- Do not include any explanations, markdown code blocks, or commentary.

User request:
{state["user_input"]}
"""

    # Inject the history into the single flat prompt structure Llama understands cleanly
    if state["history"]:
        prompt += "\n\nExecution History so far:"
        for idx, turn in enumerate(state["history"]):
            prompt += f"\nStep {idx+1}: Tool called: '{turn['tool']}' with parameters: {json.dumps(turn.get('arguments', {}))} -> Result context: {json.dumps(turn['result'])}"

    result = llm.invoke(prompt)
    debug(f"[RAW PLAN] {result.content}")

    try:
        plan = parse_json(result.content)
    except:
        plan = {"tool": "FINAL", "arguments": {}}

    tool = plan.get("tool")
    
    if state.get("visited_tools") is None:
        state["visited_tools"] = set()

    visited = state["visited_tools"]

    if tool in visited and tool == state.get("last_tool") and tool != "FINAL":
        debug("[LOOP BREAK] duplicate tool execution cycle caught → forcing FINAL stop")
        plan = {"tool": "FINAL", "arguments": {}}

    if tool != "FINAL":
        visited.add(tool)
        state["last_tool"] = tool

    state["plan"] = plan
    return state


# =========================================================
# STEP 2: NORMALIZER
# =========================================================
def normalize_args(tool_name, args, tools):
    tool = next((t for t in tools if t.name == tool_name), None)
    if not tool:
        return args
    return args or {}


# =========================================================
# STEP 3: EXECUTION
# =========================================================
async def execute_tool(state: HRState):
    debug("\n[STEP 2] Tool execution")

    tool_name = state["plan"]["tool"]
    args = state["plan"].get("arguments", {})

    tool = next((t for t in state["tools"] if t.name == tool_name), None)

    if not tool:
        error_msg = f"Error: Tool '{tool_name}' does not exist. Choose from available tools list only."
        state["tool_result"] = {"error": error_msg}
        state["history"].append({"tool": tool_name, "arguments": args, "result": error_msg})
        debug(f"[TOOL RESULT] {state['tool_result']}")
        return state

    args = normalize_args(tool_name, args, state["tools"])
    debug(f"[ARGS CLEAN] {args}")

    try:
        result = await tool.ainvoke(args)

        if isinstance(result, list) and result:
            result = result[0].get("text", result)
        elif isinstance(result, dict):
            result = result.get("text", result)

        state["tool_result"] = result
        state["history"].append({"tool": tool_name, "arguments": args, "result": result})

        if tool_name == "get_employee_code":
            name = args.get("employee_name")
            if isinstance(result, str) and name:
                NAME_TO_CODE_CACHE[name] = result

    except Exception as e:
        state["tool_result"] = {"error": str(e)}
        state["history"].append({"tool": tool_name, "arguments": args, "result": f"Error: {str(e)}"})

    debug(f"[TOOL RESULT] {state['tool_result']}")
    return state


# =========================================================
# STEP 4: ROUTING CONDITIONAL EDGES
# =========================================================
def check_next_step(state: HRState):
    plan = state.get("plan", {})
    tool_name = plan.get("tool", "FINAL")

    if tool_name == "FINAL" or state.get("steps", 0) >= Config.max_steps:
        return "end"
    
    return "execute"


# =========================================================
# STEP 5: RESPONSE GENERATION
# =========================================================
def generate_response(state: HRState):
    debug("\n[STEP 3] Response")

    if state.get("history"):
        result = state["history"][-1]["result"]
    else:
        result = state.get("tool_result", "No data retrieved.")

    state["final_answer"] = json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
    return state


# =========================================================
# GRAPH BUILDER
# =========================================================
def build_graph():
    g = StateGraph(HRState)

    g.add_node("plan", planner)
    g.add_node("exec", execute_tool)
    g.add_node("final", generate_response)

    g.set_entry_point("plan")

    g.add_conditional_edges(
        "plan",
        check_next_step,
        {
            "execute": "exec",
            "end": "final"
        }
    )

    g.add_edge("exec", "plan")
    g.add_edge("final", END)

    return g.compile()


# =========================================================
# RUNNER
# =========================================================
async def run_agent(query: str, tools):
    graph = build_graph()

    result = await graph.ainvoke({
        "user_input": query,
        "tools": tools,
        "plan": None,
        "tool_result": None,
        "final_answer": None,
        "steps": 0,
        "last_tool": None,
        "visited_tools": set(),
        "history": []
    })

    return result["final_answer"]


# =========================================================
# MAIN
# =========================================================
async def main():
    tools = await init_tools()
    print("\nHR AGENT READY\n")

    while True:
        q = input(">>>>> Ask HR: ")

        if q.lower() in ["exit", "quit"]:
            break

        ans = await run_agent(q, tools)
        print("\n================ OUTPUT ================\n")
        print(ans)

    print("\n================ Good Bye ================\n")
if __name__ == "__main__":
    asyncio.run(main())