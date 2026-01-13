from google.genai.types import Tool, FunctionDeclaration

LLM_TOOLS = [
    Tool(
        function_declarations=[
            FunctionDeclaration(
                name="task.manage",
                description=(
                    "Unified task management function for personal tasks. "
                    "Use this tool to create, update, delete, or list tasks. "
                    "Choose the appropriate action based on the user's intent."
    
                    "Do NOT invent or guess any task IDs. "
                    "Tasks must be identified using natural language descriptions provided by the user. "
                    "The backend will resolve the correct task internally.\n\n"
    
                    "For update or delete actions, extract a short descriptive phrase that uniquely "
                    "identifies the task (for example: 'finish the report', 'submit assignment'). "
                    "If multiple tasks could match, ask the user to be more specific.\n\n"
    
                    "For create actions, generate a concise title and optional description. "
                    
                    "For List action, extract a short keyword for search if the user is looking for something specific."
    
                    "Use this tool for requests such as:\n"
                    "- 'Create a task to finish the report by Friday'\n"
                    "- 'Mark the task about project documentation as done'\n"
                    "- 'Delete the task related to exam prep'\n"
                    "- 'List my tasks for this conversation'\n\n"
    
                    "If the tool returns more information than the user explicitly asked for, "
                    "summarize the relevant parts clearly."
                    
                    "If you encounter an error when using this tool, if the error is not descriptive enough for you to solve the issue, STOP and do not use the tool again and tell the user to try again later."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "update", "delete", "list"],
                            "description": (
                                "The task operation to perform. "
                                "Choose based on user intent."
                            ),
                        },
                        "query": {
                            "type": "string",
                            "description": (
                                "Short natural language description used to identify an existing task. "
                            ),
                            "nullable": True,
                        },
                        "title": {
                            "type": "string",
                            "description": (
                                "Title for a new task or updated title for an existing task."
                            ),
                            "nullable": True,
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "Optional longer description for a task."
                            ),
                            "nullable": True,
                        },
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "done"],
                            "description": (
                                "New status for the task when updating."
                            ),
                            "nullable": False,
                        },
                    },
                    "required": ["action"],
                },
            )
        ]
    )
]