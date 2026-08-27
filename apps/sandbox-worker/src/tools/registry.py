"""
Tool Registry & JSON Schema Definitions for Gemini Function Calling.
"""

from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str]


class ToolRegistry:
    """Registry of available agent execution tools and their Gemini function calling schemas."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        # 1. readFile
        self.register(
            name="readFile",
            description="Read the UTF-8 text contents of a file in the workspace repository.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path from workspace root (e.g. 'django/core/validators.py').",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional starting line number (1-indexed).",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional ending line number (1-indexed).",
                    },
                },
                "required": ["path"],
            },
        )

        # 2. writeFile
        self.register(
            name="writeFile",
            description="Create or overwrite a file with the given content.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path."},
                    "content": {"type": "string", "description": "Complete text content to write."},
                },
                "required": ["path", "content"],
            },
        )

        # 3. editHunk
        self.register(
            name="editHunk",
            description="Replace an exact target block of code with replacement code in a specified file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Target relative file path."},
                    "target_content": {"type": "string", "description": "Exact text chunk to match and replace."},
                    "replacement_content": {"type": "string", "description": "New text to substitute in place."},
                },
                "required": ["path", "target_content", "replacement_content"],
            },
        )

        # 4. runBashCommand
        self.register(
            name="runBashCommand",
            description="Execute a sandboxed bash command within the gVisor container environment with a 30s timeout.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Bash command string to execute."},
                },
                "required": ["command"],
            },
        )

        # 5. runPytest
        self.register(
            name="runPytest",
            description="Run automated pytest assertions against the repository test fixtures to verify bug resolution.",
            parameters={
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "Specific test file or directory path (e.g. 'tests/test_validators.py').",
                    },
                    "test_args": {
                        "type": "string",
                        "description": "Optional pytest flags (e.g. '-k test_regex -v').",
                    },
                },
                "required": [],
            },
        )

    def register(self, name: str, description: str, parameters: Dict[str, Any], handler: Optional[Callable] = None):
        """Register a tool with its schema definition and optional handler."""
        tool_def = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            required=parameters.get("required", []),
        )
        self._schemas[name] = tool_def
        if handler:
            self._tools[name] = handler

    def get_tool_definition(self, name: str) -> Optional[ToolDefinition]:
        return self._schemas.get(name)

    def get_gemini_declarations(self) -> List[Dict[str, Any]]:
        """Format tools as Vertex AI Gemini function declarations."""
        return [
            {
                "name": schema.name,
                "description": schema.description,
                "parameters": schema.parameters,
            }
            for schema in self._schemas.values()
        ]

    def validate_call(self, tool_name: str, arguments: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool invocation against its registered schema."""
        schema = self._schemas.get(tool_name)
        if not schema:
            return False, f"Unknown tool: '{tool_name}'. Registered tools: {list(self._schemas.keys())}"

        for req in schema.required:
            if req not in arguments:
                return False, f"Missing required parameter '{req}' for tool '{tool_name}'"

        return True, None
