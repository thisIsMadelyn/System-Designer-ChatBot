from langgraph.graph import StateGraph, END
from agents.llm_factory import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict, Optional
import json, os

from models.schemas import (
    MicroserviceOutput,
    SystemAnalystOutput, ArchitectOutput, DatabaseAgentOutput,
    BackendLayerOutput, DevOpsOutput, TestingOutput,
    StructuredDesignOutput, # na to vgalo
)
from agents.system_anaylst        import run_system_analyst
from agents.architect             import run_architect
from agents.database              import run_database_agent
from agents.backend_layer         import run_backend_layer
from agents.devops                import run_devops
from agents.testing               import run_testing

USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"


# ── State ─────────────────────────────────────────────────────

class DesignState(TypedDict):
    user_message:   str
    history:        list[dict]
    needs_design:   bool
    system_analyst: Optional[SystemAnalystOutput]
    architect:      Optional[ArchitectOutput]
    database:       Optional[DatabaseAgentOutput]
    backend_layer:  Optional[BackendLayerOutput]
    devops:         Optional[DevOpsOutput]
    testing:        Optional[TestingOutput]
    final_response: str


# ── Mock ──────────────────────────────────────────────────────

MOCK_OUTPUT = MicroserviceOutput(
    system_analyst=SystemAnalystOutput(
        summary="E-Commerce microservice with product catalog and order management",
        requirements=["CRUD for products", "Order creation", "User authentication", "SQLite persistence"],
        tech_stack={"language": "Java 21", "framework": "Spring Boot 3.2", "database": "SQLite3", "build": "Maven"},
        agent_plan=["Architect", "Database", "Backend Layer", "DevOps", "Testing"],
    ),
    architect=ArchitectOutput(
        summary="Layered DDD architecture",
        package_structure="com.microservice.app/\n  entity/\n  repository/\n  service/\n    impl/\n  controller/\n  dto/\n    request/\n    response/\n  exception/\n  config/",
        design_patterns=["Entity", "Repository", "Service", "Controller", "DTO", "GlobalExceptionHandler"],
        uml_class="@startuml\nclass Product { +Long id\n+String name\n+BigDecimal price }\n@enduml",
        uml_sequence="@startuml\nClient -> Controller: POST /api/v1/products\nController -> Service: create(req)\nService -> Repository: save(entity)\nRepository --> Service: saved\nService --> Controller: response\nController --> Client: 201\n@enduml",
        tech_versions={"java": "21", "spring_boot": "3.2.x", "sqlite": "latest", "maven": "3.9.x"},
    ),
    database=DatabaseAgentOutput(
        summary="Product and Order entities with SQLite",
        entities=[
            {"name": "Product", "table": "products", "fields": [
                {"name": "id", "type": "Long", "annotations": ["@Id", "@GeneratedValue"]},
                {"name": "name", "type": "String", "annotations": ["@NotNull"]},
                {"name": "price", "type": "BigDecimal", "annotations": ["@NotNull"]},
            ]},
        ],
        relationships=["Order (1) --- (*) Product : ManyToMany"],
        java_code="// === FILE: src/main/java/com/microservice/app/entity/Product.java ===\npackage com.microservice.app.entity;\n// ... full entity code",
        application_properties="spring.datasource.url=jdbc:sqlite:./data/app.db\nspring.datasource.driver-class-name=org.sqlite.JDBC\nspring.jpa.hibernate.ddl-auto=update",
    ),
    backend_layer=BackendLayerOutput(
        summary="Full backend: DTOs, Services, Controllers with Swagger",
        dto_code="// === FILE: src/main/java/com/microservice/app/dto/request/ProductRequest.java ===\n// ... DTO code",
        service_code="// === FILE: src/main/java/com/microservice/app/service/ProductService.java ===\n// ... service code",
        exception_code="// === FILE: src/main/java/com/microservice/app/exception/GlobalExceptionHandler.java ===\n// ... exception code",
        controller_code="// === FILE: src/main/java/com/microservice/app/controller/ProductController.java ===\n// ... controller code",
        swagger_config="// OpenAPI config — Swagger UI at /swagger-ui.html",
    ),
    devops=DevOpsOutput(
        summary="Multi-stage Docker build",
        dockerfile="FROM maven:3.9-eclipse-temurin-21 AS build\nWORKDIR /app\nCOPY pom.xml .\nRUN mvn dependency:resolve\nCOPY src ./src\nRUN mvn package -DskipTests\n\nFROM eclipse-temurin:21-jre-alpine\nRUN adduser -D appuser\nUSER appuser\nCOPY --from=build /app/target/*.jar app.jar\nENTRYPOINT [\"java\",\"-jar\",\"app.jar\"]",
        docker_compose="version: '3.8'\nservices:\n  app:\n    build: .\n    ports: ['8080:8080']\n    volumes: ['./data:/app/data']",
        dockerignore="target/\n.git/\n*.md",
        readme="# Microservice\n## Run\n```bash\ndocker-compose up --build\n```\n## Swagger\nhttp://localhost:8080/swagger-ui.html",
    ),
    testing=TestingOutput(
        summary="Unit tests — estimated 85% coverage",
        unit_tests="// === FILE: src/test/java/com/microservice/app/ProductServiceTest.java ===\n@ExtendWith(MockitoExtension.class)\nclass ProductServiceTest { }",
        test_report="## Test Report\n✅ ProductService CRUD — PASS\n✅ Input validation — PASS",
        errors=[],
        coverage_estimate="~85%",
    ),
    final_summary="✅ Mock design complete. Set USE_MOCK=false for real GPT-4o output.",
)


# ── Nodes ─────────────────────────────────────────────────────

async def router_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        return {**state, "needs_design": True}
    llm = get_llm(temperature=0)
    response = await llm.ainvoke([HumanMessage(
        content=f'User message: "{state["user_message"]}"\nReply with ONLY: "DESIGN" or "CHAT"'
    )])
    return {**state, "needs_design": response.content.strip().upper() == "DESIGN"}


async def analyst_node(state: DesignState) -> DesignState:
    if USE_MOCK: return {**state, "system_analyst": MOCK_OUTPUT.system_analyst}
    result = await run_system_analyst(state["user_message"])
    return {**state, "system_analyst": result}


async def architect_node(state: DesignState) -> DesignState:
    if USE_MOCK: return {**state, "architect": MOCK_OUTPUT.architect}
    # καλω την συναρτηση run_architect απο το architect.py αρχείο
    result = await run_architect(state["user_message"], state["system_analyst"])
    return {**state, "architect": result}


async def database_node(state: DesignState) -> DesignState:
    if USE_MOCK: return {**state, "database": MOCK_OUTPUT.database}
    result = await run_database_agent(state["user_message"], state["system_analyst"], state["architect"])
    return {**state, "database": result}


async def backend_node(state: DesignState) -> DesignState:
    if USE_MOCK: return {**state, "backend_layer": MOCK_OUTPUT.backend_layer}
    result = await run_backend_layer(state["user_message"], state["system_analyst"], state["architect"], state["database"])
    return {**state, "backend_layer": result}


async def devops_node(state: DesignState) -> DesignState:
    if USE_MOCK: return {**state, "devops": MOCK_OUTPUT.devops}
    result = await run_devops(state["user_message"], state["system_analyst"], state["architect"])
    return {**state, "devops": result}


async def testing_node(state: DesignState) -> DesignState:
    if USE_MOCK: return {**state, "testing": MOCK_OUTPUT.testing}
    result = await run_testing(
        state["user_message"], state["system_analyst"], state["database"],
        state["backend_layer"], state["backend_layer"],
    )
    return {**state, "testing": result}


async def summarizer_node(state: DesignState) -> DesignState:
    if USE_MOCK: return {**state, "final_response": MOCK_OUTPUT.final_summary}
    llm = get_llm(temperature=0.3)
    context = f"""Summarize this complete Java microservice design in clear markdown:
System: {state['system_analyst'].summary}
Architecture: {state['architect'].summary}
Database: {state['database'].summary}
Backend: {state['backend_layer'].summary}
DevOps: {state['devops'].summary}
Testing: {state['testing'].summary}
Coverage: {state['testing'].coverage_estimate}
Errors: {len(state['testing'].errors)}"""
    response = await llm.ainvoke([HumanMessage(content=context)])
    return {**state, "final_response": response.content}


async def chat_node(state: DesignState) -> DesignState:
    if USE_MOCK:
        return {**state, "final_response": "Mock chat — describe a Java microservice and I'll run the full pipeline!"}
    llm = get_llm(temperature=0.5)
    messages = [SystemMessage(content="You are a Java Spring Boot microservice expert.")]
    for msg in state["history"][-6:]:
        if msg["role"] == "user": messages.append(HumanMessage(content=msg["content"]))
        else: messages.append(SystemMessage(content=msg["content"]))
    messages.append(HumanMessage(content=state["user_message"]))
    response = await llm.ainvoke(messages)
    return {**state, "final_response": response.content}


def route_decision(state: DesignState) -> str:
    return "analyst" if state["needs_design"] else "chat"


# ── Graph ─────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(DesignState)

    graph.add_node("router",     router_node)
    graph.add_node("analyst",    analyst_node)
    graph.add_node("architect",  architect_node)
    graph.add_node("database",   database_node)
    graph.add_node("backend",    backend_node)
    graph.add_node("devops",     devops_node)
    graph.add_node("testing",    testing_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("chat",       chat_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_decision, {
        "analyst": "analyst",
        "chat":    "chat",
    })
    graph.add_edge("analyst",    "architect")
    graph.add_edge("architect",  "database")
    graph.add_edge("database",   "backend")
    graph.add_edge("backend",    "devops")
    graph.add_edge("devops",     "testing")
    graph.add_edge("testing",    "summarizer")
    graph.add_edge("summarizer", END)
    graph.add_edge("chat",       END)

    return graph.compile()


orchestrator = build_graph()


# ── Public API ────────────────────────────────────────────────

# agents/orchestrator.py
# ΑΛΛΑΞΕ ΜΟΝΟ την τελευταία συνάρτηση run_orchestrator — τα υπόλοιπα μένουν ίδια

async def run_orchestrator(user_message: str, history: list[dict]) -> dict:
    """
    Τρέχει το 6-agent pipeline και επιστρέφει:
    {
        "response": str,                  # markdown summary για chat
        "structured_output": dict | None  # πλήρες output για MySQL + frontend
    }
    """
    initial: DesignState = {
        "user_message":   user_message,
        "history":        history,
        "needs_design":   False,
        "system_analyst": None,
        "architect":      None,
        "database":       None,
        "backend_layer":  None,
        "devops":         None,
        "testing":        None,
        "final_response": "",
    }

    result = await orchestrator.ainvoke(initial)

    # Αν δεν έτρεξε design pipeline, επιστρέφουμε μόνο chat response
    if not result["needs_design"]:
        return {
            "response":          result["final_response"],
            "structured_output": None,
        }

    # Φτιάχνουμε το MicroserviceOutput Pydantic object
    structured = MicroserviceOutput(
        system_analyst = result["system_analyst"],
        architect      = result["architect"],
        database       = result["database"],
        backend_layer  = result["backend_layer"],
        devops         = result["devops"],
        testing        = result["testing"],
        final_summary  = result["final_response"],
    )

    # .model_dump() το μετατρέπει σε dict ώστε να αποθηκευτεί ως JSON στη MySQL
    # και να σταλεί κατευθείαν στο frontend
    return {
        "response":          result["final_response"],
        "structured_output": structured.model_dump(),
    }