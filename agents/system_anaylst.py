from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json, os
from models.schemas import SystemAnalystOutput

SYSTEM_PROMPT = """You are an experienced System Analyst and System Designer specializing in Java microservices.
Your job is to analyze the user's requirements and produce a structured analysis.

You MUST respond with ONLY valid JSON matching this exact structure:
{
  "summary": "brief overview of what we are building",
  "requirements": ["requirement 1", "requirement 2", ...],
  "tech_stack": {
    "language": "Java 21",
    "framework": "Spring Boot 3.2",
    "database": "SQLite3",
    "build": "Maven",
    "containerization": "Docker"
  },
  "agent_plan": [
    "System Architect: design package structure and UML diagrams",
    "Database Agent: create JPA entities and repositories",
    "Service Layer: implement business logic and DTOs",
    "Controller Layer: implement REST API and Swagger",
    "DevOps Engineer: create Dockerfile and docker-compose",
    "Testing Manager: write unit tests and error report"
  ]
}

Be specific. Extract ALL requirements from the user's description.
Do NOT include any text outside the JSON."""


async def run_system_analyst(user_prompt: str) -> SystemAnalystOutput:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze these requirements and produce the JSON:\n\n{user_prompt}"),
    ]
    response = await llm.ainvoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    return SystemAnalystOutput(**data)