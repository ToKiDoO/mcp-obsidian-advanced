# Advanced MCP Tools for Obsidian

<p>
  <a href="https://mseep.ai/app/tokidoo-mcp-obsidian-advanced">
    <img src="https://mseep.net/pr/tokidoo-mcp-obsidian-advanced-badge.png" alt="MseeP.ai Security Assessment Badge">
  </a>&nbsp;&nbsp;
  <a href="https://glama.ai/mcp/servers/@ToKiDoO/mcp-obsidian-advanced">
    <img src="https://glama.ai/mcp/servers/@ToKiDoO/mcp-obsidian-advanced/badge" alt="Glama MCP Server Badge" width="380" height="200">
  </a>&nbsp;&nbsp;
  <a href="https://smithery.ai/@ToKiDoO/mcp-obsidian-advanced">
    <img src="https://smithery.ai/badge/@ToKiDoO/mcp-obsidian-advanced" alt="Smithery Badge" height="56">
  </a>
</p>



Advanced MCP server for interacting with Obsidian via the Local REST API community plugin. It empowers AI agents (like Claude) to deeply understand your vault's structure, links, and content—beyond basic read/write operations.

Key advanced features, powered by the obsidiantools library:
- Vault tree structure discovery to map your note hierarchy
- NetworkX graph analysis of note connections for LLM-friendly insights
- Execution of Obsidian commands directly from AI
- Batch file reading with metadata and link details
- Access to your currently active note for real-time context
- Opening notes/files in new Obsidian leaves for seamless editing

This setup lets AI agents work alongside you, boosting productivity by efficiently navigating and enhancing your knowledge base.

## Components

### Tools

The server implements multiple tools to interact with Obsidian:

#### Core File Operations

- `obsidian_list_files_in_dir`: Lists all files and directories in a specific Obsidian directory
- `obsidian_batch_get_files`: Return the contents and metadata of one or more notes (.md files) in your vault
- `obsidian_put_file`: Create a new file in your vault or update the content of an existing one
- `obsidian_append_to_file`: Append content to a new or existing file in the vault
- `obsidian_patch_file`: Insert content into an existing note relative to a heading, block reference, or frontmatter field
- `obsidian_delete_file`: Delete a file or directory from your vault

#### Search Operations

- `obsidian_simple_search`: Simple search for documents matching a specified text query across all files in the vault
- `obsidian_complex_search`: Complex search for documents using a JsonLogic query with support for 'glob' and 'regexp' pattern matching

#### Note Management

- `obsidian_get_active_note`: Get the content and metadata of the currently active note in Obsidian
- `obsidian_periodic_notes`: Get current periodic note for the specified period (daily, weekly, monthly, quarterly, yearly)
- `obsidian_recent_periodic_notes`: Get most recent periodic notes for the specified period type
- `obsidian_recent_changes`: Get recently modified files in the vault
	- NOTE: This tool requires the `Dataview` community plugin to function. Make sure to install the Dataview plugin in your vault.

#### Vault Analysis

- `obsidian_understand_vault`: Get a comprehensive understanding of the vault structure including directory tree and NetworkX graph of note connections
- `obsidian_open_files`: Open one or more files in the vault in a new leaf
- `obsidian_list_commands`: List all available commands you can run in obsidian interface
- `obsidian_execute_commands`: Execute one or more commands in obsidian interface

### Example prompts

Its good to first instruct Claude (or any other MCP client) to use Obsidian. Then it will always call the tool. For instance, 

The use prompts like this:
- *"Expand on the Marketing section of the report I'm currently working on in obsidian"*
	- Claude will use `obsidian_get_active_note`, read it, then edit the note.
- *"Search for all files where Azure CosmosDb is mentioned and quickly explain to me the context in which it is mentioned"*
- *"Summarize the last meeting notes and put them into a new note 'summary meeting.md'. Add an introduction so that I can send it via email."*

## Configuration

### Environment Variables

For this MCP server, there are **2 required environment variables** that need to be configured:

* `OBSIDIAN_API_KEY`: Obtain this by installing the Obsidian REST API plugin, and go into settings.
* `OBSIDIAN_VAULT_PATH`: The absolute path to your vault must be set in order for tools (e.g. `obsidian_understand_vault`) to function properly.

Additionally, there are **3 optional environment variables** that could be altered:

* `OBSIDIAN_HOST`: Could be changed in the Obsidian REST API plugin settings. Defaults to `127.0.0.1` as per the plugin's default settings.
* `OBSIDIAN_PORT`: Could be changed in the Obsidian REST API plugin settings. Defaults to `27124` as per the plugin's default settings.
* `INCLUDE_TOOLS`: This variable controls which tools would be available for use.
	* Write the name of the tool(s) you want to include (name listed above), separated by commas.
	* For instance, if you only want the `obsidian_understand_vault` and `obsidian_simple_search` tool, you would set `INCLUDE_TOOLS="obsidian_understand_vault,obsidian_simple_search"` in the .env or in the server config.

There are two ways to configure the environment with the Obsidian REST API Key. 

1. Add to server config (PREFERRED):

```json
{
  "mcp-obsidian-advanced": {
    "command": "uvx",
    "args": [
      "mcp-obsidian-advanced"
    ],
    "env": {
      "OBSIDIAN_API_KEY": "%3Cyour_api_key_here%3E",
      "OBSIDIAN_HOST": "<your_obsidian_host>",
      "OBSIDIAN_PORT": "<your_obsidian_port>",
      "OBSIDIAN_VAULT_PATH": "</path/to/your/vault>",
      "INCLUDE_TOOLS": ""
    }
  }
}
```

> Sometimes Claude has issues detecting the location of uv / uvx. You can use `which uvx` to find and paste the full path in above config in such cases.

2. Create a `.env` file in the working directory with the following variables (only `OBSIDIAN_API_KEY` and `OBSIDIAN_VAULT_PATH` are required):

```
OBSIDIAN_API_KEY=your_api_key_here
OBSIDIAN_HOST=your_obsidian_host
OBSIDIAN_PORT=your_obsidian_port
OBSIDIAN_VAULT_PATH=/path/to/your/vault
INCLUDE_TOOLS=name_of_tool1,name_of_tool2,...
```

> Note: You can find the API key, Host and Port in the Obsidian plugin config
> Default port is 27124 if not specified
> Default host is 127.0.0.1 if not specified

## Quickstart

### Install

### Installing via Smithery

To install Advanced Obsidian MCP Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@ToKiDoO/mcp-obsidian-advanced):

```bash
npx -y @smithery/cli install @ToKiDoO/mcp-obsidian-advanced --client claude
```

#### Obsidian REST API

You need the Obsidian REST API community plugin running: https://github.com/coddingtonbear/obsidian-local-rest-api
* You can install it by going to "Community Plugins" in Obsidian, search it up.

Install and enable it in the settings and copy the api key.

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

Published Servers Configuration:
  
```json
{
  "mcpServers": {
    "mcp-obsidian-advanced": {
      "command": "uvx",
      "args": [
        "mcp-obsidian-advanced"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "<your_api_key_here>",
        "OBSIDIAN_VAULT_PATH": "/path/to/your/vault/"
      }
    }
  }
}
```

Development/Unpublished Servers Configuration
  
```json
{
  "mcpServers": {
    "mcp-obsidian": {
      "command": "uv",
      "args": [
        "--directory",
        "/dir/to/mcp-obsidian-advanced",
        "run",
        "mcp-obsidian"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "<your_api_key_here>",
        "OBSIDIAN_VAULT_PATH": "/path/to/your/vault/"
      }
    }
  }
}
```


## Development

### Additional Documentation for obsidiantools Library and Obsidian REST API

Additional documentation for the obsidiantools library and Obsidian REST API can be found in the `docs` directory.

* `obsidiantools_in_15_minutes_documentation.md` is a ipynb file that demonstrates use cases for obsidiantools.
* `obsidian_rest_api_documentation.yaml` is a yaml file that demonstrates use cases for the Obsidian REST API.

### Building

To prepare the package for distribution:

1. Sync dependencies and update lockfile:

```bash
uv sync
```

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-obsidian-advanced run mcp-obsidian-advanced
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

You can also watch the server logs with this command:

```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-obsidian-advanced.log
```
