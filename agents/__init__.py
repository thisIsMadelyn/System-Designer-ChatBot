from .orchestrator import run_orchestrator

# Το μοτίβο που επαναλαμβάνεται σε όλους τους agents
# SYSTEM_PROMPT (τι agent είσαι και τι είδους JSON επιστρέφεις)
#  |
#  V
# run_agent (user_prompt, output από προηγούμενους agents)
#  |
#  V
# context = συνδυασμός user_prompt και output προηγούμενων agents
#  |
#  V
# llm.ainvoke([SystemMessage, HumanMessage(context)])
#  |
#  V
# καθαρισμός των markdown
#  |
#  V
# json.loads ->  PydanticModel(data)#
