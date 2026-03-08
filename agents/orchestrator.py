from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import json, os

from models.schemas import (
    RequirementsOutput,
    ArchitectureOutput,
    DatabaseOutput,
    ApiDesignOutput,
    StructuredDesignOutput,
)
from agents.requirements_agent import run_requirements_agent
from agents.architecture_agent import run_architecture_agent
from agents.database_agent import run_database_agent
from agents.api_agent import run_api_agent
from agents.mock_responses import (
    MOCK_REQUIREMENTS,
    MOCK_ARCHITECTURE,
    MOCK_DATABASE,
    MOCK_API,
)

USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"


# ─────────────────────────────────────────
# State
# ─────────────────────────────────────────

class DesignState(TypedDict):
    user_message: str
    history: list[dict]
    needs_design: bool
    requirements: Optional[RequirementsOutput]
    architecture: Optional[ArchitectureOutput]
    database: Optional[DatabaseOutput]
    api_design: Optional[ApiDesignOutput]
    final_response: str


# ─────────────────────────────────────────
# Node 0: Router
# ─────────────────────────────────────────

async def router_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        return {**state, "needs_design": True}

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o"), temperature=0)
    prompt = f"""
You are a router. Decide if the user's message requires full system design (all 4 agents)
or just a conversational answer.

User message: "{state['user_message']}"

Reply with ONLY one word: "DESIGN" or "CHAT"
"""
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    decision = response.content.strip().upper()
    return {**state, "needs_design": decision == "DESIGN"}


# ─────────────────────────────────────────
# Node 1: Requirements
# ─────────────────────────────────────────

async def requirements_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        return {**state, "requirements": MOCK_REQUIREMENTS}
    result = await run_requirements_agent(state["user_message"], state["history"])
    return {**state, "requirements": result}


# ─────────────────────────────────────────
# Node 2: Architecture
# ─────────────────────────────────────────

async def architecture_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        return {**state, "architecture": MOCK_ARCHITECTURE}
    result = await run_architecture_agent(state["user_message"], state["requirements"])
    return {**state, "architecture": result}


# ─────────────────────────────────────────
# Node 3: Database
# ─────────────────────────────────────────

async def database_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        return {**state, "database": MOCK_DATABASE}
    result = await run_database_agent(
        state["user_message"],
        state["requirements"],
        state["architecture"],
    )
    return {**state, "database": result}


# ─────────────────────────────────────────
# Node 4: API
# ─────────────────────────────────────────

async def api_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        return {**state, "api_design": MOCK_API}
    result = await run_api_agent(
        state["user_message"],
        state["requirements"],
        state["architecture"],
        state["database"],
    )
    return {**state, "api_design": result}


# ─────────────────────────────────────────
# Node 5: Summarizer
# ─────────────────────────────────────────

async def summarizer_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        summary = """## ✅ System Design Complete (Mock Mode)

### Architecture
Chosen a **Modular Monolith** with Spring Boot 3.2 — ideal for small team and medium scale.

### Services
- **AuthModule** — JWT login & registration
- **ProductModule** — catalog, search, CRUD
- **OrderModule** — cart and order management
- **AdminModule** — dashboard and management

### Database
5 MySQL tables: `users`, `categories`, `products`, `orders`, `order_items` with proper FK constraints.

### API
6 REST endpoints with Spring Security JWT — public routes for auth/browse, protected routes for orders and admin.

### Docker
Single app container + MySQL container via Docker Compose.

> 💡 This is a **mock response**. Add your OpenAI API key and set `USE_MOCK=false` to get real AI-generated designs.
"""
        return {**state, "final_response": summary}

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o"), temperature=0.3)
    context = f"""
You are a System Design Assistant. Summarize the complete system design clearly using markdown.

Requirements summary: {state['requirements'].summary if state['requirements'] else 'N/A'}
Architecture summary: {state['architecture'].summary if state['architecture'] else 'N/A'}
Database summary: {state['database'].summary if state['database'] else 'N/A'}
API summary: {state['api_design'].summary if state['api_design'] else 'N/A'}
"""
    response = await llm.ainvoke([HumanMessage(content=context)])
    return {**state, "final_response": response.content}


# ─────────────────────────────────────────
# Node: Simple Chat
# ─────────────────────────────────────────

async def chat_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        return {**state, "final_response": "Mock chat mode — describe a system and I'll run the full design pipeline!"}

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o"), temperature=0.5)
    system = """You are a System Designer Assistant specializing in Java Spring Boot,
MySQL, JPA, Spring Security (JWT), and Docker. Answer technically and helpfully."""

    messages = [SystemMessage(content=system)]
    for msg in state["history"][-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(SystemMessage(content=msg["content"]))
    messages.append(HumanMessage(content=state["user_message"]))

    response = await llm.ainvoke(messages)
    return {**state, "final_response": response.content}


# ─────────────────────────────────────────
# Conditional Edge
# ─────────────────────────────────────────

def route_decision(state: DesignState) -> str:
    return "requirements" if state["needs_design"] else "chat"


# ─────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────

def build_graph():
    graph = StateGraph(DesignState)

    graph.add_node("router", router_node)
    graph.add_node("requirements", requirements_node)
    graph.add_node("architecture", architecture_node)
    graph.add_node("database", database_node)
    graph.add_node("api", api_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("chat", chat_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges("router", route_decision, {
        "requirements": "requirements",
        "chat": "chat",
    })

    graph.add_edge("requirements", "architecture")
    graph.add_edge("architecture", "database")
    graph.add_edge("database", "api")
    graph.add_edge("api", "summarizer")
    graph.add_edge("summarizer", END)
    graph.add_edge("chat", END)

    return graph.compile()


orchestrator = build_graph()


# ─────────────────────────────────────────
# Public function
# ─────────────────────────────────────────

async def run_orchestrator(user_message: str, history: list[dict]) -> dict:
    initial_state: DesignState = {
        "user_message": user_message,
        "history": history,
        "needs_design": False,
        "requirements": None,
        "architecture": None,
        "database": None,
        "api_design": None,
        "final_response": "",
    }

    result = await orchestrator.ainvoke(initial_state)

    structured = None
    if result["needs_design"]:
        structured = StructuredDesignOutput(
            requirements=result["requirements"],
            architecture=result["architecture"],
            database=result["database"],
            api_design=result["api_design"],
        )

    return {
        "response": result["final_response"],
        "structured_output": structured,
    }