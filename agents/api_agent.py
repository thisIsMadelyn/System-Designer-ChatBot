from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import (
    RequirementsOutput, ArchitectureOutput, DatabaseOutput, ApiDesignOutput
)
import json, os

SYSTEM_PROMPT = """
You are a Senior API Architect specializing in Spring Boot REST APIs, Spring Security with JWT, and Docker.

Given the full system design, you will:
1. Design all REST endpoints (method, path, request body, response, auth required)
2. Provide Spring Security JWT configuration description
3. Generate a Mermaid sequence diagram showing the main API flow
4. Generate a Docker Compose configuration for all services

Always respond in valid JSON matching this exact structure:
{
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/auth/login",
      "description": "...",
      "request_body": {},
      "response": {},
      "auth_required": false,
      "roles": []
    }
  ],
  "spring_security_config": "...",
  "api_mermaid_diagram": "sequenceDiagram\\n ...",
  "docker_compose_snippet": "version: '3.8'\\n ...",
  "summary": "..."
}

No markdown, no explanation outside the JSON.
"""


async def run_api_agent(
    user_message: str,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    database: DatabaseOutput,
) -> ApiDesignOutput:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.2,
    )

    context = f"""
Original user request:
{user_message}

Architecture Style: {architecture.architecture_style}
Services: {json.dumps(architecture.services)}
Tech Stack: {json.dumps(architecture.tech_stack)}

Database Entities:
{json.dumps([e['name'] for e in database.entities])}

Functional Requirements:
{chr(10).join(f'- {r}' for r in requirements.functional_requirements)}

Constraints:
{chr(10).join(f'- {c}' for c in requirements.constraints)}
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    response = await llm.ainvoke(messages)

    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())
    return ApiDesignOutput(**data)