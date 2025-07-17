import logging
from collections.abc import Sequence
from typing import Any
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

load_dotenv()

from . import tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-obsidian-advanced")


app = Server("mcp-obsidian-advanced")

# Tool mapping between tool constants and their handler classes
TOOL_MAPPING = {
    tools.TOOL_LIST_FILES_IN_DIR: tools.ListFilesInDirToolHandler,
    tools.TOOL_SIMPLE_SEARCH: tools.SearchToolHandler,
    tools.TOOL_PATCH_CONTENT: tools.PatchContentToolHandler,
    tools.TOOL_PUT_CONTENT: tools.PutContentToolHandler,
    tools.TOOL_APPEND_CONTENT: tools.AppendContentToolHandler,
    tools.TOOL_DELETE_FILE: tools.DeleteFileToolHandler,
    tools.TOOL_COMPLEX_SEARCH: tools.ComplexSearchToolHandler,
    tools.TOOL_BATCH_GET_FILES: tools.BatchGetFilesToolHandler,
    tools.TOOL_PERIODIC_NOTES: tools.PeriodicNotesToolHandler,
    tools.TOOL_RECENT_PERIODIC_NOTES: tools.RecentPeriodicNotesToolHandler,
    tools.TOOL_RECENT_CHANGES: tools.RecentChangesToolHandler,
    tools.TOOL_UNDERSTAND_VAULT: tools.UnderstandVaultToolHandler,
    tools.TOOL_GET_ACTIVE_NOTE: tools.GetActiveNoteToolHandler,
    tools.TOOL_OPEN_FILES: tools.OpenFilesToolHandler,
    tools.TOOL_LIST_COMMANDS: tools.ListCommandsToolHandler,
    tools.TOOL_EXECUTE_COMMANDS: tools.ExecuteCommandsToolHandler,
}

def parse_include_tools():
    """Parse the INCLUDE_TOOLS environment variable and return a set of tool names to include."""
    include_tools_env = os.getenv('INCLUDE_TOOLS', '').strip()
    
    if not include_tools_env:
        logger.info("INCLUDE_TOOLS environment variable not set or empty, including all tools")
        return set(TOOL_MAPPING.keys())
    
    # Split by comma and strip whitespace
    requested_tools = [tool.strip() for tool in include_tools_env.split(',') if tool.strip()]
    
    if not requested_tools:
        logger.info("INCLUDE_TOOLS environment variable contains no valid tool names, including all tools")
        return set(TOOL_MAPPING.keys())
    
    # Filter to only include valid tool names
    valid_tools = set()
    invalid_tools = []
    
    for tool_name in requested_tools:
        if tool_name in TOOL_MAPPING:
            valid_tools.add(tool_name)
        else:
            invalid_tools.append(tool_name)
    
    # Log warnings for unrecognized tool names
    if invalid_tools:
        logger.warning(f"Unrecognized tool names in INCLUDE_TOOLS: {', '.join(invalid_tools)}")
        logger.info(f"Available tool names: {', '.join(sorted(TOOL_MAPPING.keys()))}")
    
    # Fall back to all tools if no valid tools found
    if not valid_tools:
        logger.warning("No valid tool names found in INCLUDE_TOOLS, falling back to all tools")
        return set(TOOL_MAPPING.keys())
    
    logger.info(f"Including tools: {', '.join(sorted(valid_tools))}")
    return valid_tools

tool_handlers = {}
def add_tool_handler(tool_class: tools.ToolHandler):
    global tool_handlers

    tool_handlers[tool_class.name] = tool_class

def get_tool_handler(name: str) -> tools.ToolHandler | None:
    if name not in tool_handlers:
        return None
    
    return tool_handlers[name]

def register_tools():
    """Register the selected tools with the server."""
    tools_to_include = parse_include_tools()
    
    registered_count = 0
    for tool_name in tools_to_include:
        if tool_name in TOOL_MAPPING:
            handler_class = TOOL_MAPPING[tool_name]
            handler_instance = handler_class()
            add_tool_handler(handler_instance)
            registered_count += 1
            logger.debug(f"Registered tool: {tool_name}")
    
    logger.info(f"Successfully registered {registered_count} tools")

# Register tools based on INCLUDE_TOOLS environment variable
register_tools()

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""

    return [th.get_tool_description() for th in tool_handlers.values()]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for command line run."""
    
    if not isinstance(arguments, dict):
        raise RuntimeError("arguments must be dictionary")


    tool_handler = get_tool_handler(name)
    if not tool_handler:
        raise ValueError(f"Unknown tool: {name}")

    try:
        return tool_handler.run_tool(arguments)
    except Exception as e:
        logger.error(str(e))
        raise RuntimeError(f"Caught Exception. Error: {str(e)}")


async def async_main():

    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

def main():
    import asyncio
    asyncio.run(async_main())
