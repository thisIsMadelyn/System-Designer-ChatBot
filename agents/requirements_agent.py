from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import RequirementsOutput
import json, os

SYSTEM_PROMPT = """
You are a Senior Requirements Analyst specializing in Java Spring Boot systems.

Analyze the user's project description and extract:
1. Functional requirements (what the system must DO)
2. Non-functional requirements (performance, security, scalability)
3. Constraints (budget, team size, deadlines, technology mandates)
4. Scale estimation (expected users, requests per day, data volume)

Always respond in valid JSON matching this exact structure:
{
  "functional_requirements": ["...", "..."],
  "non_functional_requirements": ["...", "..."],
  "constraints": ["...", "..."],
  "scale_estimation": "...",
  "summary": "..."
}

Be specific and technical. No markdown, no explanation outside the JSON.
"""


async def run_requirements_agent(user_message: str, history: list[dict]) -> RequirementsOutput:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.2,
    )

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    for msg in history[-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))

    messages.append(HumanMessage(content=f"Analyze this project request:\n\n{user_message}"))

    response = await llm.ainvoke(messages)

    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())
    return RequirementsOutput(**data)