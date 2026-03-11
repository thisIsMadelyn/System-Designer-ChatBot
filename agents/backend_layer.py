from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json, os
from models.schemas import SystemAnalystOutput, ArchitectOutput, DatabaseAgentOutput, BackendLayerOutput

SYSTEM_PROMPT = """You are a senior Backend Developer implementing the complete backend of a Java Spring Boot microservice.
You implement the Service Layer AND the Controller Layer in one pass.

You MUST respond with ONLY valid JSON — no markdown, no explanation, no code blocks.

Exact JSON structure:
{
  "summary": "brief description of the full backend implementation",
  "dto_code": "all DTO classes (request and response) for every entity",
  "service_code": "all Service interfaces and ServiceImpl classes",
  "exception_code": "custom exceptions + GlobalExceptionHandler",
  "controller_code": "all REST controllers with Swagger annotations",
  "swagger_config": "OpenAPIConfig class + any extra application.properties lines for Swagger"
}

Service Layer rules:
- Create XRequest (input DTO) and XResponse (output DTO) for every entity
- Create XService interface and XServiceImpl for every entity
- @Service @Transactional @Slf4j on every ServiceImpl
- Manual mapping Entity <-> DTO (no MapStruct needed)
- Throw ResourceNotFoundException when entity not found
- Add input validation in service before saving
- Add JavaDoc on all public methods

Controller Layer rules:
- @RestController @RequestMapping("/api/v1/...") on every controller
- Implement: GET all (paginated), GET by id, POST create, PUT update, DELETE
- Use @Valid on @RequestBody
- Return ResponseEntity<> with correct HTTP status codes:
  GET list → 200, GET one → 200, POST → 201, PUT → 200, DELETE → 204
- Add @Operation(summary="...") and @ApiResponse on every endpoint
- Add @CrossOrigin(origins = "*") on every controller
- Add request logging with SLF4J

Exception handling rules:
- ResourceNotFoundException extends RuntimeException
- ValidationException extends RuntimeException
- GlobalExceptionHandler uses @RestControllerAdvice
- Returns { "status": int, "error": string, "message": string, "timestamp": string }

Swagger config rules:
- @Configuration class with @Bean OpenAPI
- Title, description, version from project info
- springdoc.api-docs.path=/api-docs
- springdoc.swagger-ui.path=/swagger-ui.html

Separate each file with: // === FILE: src/main/java/com/microservice/app/PACKAGE/ClassName.java ===

Do NOT wrap in markdown. Do NOT add any text before or after the JSON."""


async def run_backend_layer(
    user_prompt: str,
    analyst: SystemAnalystOutput,
    architect: ArchitectOutput,
    database: DatabaseAgentOutput,
) -> BackendLayerOutput:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    context = f"""=== SYSTEM ANALYST OUTPUT ===
Summary: {analyst.summary}
Requirements:
{chr(10).join(f'- {r}' for r in analyst.requirements)}

=== ARCHITECT OUTPUT ===
Package Structure:
{architect.package_structure}
UML Sequence:
{architect.uml_sequence}

=== DATABASE AGENT OUTPUT ===
Entities:
{json.dumps(database.entities, indent=2)}
Relationships: {json.dumps(database.relationships, indent=2)}

Database Java Code:
{database.java_code}

=== USER REQUEST ===
{user_prompt}

Now generate the complete backend layer JSON."""

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
    return BackendLayerOutput(**data)