from agents.llm_factory import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json, os
from models.schemas import SystemAnalystOutput, DatabaseAgentOutput, BackendLayerOutput, TestingOutput

SYSTEM_PROMPT = """You are an experienced Testing Manager for Java Spring Boot microservices.
You write thorough JUnit 5 unit tests and produce beginner-friendly error reports.

You MUST respond with ONLY valid JSON — no markdown, no explanation, no code blocks.

Exact JSON structure:
{
  "summary": "what was tested and overall result",
  "unit_tests": "full JUnit 5 + Mockito test code for all service classes",
  "test_report": "markdown report: what works, what to watch out for, how to run tests",
  "errors": [
    {
      "file": "path/to/File.java",
      "line": "line number or range",
      "description": "what happened in simple words",
      "cause": "root cause explanation for beginners"
    }
  ],
  "coverage_estimate": "estimated coverage % with explanation"
}

Unit test rules:
- @ExtendWith(MockitoExtension.class) on every test class
- @Mock for repositories, @InjectMocks for services
- Test every service method: happy path + not found + validation error
- Use @DisplayName("...") for readable test names
- Use assertThrows for exception testing
- Use verify() to confirm repository interactions
- Separate files with: // === FILE: src/test/java/com/microservice/app/service/XServiceTest.java ===

Do NOT wrap in markdown. Do NOT add any text before or after the JSON."""


async def run_testing(
    user_prompt: str,
    analyst: SystemAnalystOutput,
    database: DatabaseAgentOutput,
    backend: BackendLayerOutput,
    _ignored=None,  # kept for signature compatibility
) -> TestingOutput:
    llm = get_llm(temperature=0.1)
    context = f"""=== SYSTEM ANALYST ===
{analyst.summary}
Requirements: {json.dumps(analyst.requirements, indent=2)}

=== ENTITIES ===
{json.dumps(database.entities, indent=2)}

=== SERVICE CODE ===
{backend.service_code[:3000]}

=== CONTROLLER CODE ===
{backend.controller_code[:2000]}

=== USER REQUEST ===
{user_prompt}

Generate the complete testing JSON."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]
    response = await llm.ainvoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    data = json.loads(raw)
    return TestingOutput(**data)



# from langchain_openai import ChatOpenAI
# from langchain_core.messages import SystemMessage, HumanMessage
# import json, os
# from models.schemas import (
#     SystemAnalystOutput, DatabaseAgentOutput,
#     ServiceLayerOutput, ControllerLayerOutput, TestingOutput
# )
#
# SYSTEM_PROMPT = """You are an experienced Testing Manager for Java Spring Boot microservices.
# You write thorough unit tests and produce beginner-friendly error reports.
#
# You MUST respond with ONLY valid JSON matching this exact structure:
# {
#   "summary": "what was tested and overall result",
#   "unit_tests": "// Full JUnit 5 + Mockito test code\\n// Separate files with: // === FILE: path/FileName.java ===",
#   "test_report": "Human-readable markdown report of what works and what to watch out for",
#   "errors": [
#     {
#       "file": "path/to/File.java",
#       "line": "line number or range",
#       "description": "what happened in simple words",
#       "cause": "root cause explanation for beginners"
#     }
#   ],
#   "coverage_estimate": "estimated code coverage percentage and explanation"
# }
#
# Rules for unit tests:
# - Use JUnit 5 (@Test, @ExtendWith(MockitoExtension.class))
# - Use Mockito (@Mock, @InjectMocks, when/then/verify)
# - Test all service methods: happy path + edge cases
# - Test input validation (null, empty, invalid)
# - Test exception throwing
# - Minimum 80% coverage target
# - Add @DisplayName for readable test names
# - Separate files with: // === FILE: src/test/java/com/microservice/[name]/FileName.java ===
#
# Rules for error report:
# - Explain each potential error in simple language
# - Say WHERE it could happen (file + method)
# - Say WHY it could happen (root cause)
# - Suggest how to fix it
#
# Do NOT include any text outside the JSON."""
#
#
# async def run_testing(
#     user_prompt: str,
#     analyst: SystemAnalystOutput,
#     database: DatabaseAgentOutput,
#     service: ServiceLayerOutput,
#     controller: ControllerLayerOutput,
# ) -> TestingOutput:
#     llm = ChatOpenAI(
#         model=os.getenv("OPENAI_MODEL", "gpt-4o"),
#         temperature=0.1,
#         api_key=os.getenv("OPENAI_API_KEY"),
#     )
#     context = f"""System Summary: {analyst.summary}
# Requirements: {json.dumps(analyst.requirements, indent=2)}
#
# Entities: {json.dumps(database.entities, indent=2)}
#
# Service Layer Summary: {service.summary}
# Service Code (reference):
# {service.java_code[:2500]}
#
# Controller Layer Summary: {controller.summary}
# Controller Code (reference):
# {controller.java_code[:2000]}
#
# Original user request:
# {user_prompt}"""
#
#     messages = [
#         SystemMessage(content=SYSTEM_PROMPT),
#         HumanMessage(content=context),
#     ]
#     response = await llm.ainvoke(messages)
#     raw = response.content.strip()
#     if raw.startswith("```"):
#         raw = raw.split("```")[1]
#         if raw.startswith("json"):
#             raw = raw[4:]
#     data = json.loads(raw.strip())
#     return TestingOutput(**data)