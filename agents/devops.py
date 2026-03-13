
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json, os
from models.schemas import SystemAnalystOutput, ArchitectOutput, DevOpsOutput

SYSTEM_PROMPT = """You are a DevOps Engineer responsible for containerizing Java Spring Boot microservices.
You create production-ready Docker configurations.

You MUST respond with ONLY valid JSON matching this exact structure:
{
  "summary": "brief description of the containerization setup",
  "dockerfile": "# Multi-stage Dockerfile content here",
  "docker_compose": "# docker-compose.yml content here",
  "dockerignore": "# .dockerignore content here",
  "readme": "# README.md with build and run instructions"
}

Rules for Dockerfile:
- Multi-stage build: stage 1 = maven:3.9-eclipse-temurin-21 for build, stage 2 = eclipse-temurin:21-jre-alpine for runtime
- Layer caching: copy pom.xml and download dependencies first
- Run as non-root user (create 'app user')
- Add HEALTHCHECK
- Add LABELs for metadata
- Set memory limits via JAVA_OPTS

Rules for docker-compose.yml:
- App service with proper environment variables
- Volume for SQLite data persistence
- Health check
- Port mapping
- Restart policy

Rules for README:
- Prerequisites section
- Build instructions
- Run instructions
- API endpoints list
- Environment variables table
- Swagger UI URL

Do NOT include any text outside the JSON."""

# απο τον analyst παίρνει tech_stack, (java edition)
# απο τον architect παίρνει tech_version (ακριβείς εκδόσεις)
async def run_devops(
    user_prompt: str,
    analyst: SystemAnalystOutput, # απο τον analyst παίρνει το #
    architect: ArchitectOutput,
) -> DevOpsOutput:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    context = f"""System Analyst: {analyst.summary}
Tech Stack: {json.dumps(analyst.tech_stack, indent=2)}
Tech Versions: {json.dumps(architect.tech_versions, indent=2)}

Package Structure:
{architect.package_structure}

Original user request:
{user_prompt}"""

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
    return DevOpsOutput(**data)