from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import RequirementsOutput, ArchitectureOutput
import json, os

SYSTEM_PROMPT = """
You are a Senior Software Architect specializing in Java Spring Boot microservices.

Given the analyzed requirements, design the system architecture:
1. Decide: Microservices vs Monolith (with clear justification)
2. Define each service/module with its responsibility
3. Explain tradeoffs of the chosen architecture
4. Define the full tech stack

Always respond in valid JSON matching this exact structure:
{
  "architecture_style": "Microservices" | "Monolith" | "Modular Monolith",
  "services": [
    {"name": "ServiceName", "responsibility": "...", "spring_boot_module": "..."}
  ],
  "tradeoffs": ["Pro: ...", "Con: ..."],
  "tech_stack": {
    "backend": "Spring Boot 3.x",
    "database": "MySQL 8",
    "auth": "Spring Security + JWT",
    "containerization": "Docker + Docker Compose",
    "other": []
  },
  "summary": "..."
}

No markdown, no explanation outside the JSON.
"""


async def run_architecture_agent(
    user_message: str,
    requirements: RequirementsOutput,
) -> ArchitectureOutput:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.2,
    )

    context = f"""
Original user request:
{user_message}

Requirements Analysis:
- Functional: {', '.join(requirements.functional_requirements)}
- Non-Functional: {', '.join(requirements.non_functional_requirements)}
- Constraints: {', '.join(requirements.constraints)}
- Scale: {requirements.scale_estimation}
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
    return ArchitectureOutput(**data)