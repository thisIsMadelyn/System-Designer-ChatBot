## System Designer Assistant

For the whole documentation and specs : [Check out this](https://github.com/thisIsMadelyn/GenAI-Designer-Specs/tree/main)

### Pipeline Diagram
```angular2html
user_prompt
    |
    V
analyst (user_prompt)
    | summary, requirements, tech_stach
    V
architect (user_promt, analyst)
    | package_structure, uml, tech_versions
    V
database (user_prompt, analyst, architect)
    | entities, java_code, properties
    V
backend (user_prompt, analyst, architect, database)
    | service_code, controller_code, dto_code
    V
devops (user_prompt, analyst, architect)
    | dockerfile, docker_compose, readme
    V
testing (user_prompt, analyst, database, backed)
    | unit_tests, test_report, errors
    V
summarizer -> final_response
```