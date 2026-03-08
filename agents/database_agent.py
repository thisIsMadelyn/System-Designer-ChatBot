from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import RequirementsOutput, ArchitectureOutput, DatabaseOutput
import json, os

SYSTEM_PROMPT = """
You are a Senior Database Architect specializing in MySQL and JPA/Hibernate.

Given the system requirements and architecture:
1. Identify all entities and their fields (with data types)
2. Define relationships between entities (1:1, 1:N, M:N)
3. Write complete MySQL CREATE TABLE statements
4. Generate a Mermaid ER diagram

Always respond in valid JSON matching this exact structure:
{
  "entities": [
    {
      "name": "EntityName",
      "fields": [
        {"name": "id", "type": "BIGINT", "constraints": "PRIMARY KEY AUTO_INCREMENT"}
      ]
    }
  ],
  "relationships": ["User 1--N Order : places"],
  "mysql_schema_sql": "CREATE TABLE ...",
  "erd_mermaid": "erDiagram\\n    USER { ... }",
  "summary": "..."
}

The mysql_schema_sql must be complete and runnable.
The erd_mermaid must be valid Mermaid syntax.
No markdown, no explanation outside the JSON.
"""


async def run_database_agent(
    user_message: str,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
) -> DatabaseOutput:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.1,
    )

    context = f"""
Original user request:
{user_message}

Architecture: {architecture.architecture_style}
Services: {json.dumps(architecture.services)}
Tech Stack DB: {architecture.tech_stack.get('database', 'MySQL 8')}

Functional Requirements:
{chr(10).join(f'- {r}' for r in requirements.functional_requirements)}
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
    return DatabaseOutput(**data)