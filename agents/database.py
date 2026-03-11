from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json, os
from models.schemas import SystemAnalystOutput, ArchitectOutput, DatabaseAgentOutput

SYSTEM_PROMPT = """You are a Backend Developer specializing in Java data persistence with Spring Data JPA and SQLite3.

You MUST respond with ONLY valid JSON — no markdown, no explanation, no code blocks.

Exact JSON structure:
{
  "summary": "brief description of the data layer",
  "entities": [
    {
      "name": "EntityName",
      "table": "table_name",
      "fields": [
        {"name": "id", "type": "Long", "annotations": ["@Id", "@GeneratedValue(strategy = GenerationType.IDENTITY)"]},
        {"name": "name", "type": "String", "annotations": ["@NotNull", "@Size(max = 255)"]}
      ]
    }
  ],
  "relationships": [
    "User (1) --- (*) Order : OneToMany / ManyToOne"
  ],
  "java_code": "full Java source code for all entities and repositories",
  "application_properties": "full application.properties content"
}

Java code rules:
- Use Java 21 + Spring Boot 3.2
- Use Lombok: @Data @Builder @NoArgsConstructor @AllArgsConstructor on every entity
- Use @Entity @Table(name="...") on every entity
- Every entity must have: @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
- Add @CreatedDate private LocalDateTime createdAt; and @LastModifiedDate private LocalDateTime updatedAt; on every entity
- Add @EntityListeners(AuditingEntityListener.class) on every entity
- Use @OneToMany(cascade = CascadeType.ALL, fetch = FetchType.LAZY) for collections
- Use @ManyToOne(fetch = FetchType.LAZY) @JoinColumn for references
- Add @NotNull @Size @Email @Min @Max validations where appropriate
- Every repository: public interface XRepository extends JpaRepository<X, Long>
- Add @EnableJpaAuditing on a @Configuration class
- Separate each file with exactly this comment: // === FILE: src/main/java/com/microservice/app/PACKAGE/ClassName.java ===

application.properties rules:
- spring.datasource.url=jdbc:sqlite:./data/app.db
- spring.datasource.driver-class-name=org.sqlite.JDBC
- spring.jpa.database-platform=org.hibernate.community.dialect.SQLiteDialect
- spring.jpa.hibernate.ddl-auto=update
- spring.jpa.show-sql=false
- spring.data.jpa.repositories.enabled=true
- server.port=8080

Do NOT wrap in markdown. Do NOT add any text before or after the JSON."""


async def run_database_agent(
    user_prompt: str,
    analyst: SystemAnalystOutput,
    architect: ArchitectOutput,
) -> DatabaseAgentOutput:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    context = f"""=== SYSTEM ANALYST OUTPUT ===
Summary: {analyst.summary}
Requirements:
{chr(10).join(f'- {r}' for r in analyst.requirements)}
Tech Stack: {json.dumps(analyst.tech_stack, indent=2)}

=== ARCHITECT OUTPUT ===
Package Structure:
{architect.package_structure}

UML Class Diagram:
{architect.uml_class}

Design Patterns: {', '.join(architect.design_patterns)}

=== USER REQUEST ===
{user_prompt}

Now generate the complete database layer JSON."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    # Strip markdown if model wraps anyway
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    data = json.loads(raw)
    return DatabaseAgentOutput(**data)