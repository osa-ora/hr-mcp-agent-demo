import json
import asyncio
import sys
import ollama
import re

from dataclasses import dataclass
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from config import MODEL_NAME, DEBUG, MAX_STEPS, MCP_ENDPOINT

import httpx
import time

# =========================================================
# Global CONFIG
# =========================================================
@dataclass
class AgentConfig:
    model_name: str = MODEL_NAME
    debug: bool = DEBUG
    max_steps: int = MAX_STEPS
    mcp_endpoint: str = MCP_ENDPOINT

# =========================================================
# AGENT
# =========================================================
class HRAgent:
    def __init__(self, config: AgentConfig):
        
        base = AgentConfig()

        if config is None:
            config = base

        # field-by-field override
        self.config = AgentConfig(
            model_name=config.model_name if config.model_name is not None else base.model_name,
            debug=config.debug if config.debug is not None else base.debug,
            max_steps=config.max_steps if config.max_steps is not None else base.max_steps,
            mcp_endpoint=config.mcp_endpoint if config.mcp_endpoint is not None else base.mcp_endpoint,
        )
        print(f"Will use HR MCP Server at: {self.config.mcp_endpoint}")    
        # session state only    
        self._session = None
        self._session_ctx = None
        self.memory = {
            "employee": None,
            "employee_name": None,
            "employee_code": None,
            "manager_code": None,
            "last_response": None,
            "hr_tools": None
        }
    
        # optional: runtime metadata (safe)
        self._last_error = None
        print("[AGENT] initialize() called and Agent is Ready!")
    
    
    # -----------------------------------------------------
    # DEBUG HELPER
    # -----------------------------------------------------
    def debug(self, msg):
        if self.config.debug:
            print(msg)

    # -----------------------------------------------------
    # LLM CALL
    # -----------------------------------------------------
    def call_llm(self, messages):
        #self.debug(f"[AGENT] LLM Message: {messages}")
        response = ollama.chat(
            model=self.config.model_name,
            messages=messages
        )
        return response["message"]["content"]
    # -----------------------------------------------------
    # Memory validation CALL
    # -----------------------------------------------------   
    def validate_identity_gate(self):
        if not self.memory["employee_code"]:
            return {
                "action": "final",
                "answer": "Please provide your employee name or employee code first."
            }
        return None
    # -----------------------------------------------------
    # Update Empolyee Details
    # -----------------------------------------------------  
    def set_identity(self, employee_name: str, employee_code: str):
        if self.memory["employee_code"] is not None:
            if (self.memory["employee_code"] != employee_code or
                self.memory["employee_name"] != employee_name):
    
                return {
                    "error": "Identity is locked for this session and cannot be changed."
                }
    
        self.memory["employee_code"] = employee_code
        self.memory["employee_name"] = employee_name
    
        return {"ok": True}
    # -----------------------------------------------------
    # JSON PARSER
    # -----------------------------------------------------
    def extract_json(self, text: str):
        # 1. try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass
    
        # 2. extract FIRST valid JSON object only
        decoder = json.JSONDecoder()
    
        for i, ch in enumerate(text):
            if ch == "{":
                try:
                    obj, _ = decoder.raw_decode(text[i:])
                    return obj
                except Exception:
                    continue
    
        raise ValueError("No valid JSON object found")

    # -----------------------------------------------------
    # TOOL ARGUMENT NORMALIZER (UNCHANGED LOGIC)
    # -----------------------------------------------------
    def normalize_arguments(self, tool_name: str, args: dict):
        if not isinstance(args, dict):
            return {}
    
        args = dict(args)
    
        # -----------------------------
        # employee identifier cleanup
        # -----------------------------
        if "employee_identifier" in args:
            args["employee_identifier"] = str(args["employee_identifier"])
    
        if "identifier" in args:
            args["employee_identifier"] = str(args.pop("identifier"))
    
        if "employee_number" in args:
            args["employee_identifier"] = str(args.pop("employee_number"))
    
        if "manager_identifier" in args:
            args["employee_identifier"] = str(args.pop("manager_identifier"))
    
        # -----------------------------
        # strict validation rules
        # -----------------------------
        if tool_name == "get_leave_balance":
            if "employee_identifier" in args:
                raise ValueError("get_leave_balance expects employee_code only")
    
        return args

    # -----------------------------------------------------
    # TOOL OUTPUT PARSER (UNCHANGED LOGIC)
    # -----------------------------------------------------
    def parse_tool_output(self, result):
        try:
            content = result.content
    
            # MCP may return multiple content blocks
            if isinstance(content, list) and len(content) > 0:
                first = content[0]
    
                text = getattr(first, "text", None)
                if text is None:
                    text = str(first)
    
            else:
                text = str(content)
    
            # try JSON
            try:
                output = json.loads(text)
            except Exception:
                output = text
    
        except Exception as e:
            output = {
                "error": True,
                "message": str(e)
            }
    
        # -----------------------
        # MEMORY CAPTURE on Firt Use
        # -----------------------
        if isinstance(output, dict) and self.memory.get("employee") is None:
            emp = output.get("employee")
        
            if isinstance(emp, dict):
                self.memory["employee"] = emp
                self.memory["employee_code"] = emp.get("employee_code")
                self.memory["employee_name"] = emp.get("full_name")
    
        return output
    # -----------------------------------------------------
    # SAFE CLOSE (May be used for NOTEBOOKS)
    # -----------------------------------------------------
    async def close(self):
        self.debug("[AGENT] close() called")

        try:
            if self._session:
                await self._session.__aexit__(None, None, None)
        except Exception:
            pass

        try:
            if self._session_ctx:
                await self._session_ctx.__aexit__(None, None, None)
        except Exception:
            pass

        self._session = None
        self._session_ctx = None

    # -----------------------------------------------------
    # SYSTEM PROMPT (UNCHANGED)
    # -----------------------------------------------------
    def system_prompt(self):
        return """
You are an HR agent that ONLY operates via tools. Your final answer to the user MUST be returned via the "final" action.

STRICT RULES:

---

### A) TOOL-DISCOVERY / HELP MODE
If the user asks about:
- available tools
- tool usage
- how to call something

THEN:
- DO NOT call any tool
- DO NOT output tool JSON
- ONLY respond in natural language explaining AVAILABLE TOOLS schema and usage
- Don't return dummy example

---

### B) CORE EXECUTION RULES
Otherwise:

1. NEVER answer directly without tools.
   - Every answer MUST be derived from a tool result.

2. If tool is needed, you MUST output ONLY tool JSON.
   - You are NOT allowed to explain tools, or describe what user should do.
   - You must execute, not instruct.
   
3. ALWAYS return valid JSON ONLY (no explanations, no markdown, no extra text, no dummy examples).

4. If user provides employee name:
   - MUST call get_employee_code FIRST to get the employee_code
   - NO EXCEPTIONS

5. employee_code is STRING ONLY
   - If unknown, MUST be resolved via tool call (never guessed)

6. manager_code is STRING ONLY
   - If unknown, MUST be resolved via tool call
   - It may be equivalent to employee_code only AFTER resolution via tools

7. TOOL SEQUENCING RULE:
   - Identity resolution tools MUST be called BEFORE any HR action tools
   - (approve_leave_request, reject_leave_request, balance queries, leave requests)

8. NO TOOL INVENTION:
   - You may ONLY use tools listed in AVAILABLE TOOLS
   - Never assume or fabricate tool names
9. If tool is search_policies, ALWAYS use "keyword" as the argument name.

---

### C) SAFE DEFAULT BEHAVIOR
If uncertain:
- call get_employee_code first
- then refine using returned data

---

### D) TOOL SELECTION SAFETY
If multiple tools could apply:
- prefer identity tools first
- then read tools
- then write/action tools last

---

AVAILABLE TOOLS:

(Injected at runtime from MCP server. Do not assume tools exist unless listed below.)

---

OUTPUT FORMAT ONLY:

{
  "action": "tool",
  "tool_name": "...",
  "arguments": {}
}

OR

{
  "action": "final",
  "answer": "..."
}

STRICT TOOL RULES:

- You may ONLY use tools from AVAILABLE TOOLS list
- Never invent tools
- If unsure, use get_employee_code first
"""

    # -----------------------------------------------------
    # MAIN LOOP (FIXED ONLY WHERE BROKEN)
    # -----------------------------------------------------
    async def run(self, user_input: str, debug: bool | None = None):
        if debug is not None:
            self.config.debug = debug
        #gate = self.validate_identity_gate()
        #if gate:
        #    return gate["answer"]
        
        self.debug("\n[DEBUG] Starting MCP session...\n")
    
        try:
            # ❌ REMOVED: storing async context manager breaks reuse + causes
            # generator teardown errors in anyio when failures happen
    
            async with sse_client(self.config.mcp_endpoint) as (read, write):
                async with ClientSession(read, write) as session:
    
                    self._session = session
    
                    await session.initialize()
                    tools = await session.list_tools()
                    if self.memory.get("hr_tools") is None:
                        tool_data = tools.model_dump() if hasattr(tools, "model_dump") else tools
                        self.memory["hr_tools"] = json.dumps(tool_data, indent=2)
                    known_context = "" 
                    if self.memory["employee_code"] or self.memory["employee_name"]:
                        known_context += "KNOWN CONTEXT:\n"
                    
                        if self.memory["employee_name"]:
                            known_context += f"employee_name: {self.memory['employee_name']}\n"
                    
                        if self.memory["employee_code"]:
                            known_context += f"employee_code: {self.memory['employee_code']}\n"
                    
                        #if self.memory["last_response"]:
                        #    known_context += f"previous_response: {self.memory['last_response']}\n"
                        self.debug(known_context)
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                self.system_prompt()
                                + known_context
                                + "\n\nAVAILABLE TOOLS:\n"
                                + self.memory["hr_tools"])
                        },
                        {"role": "user", "content": user_input}
                    ]
                    step = 0
    
                    while step < self.config.max_steps:
                        step += 1
    
                        self.debug(f"\n================ STEP {step} ================\n")
                        
                        # LLM CALL
                        raw = self.call_llm(messages)
    
                        self.debug("[RAW LLM OUTPUT]")
                        self.debug(raw)
    
                        # JSON PARSE
                        try:
                            decision = self.extract_json(raw)
                            # 🔧 FIX: prevent mixed "final + tool" hallucinations
                            if decision.get("action") == "final":
                                if "tool_name" in raw:
                                    decision["action"] = "tool"
                        except Exception as e:
                            self.debug(f"[JSON PARSE ERROR] {e}")
                            messages.append({
                                "role": "user",
                                "content": "Return ONLY valid JSON."
                            })
                            continue
    
                        self.debug("[PARSED DECISION]")
                        self.debug(decision)
    
                        action = decision.get("action")
    
                        # =================================================
                        # TOOL EXECUTION PATH
                        # =================================================
                        if action == "tool":
    
                            tool_name = decision.get("tool_name")
                            arguments = self.normalize_arguments(
                                tool_name,
                                decision.get("arguments", {})
                            )
    
                            self.debug(f"[TOOL CALL] {tool_name}")
                            self.debug(f"[ARGS] {arguments}")
    
                            try:
                                result = await session.call_tool(tool_name, arguments)
                                tool_output = self.parse_tool_output(result)
                            except Exception as e:
                                tool_output = {
                                    "error": True,
                                    "message": str(e),
                                    "retry": True
                                }
    
                            self.debug("[TOOL OUTPUT]")
                            self.debug(tool_output)
    
                            messages.append({
                                "role": "assistant",
                                "content": json.dumps(decision)
                            })
    
                            messages.append({
                                "role": "user",
                                "content": json.dumps({
                                    "type": "tool_result",
                                    "data": tool_output
                                })
                            })
    
                            continue
    
                        # =================================================
                        # FINAL ANSWER PATH
                        # =================================================
                        if action == "final":
                            self.memory["last_response"]=decision.get("answer");
                            return decision.get("answer")
    
                        # =================================================
                        # INVALID ACTION PATH
                        # =================================================
                        messages.append({
                            "role": "user",
                            "content": "Invalid action. Must be tool or final."
                        })
                    self.memory["last_response"]="Max steps reached without final answer."
                    return "Max steps reached without final answer."
    
        except Exception as e:
            self.debug(f"[MCP CONNECTION FAILED] {e}")
            raise

# =========================================================
# CLI ENTRYPOINT
# =========================================================
if __name__ == "__main__":

    agent = HRAgent(
        AgentConfig(
            model_name=MODEL_NAME,
            debug=DEBUG,
            max_steps=MAX_STEPS,
            mcp_endpoint= MCP_ENDPOINT
        )
    )
    print("HR Agent ready. Type 'exit' to quit.\n")

    while True:
        user_query = input("Ask HR Agent: ")

        if user_query.lower() in ["exit", "quit"]:
            print("Bye.")
            break

        result = asyncio.run(agent.run(user_query))

        print("\n================ RESPONSE ================\n")
        print(result)
    print("\n================ Good Bye ================\n")