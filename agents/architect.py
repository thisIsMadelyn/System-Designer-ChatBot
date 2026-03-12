from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json, os
from models.schemas import SystemAnalystOutput, ArchitectOutput

SYSTEM_PROMPT = """You are an experienced System Architect responsible for designing Java microservice structure.
You follow DDD principles and microservices best practices.

You MUST respond with ONLY valid JSON matching this exact structure:
{
  "summary": "brief architecture overview",
  "package_structure": "ASCII tree of the full package structure",
  "design_patterns": ["Entity", "Repository", "Service", "Controller", "DTO", "GlobalExceptionHandler"],
  "uml_class": "@startuml\\n...PlantUML class diagram...\\n@enduml",
  "uml_sequence": "@startuml\\n...PlantUML sequence diagram for main flow...\\n@enduml",
  "tech_versions": {
    "java": "21",
    "spring_boot": "3.2.x",
    "sqlite": "latest",
    "maven": "3.9.x",
    "springdoc_openapi": "2.3.x",
    "lombok": "latest",
    "mapstruct": "1.5.x"
  }
}

The package structure must follow this pattern:
com.microservice.[name]/
  entity/
  repository/
  service/ (interface + impl/)
  controller/
  dto/ (request/ + response/)
  exception/
  config/
  mapper/

Do NOT include any text outside the JSON."""

# παίρνει content απο τον προηγούμενο agent

async def run_architect(user_prompt: str, analyst: SystemAnalystOutput) -> ArchitectOutput:

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    # δέχεται το output του system analyst και το χρησιμοποιεί ως παράμετρο
    # για να φτιάξει πιο σύνθετο υλικό
    context = f"""Requirements from System Analyst:
    Summary: {analyst.summary}
    Requirements: {json.dumps(analyst.requirements, indent=2)}
    Tech Stack: {json.dumps(analyst.tech_stack, indent=2)}

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
    return ArchitectOutput(**data)