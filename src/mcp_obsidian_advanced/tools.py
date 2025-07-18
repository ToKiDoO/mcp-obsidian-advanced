from collections.abc import Sequence
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import json
import os
from pathlib import Path
import requests
import obsidiantools.api as otools
from networkx.readwrite import json_graph
from anytree import Node, RenderTree
from . import obsidian


# Global Obsidian API client initialization
api = obsidian.Obsidian(api_key=os.getenv("OBSIDIAN_API_KEY"), host=os.getenv("OBSIDIAN_HOST", "127.0.0.1"), port=os.getenv("OBSIDIAN_PORT", "27124"), vault_path=os.getenv("OBSIDIAN_VAULT_PATH", ""))

TOOL_LIST_FILES_IN_DIR = "obsidian_list_files_in_dir"
TOOL_SIMPLE_SEARCH = "obsidian_simple_search"
TOOL_PATCH_CONTENT = "obsidian_patch_file"
TOOL_PUT_CONTENT = "obsidian_put_file"
TOOL_APPEND_CONTENT = "obsidian_append_to_file"
TOOL_DELETE_FILE = "obsidian_delete_file"
TOOL_COMPLEX_SEARCH = "obsidian_complex_search"
TOOL_BATCH_GET_FILES = "obsidian_batch_get_files"
TOOL_GET_ACTIVE_NOTE = "obsidian_get_active_note"
TOOL_PERIODIC_NOTES = "obsidian_periodic_notes"
TOOL_RECENT_PERIODIC_NOTES = "obsidian_recent_periodic_notes"
TOOL_RECENT_CHANGES = "obsidian_recent_changes"
TOOL_UNDERSTAND_VAULT = "obsidian_understand_vault"
TOOL_OPEN_FILES = "obsidian_open_files"
TOOL_LIST_COMMANDS = "obsidian_list_commands"
TOOL_EXECUTE_COMMANDS = "obsidian_execute_commands"

class ToolHandler():
    def __init__(self, tool_name: str):
        self.name = tool_name

    def get_tool_description(self) -> Tool:
        raise NotImplementedError()

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        raise NotImplementedError()
    
class ListFilesInDirToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_LIST_FILES_IN_DIR)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Lists all files and directories that exist in a specific Obsidian directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Path to list files from (relative to your vault root). Note that empty directories will not be returned."
                    },
                },
                "required": ["dirpath"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:

        if "dirpath" not in args:
            raise RuntimeError("dirpath argument missing in arguments")

        files = api.list_files_in_dir(args["dirpath"])

        return [
            TextContent(
                type="text",
                text=json.dumps(files, indent=2)
            )
        ]
    
class SearchToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_SIMPLE_SEARCH)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="""Simple search for documents matching a specified text query across all files in the vault. 
            Use this tool when you want to do a simple text search""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to a simple search for in the vault."
                    },
                    "context_length": {
                        "type": "integer",
                        "description": "How much context to return around the matching string (default: 300)",
                        "default": 300
                    }
                },
                "required": ["query"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "query" not in args:
            raise RuntimeError("query argument missing in arguments")

        context_length = args.get("context_length", 100)
        
        results = api.search(args["query"], context_length)
        
        formatted_results = []
        for result in results:
            formatted_matches = []
            for match in result.get('matches', []):
                context = match.get('context', '')
                match_pos = match.get('match', {})
                start = match_pos.get('start', 0)
                end = match_pos.get('end', 0)
                
                formatted_matches.append({
                    'context': context,
                    'match_position': {'start': start, 'end': end}
                })
                
            formatted_results.append({
                'filename': result.get('filename', ''),
                'score': result.get('score', 0),
                'matches': formatted_matches
            })

        return [
            TextContent(
                type="text",
                text=json.dumps(formatted_results, indent=2)
            )
        ]
    
class AppendContentToolHandler(ToolHandler):
   def __init__(self):
       super().__init__(TOOL_APPEND_CONTENT)

   def get_tool_description(self):
       return Tool(
           name=self.name,
           description="Append content to a new or existing file in the vault.",
           inputSchema={
               "type": "object",
               "properties": {
                   "filepath": {
                       "type": "string",
                       "description": "Path to the file (relative to vault root)",
                       "format": "path"
                   },
                   "content": {
                       "type": "string",
                       "description": "Content to append to the file"
                   }
               },
               "required": ["filepath", "content"]
           }
       )

   def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
       if "filepath" not in args or "content" not in args:
           raise RuntimeError("filepath and content arguments required")

       api.append_content(args.get("filepath", ""), args["content"])

       return [
           TextContent(
               type="text",
               text=f"Successfully appended content to {args['filepath']}"
           )
       ]
   
class PatchContentToolHandler(ToolHandler):
   def __init__(self):
       super().__init__(TOOL_PATCH_CONTENT)

   def get_tool_description(self):
       return Tool(
           name=self.name,
           description="Insert content into an existing note relative to a heading, block reference, or frontmatter field.",
           inputSchema={
               "type": "object",
               "properties": {
                   "filepath": {
                       "type": "string",
                       "description": "Path to the file (relative to vault root)",
                       "format": "path"
                   },
                   "operation": {
                       "type": "string",
                       "description": "Operation to perform (append, prepend, or replace)",
                       "enum": ["append", "prepend", "replace"]
                   },
                   "target_type": {
                       "type": "string",
                       "description": "Type of target to patch",
                       "enum": ["heading", "block", "frontmatter"]
                   },
                   "target": {
                       "type": "string", 
                       "description": "Target identifier (heading path, block reference, or frontmatter field)"
                   },
                   "content": {
                       "type": "string",
                       "description": "Content to insert"
                   }
               },
               "required": ["filepath", "operation", "target_type", "target", "content"]
           }
       )

   def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
       if not all(k in args for k in ["filepath", "operation", "target_type", "target", "content"]):
           raise RuntimeError("filepath, operation, target_type, target and content arguments required")

       api.patch_content(
           args.get("filepath", ""),
           args.get("operation", ""),
           args.get("target_type", ""),
           args.get("target", ""),
           args.get("content", "")
       )

       return [
           TextContent(
               type="text",
               text=f"Successfully patched content in {args['filepath']}"
           )
       ]
       
class PutContentToolHandler(ToolHandler):
   def __init__(self):
       super().__init__(TOOL_PUT_CONTENT)

   def get_tool_description(self):
       return Tool(
           name=self.name,
           description="Create a new file in your vault or update the content of an existing one in your vault.",
           inputSchema={
               "type": "object",
               "properties": {
                   "filepath": {
                       "type": "string",
                       "description": "Path to the relevant file (relative to your vault root)",
                       "format": "path"
                   },
                   "content": {
                       "type": "string",
                       "description": "Content of the file you would like to upload"
                   }
               },
               "required": ["filepath", "content"]
           }
       )

   def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
       if "filepath" not in args or "content" not in args:
           raise RuntimeError("filepath and content arguments required")

       api.put_content(args.get("filepath", ""), args["content"])

       return [
           TextContent(
               type="text",
               text=f"Successfully uploaded content to {args['filepath']}"
           )
       ]
   

class DeleteFileToolHandler(ToolHandler):
   def __init__(self):
       super().__init__(TOOL_DELETE_FILE)

   def get_tool_description(self):
       return Tool(
           name=self.name,
           description="Delete a file or directory from the vault.",
           inputSchema={
               "type": "object",
               "properties": {
                   "filepath": {
                       "type": "string",
                       "description": "Path to the file or directory to delete (relative to vault root)",
                       "format": "path"
                   },
                   "confirm": {
                       "type": "boolean",
                       "description": "Confirmation to delete the file (must be true)",
                       "default": False
                   }
               },
               "required": ["filepath", "confirm"]
           }
       )

   def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
       if "filepath" not in args:
           raise RuntimeError("filepath argument missing in arguments")
       
       if not args.get("confirm", False):
           raise RuntimeError("confirm must be set to true to delete a file")

       api.delete_file(args["filepath"])

       return [
           TextContent(
               type="text",
               text=f"Successfully deleted {args['filepath']}"
           )
       ]
   
class ComplexSearchToolHandler(ToolHandler):
   def __init__(self):
       super().__init__(TOOL_COMPLEX_SEARCH)

   def get_tool_description(self):
       return Tool(
           name=self.name,
           description="""Complex search for documents using a JsonLogic query. 
           Supports standard JsonLogic operators plus 'glob' and 'regexp' for pattern matching. Results must be non-falsy.

           Use this tool when you want to do a complex search, e.g. for all documents with certain tags etc.
           ALWAYS follow query syntax in examples.

           Examples
            1. Match all markdown files
            {"glob": ["*.md", {"var": "path"}]}

            2. Match all markdown files with 1221 substring inside them
            {
              "and": [
                { "glob": ["*.md", {"var": "path"}] },
                { "regexp": [".*1221.*", {"var": "content"}] }
              ]
            }

            3. Match all markdown files in Work folder containing name Keaton
            {
              "and": [
                { "glob": ["*.md", {"var": "path"}] },
                { "regexp": [".*Work.*", {"var": "path"}] },
                { "regexp": ["Keaton", {"var": "content"}] }
              ]
            }
           """,
           inputSchema={
               "type": "object",
               "properties": {
                   "query": {
                       "type": "object",
                       "description": "JsonLogic query object. ALWAYS follow query syntax in examples. \
                            Example 1: {\"glob\": [\"*.md\", {\"var\": \"path\"}]} matches all markdown files \
                            Example 2: {\"and\": [{\"glob\": [\"*.md\", {\"var\": \"path\"}]}, {\"regexp\": [\".*1221.*\", {\"var\": \"content\"}]}]} matches all markdown files with 1221 substring inside them \
                            Example 3: {\"and\": [{\"glob\": [\"*.md\", {\"var\": \"path\"}]}, {\"regexp\": [\".*Work.*\", {\"var\": \"path\"}]}, {\"regexp\": [\"Keaton\", {\"var\": \"content\"}]}]} matches all markdown files in Work folder containing name Keaton \
                        "
                   }
               },
               "required": ["query"]
           }
       )

   def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
       if "query" not in args:
           raise RuntimeError("query argument missing in arguments")

       results = api.search_json(args.get("query", ""))

       return [
           TextContent(
               type="text",
               text=json.dumps(results, indent=2)
           )
       ]

class BatchGetFilesToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_BATCH_GET_FILES)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Return the contents and metadata of one or more notes (.md files) in your vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepaths": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Path to a file (relative to your vault root)",
                            "format": "path"
                        },
                        "description": "List of file paths to read"
                    },
                },
                "required": ["filepaths"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "filepaths" not in args:
            raise RuntimeError("filepaths argument missing in arguments")

        results = api.get_batch_file_contents(args["filepaths"])
        
        response_parts = []
        
        # For each file, add its metadata/info JSON followed by its content
        for result in results:
            if "error" not in result:
                # Add metadata and note info as JSON
                metadata_json = {
                    "filepath": result["filepath"],
                    "note_info": result["note_info"]
                }
                response_parts.append(
                    TextContent(
                        type="text",
                        text=f"## File: {result['filepath']}\n\n### Metadata & Info\n```json\n{json.dumps(metadata_json, indent=2)}\n```"
                    )
                )
                
                # Add the actual content as readable markdown
                response_parts.append(
                    TextContent(
                        type="text",
                        text=f"### Content Below:\n\n{result['content']}"
                    )
                )
            else:
                # Handle error case
                response_parts.append(
                    TextContent(
                        type="text",
                        text=f"## File: {result['filepath']}\n\n### Error\n{result['error']}"
                    )
                )
        
        return response_parts

class GetActiveNoteToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_GET_ACTIVE_NOTE)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get the content and metadata of the currently active note in Obsidian. Always returns the note that is most recently edited (edit with user).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        try:
            # Get the active note with full metadata using the JSON API
            url = f"{api.get_base_url()}/active/"
            headers = api._get_headers() | {'Accept': 'application/vnd.olrapi.note+json'}
            
            def call_fn():
                response = requests.get(url, headers=headers, verify=api.verify_ssl, timeout=api.timeout)
                response.raise_for_status()
                return response.json()
            
            active_note_data = api._safe_call(call_fn)
            
            # Extract data from the API response
            content = active_note_data.get('content', '')
            frontmatter = active_note_data.get('frontmatter', {})
            path = active_note_data.get('path', '')
            stat = active_note_data.get('stat', {})
            api_tags = active_note_data.get('tags', [])
            
            if not content and not path:
                return [
                    TextContent(
                        type="text",
                        text="No active note found."
                    )
                ]
            
            # Get additional note info using obsidiantools for connections/links
            try:
                note_info = api.get_note_info(path)
                # Replace the tags from get_note_info with the more accurate API tags
                note_info['metadata']['tags'] = api_tags
                # Also update frontmatter with API data for accuracy
                note_info['metadata']['front_matter'] = frontmatter
                # Update file info with API stat data
                note_info['metadata']['file_info'].update({
                    'creation_time': stat.get('ctime'),
                    'modification_time': stat.get('mtime'),
                    'size (bytes)': stat.get('size')
                })
            except Exception as note_info_error:
                # Fallback: create basic note info from API data
                note_info = {
                    'metadata': {
                        'tags': api_tags,
                        'front_matter': frontmatter,
                        'file_info': {
                            'rel_filepath': path,
                            'creation_time': stat.get('ctime'),
                            'modification_time': stat.get('mtime'),
                            'size (bytes)': stat.get('size')
                        },
                        'counts': {
                            'n_backlinks': 0,
                            'n_wikilinks': 0,
                            'n_embedded_files': 0,
                            'n_tags': len(api_tags)
                        }
                    },
                    'connections': {
                        'direct_links': [],
                        'backlinks': [],
                        'non_existent_links': []
                    }
                }
            
            # Create metadata JSON following BatchGetFilesToolHandler pattern
            metadata_json = {
                "filepath": path,
                "note_info": note_info
            }
            
            return [
                TextContent(
                    type="text",
                    text=f"## Active Note: {path}\n\n### Metadata & Info\n```json\n{json.dumps(metadata_json, indent=2)}\n```"
                ),
                TextContent(
                    type="text",
                    text=f"### Content Below:\n\n{content}"
                )
            ]
                
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error getting active note: {str(e)}"
                )
            ]

class PeriodicNotesToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_PERIODIC_NOTES)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get current periodic note for the specified period. Returns both comprehensive metadata (tags, links, titles, etc.) and note content using the enhanced API approach.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "The period type (daily, weekly, monthly, quarterly, yearly)",
                        "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"]
                    }
                },
                "required": ["period"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "period" not in args:
            raise RuntimeError("period argument missing in arguments")

        period = args["period"]
        valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if period not in valid_periods:
            raise RuntimeError(f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}")

        try:
            # Get the periodic note metadata to extract the file path
            metadata_response = api.get_periodic_note(period, "metadata")
            
            # Parse the JSON response to extract the file path
            import json
            try:
                metadata_json = json.loads(metadata_response)
                filepath = metadata_json.get('path', '')
            except (json.JSONDecodeError, AttributeError):
                # Fallback: try to get content directly if metadata parsing fails
                content = api.get_periodic_note(period, "content")
                return [
                    TextContent(
                        type="text",
                        text=f"## Periodic Note ({period})\n\n### Content Below:\n\n{content}"
                    )
                ]
            
            if not filepath:
                return [
                    TextContent(
                        type="text",
                        text=f"No {period} periodic note found."
                    )
                ]
            
            # Use the enhanced API approach to get comprehensive metadata and content
            # Get content using the existing method
            content = api.get_file_contents(filepath)
            
            # Get enhanced metadata using REST API
            url = f"{api.get_base_url()}/vault/{filepath}"
            headers = api._get_headers() | {'Accept': 'application/vnd.olrapi.note+json'}
            
            def call_fn():
                response = requests.get(url, headers=headers, verify=api.verify_ssl, timeout=api.timeout)
                response.raise_for_status()
                return response.json()
            
            file_data = api._safe_call(call_fn)
            
            # Extract data from the API response
            api_frontmatter = file_data.get('frontmatter', {})
            api_stat = file_data.get('stat', {})
            api_tags = file_data.get('tags', [])
            
            # Get additional note info using obsidiantools for connections/links
            try:
                note_info = api.get_note_info(filepath)
                # Replace the tags from get_note_info with the more accurate API tags
                note_info['metadata']['tags'] = api_tags
                # Also update frontmatter with API data for accuracy
                note_info['metadata']['front_matter'] = api_frontmatter
                # Update file info with API stat data
                note_info['metadata']['file_info'].update({
                    'ctime': api_stat.get('ctime'),
                    'mtime': api_stat.get('mtime'),
                    'size': api_stat.get('size')
                })
            except Exception as note_info_error:
                # Fallback: create basic note info from API data
                note_info = {
                    'metadata': {
                        'tags': api_tags,
                        'front_matter': api_frontmatter,
                        'file_info': {
                            'rel_filepath': filepath,
                            'ctime': api_stat.get('ctime'),
                            'mtime': api_stat.get('mtime'),
                            'size': api_stat.get('size')
                        },
                        'counts': {
                            'n_backlinks': 0,
                            'n_wikilinks': 0,
                            'n_embedded_files': 0,
                            'n_tags': len(api_tags)
                        }
                    },
                    'connections': {
                        'direct_links': [],
                        'backlinks': [],
                        'non_existent_links': []
                    }
                }
            
            # Create metadata JSON following BatchGetFilesToolHandler pattern
            metadata_json = {
                "filepath": filepath,
                "note_info": note_info
            }
            
            return [
                TextContent(
                    type="text",
                    text=f"## Periodic Note ({period}): {filepath}\n\n### Metadata & Info\n```json\n{json.dumps(metadata_json, indent=2)}\n```"
                ),
                TextContent(
                    type="text",
                    text=f"### Content Below:\n\n{content}"
                )
            ]
                
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error getting {period} periodic note: {str(e)}"
                )
            ]
        
class RecentPeriodicNotesToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_RECENT_PERIODIC_NOTES)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get most recent periodic notes for the specified period type. When include_content=True, return notes' comprehensive metadata (tags, links, titles, etc.) and note content using the enhanced API approach.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "The period type (daily, weekly, monthly, quarterly, yearly)",
                        "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of notes to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "include_content": {
                        "type": "boolean",
                        "description": "Whether to include note content and comprehensive metadata (default: false)",
                        "default": False
                    }
                },
                "required": ["period"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "period" not in args:
            raise RuntimeError("period argument missing in arguments")

        period = args["period"]
        valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if period not in valid_periods:
            raise RuntimeError(f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}")

        limit = args.get("limit", 5)
        if not isinstance(limit, int) or limit < 1:
            raise RuntimeError(f"Invalid limit: {limit}. Must be a positive integer")
            
        include_content = args.get("include_content", False)
        if not isinstance(include_content, bool):
            raise RuntimeError(f"Invalid include_content: {include_content}. Must be a boolean")

        results = api.get_recent_periodic_notes(period, limit, include_content)

        # If include_content is False, return the results as-is (no enhancement needed)
        if not include_content:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(results, indent=2)
                )
            ]

        # If include_content is True, enhance each note with comprehensive metadata
        enhanced_results = []
        
        for note in results:
            try:
                filepath = note.get('path', '')
                if not filepath:
                    # Keep the original note if no path is available
                    enhanced_results.append(note)
                    continue
                
                # Get enhanced metadata using REST API
                url = f"{api.get_base_url()}/vault/{filepath}"
                headers = api._get_headers() | {'Accept': 'application/vnd.olrapi.note+json'}
                
                def call_fn():
                    response = requests.get(url, headers=headers, verify=api.verify_ssl, timeout=api.timeout)
                    response.raise_for_status()
                    return response.json()
                
                file_data = api._safe_call(call_fn)
                
                # Extract data from the API response
                api_frontmatter = file_data.get('frontmatter', {})
                api_stat = file_data.get('stat', {})
                api_tags = file_data.get('tags', [])
                
                # Get additional note info using obsidiantools for connections/links
                try:
                    note_info = api.get_note_info(filepath)
                    # Replace the tags from get_note_info with the more accurate API tags
                    note_info['metadata']['tags'] = api_tags
                    # Also update frontmatter with API data for accuracy
                    note_info['metadata']['front_matter'] = api_frontmatter
                    # Update file info with API stat data
                    note_info['metadata']['file_info'].update({
                        'ctime': api_stat.get('ctime'),
                        'mtime': api_stat.get('mtime'),
                        'size': api_stat.get('size')
                    })
                except Exception as note_info_error:
                    # Fallback: create basic note info from API data
                    note_info = {
                        'metadata': {
                            'tags': api_tags,
                            'front_matter': api_frontmatter,
                            'file_info': {
                                'rel_filepath': filepath,
                                'ctime': api_stat.get('ctime'),
                                'mtime': api_stat.get('mtime'),
                                'size': api_stat.get('size')
                            },
                            'counts': {
                                'n_backlinks': 0,
                                'n_wikilinks': 0,
                                'n_embedded_files': 0,
                                'n_tags': len(api_tags)
                            }
                        },
                        'connections': {
                            'direct_links': [],
                            'backlinks': [],
                            'non_existent_links': []
                        }
                    }
                
                # Add note_info to the existing note object
                enhanced_note = note.copy()
                enhanced_note['note_info'] = note_info
                enhanced_results.append(enhanced_note)
                
            except Exception as e:
                # Keep the original note but add an error field
                enhanced_note = note.copy()
                enhanced_note['metadata_error'] = f"Error getting enhanced metadata: {str(e)}"
                enhanced_results.append(enhanced_note)

        return [
            TextContent(
                type="text",
                text=json.dumps(enhanced_results, indent=2)
            )
        ]
        
class RecentChangesToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_RECENT_CHANGES)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get recently modified files in the vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of files to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "days": {
                        "type": "integer",
                        "description": "Only include files modified within this many days (default: 90)",
                        "minimum": 1,
                        "default": 90
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        limit = args.get("limit", 10)
        if not isinstance(limit, int) or limit < 1:
            raise RuntimeError(f"Invalid limit: {limit}. Must be a positive integer")
            
        days = args.get("days", 90)
        if not isinstance(days, int) or days < 1:
            raise RuntimeError(f"Invalid days: {days}. Must be a positive integer")

        results = api.get_recent_changes(limit, days)

        return [
            TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )
        ]

class UnderstandVaultToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_UNDERSTAND_VAULT)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get a comprehensive understanding of the vault structure. Returns: 1. directory tree representation and 2. NetworkX graph of note connections used to understand how different notes (.md) and other files (e.g. images, PDFs, referenced/attached) are connected. Combines filesystem directory structure with note relationship graph between notes (.md files).",
            inputSchema={
                'type': 'object',
                'properties': {
                    'directory_path': {
                        'type': 'string',
                        'description': 'Optional path to a subdirectory to analyze, defaults to vault root'
                    },
                    'include_attachments_in_graph': {
                        'type': 'boolean',
                        'description': 'Whether to include attachment files (images, PDFs, etc.) in the *NetworkX connections graph*, excluding attachments in Obsidian. Defaults to True',
                        'default': True
                    },
                    'include_other_files_in_tree': {
                        'type': 'boolean',
                        'description': 'Whether to show only .md files in the *directory tree structure*, excluding other file types. Defaults to True',
                        'default': True
                    }
                }
            }
        )

    def _build_directory_tree(self, vault_path: str, target_dir: str = None, include_other_files: bool = True) -> str:
        """Build a directory tree structure using anytree."""
        vault_path_obj = Path(vault_path)
        target_path = vault_path_obj / target_dir if target_dir else vault_path_obj
        
        if not target_path.exists():
            raise ValueError(f"Directory path does not exist: {target_path}")
        
        # Create root node with vault name
        vault_name = vault_path_obj.name
        root = Node(vault_name)
        
        # Dictionary to store nodes by their path for building hierarchy
        nodes = {str(target_path): root}
        
        # Walk through all files and directories
        for item_path in sorted(target_path.rglob("*")):
            if item_path == target_path:
                continue
            
            # If include_other_files is False, only show .md files and directories
            if not include_other_files and item_path.is_file() and item_path.suffix != '.md':
                continue
                
            # Get relative path from vault root
            rel_path = item_path.relative_to(vault_path_obj)
            
            # Find parent node
            parent_path = str(item_path.parent)
            parent_node = nodes.get(parent_path, root)
            
            # Create display name with relative path for files
            if item_path.is_file():
                display_name = f"{item_path.name} ({rel_path})"
            else:
                display_name = f"{item_path.name}/"
            
            # Create node
            node = Node(display_name, parent=parent_node)
            nodes[str(item_path)] = node
        
        # Render tree
        tree_lines = []
        for pre, _, node in RenderTree(root):
            tree_lines.append(f"{pre}{node.name}")
        
        return "\n".join(tree_lines)

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault_path:
            raise ValueError("OBSIDIAN_VAULT_PATH environment variable is not set. This tool cannot run without it.")

        directory_path = args.get('directory_path')
        include_attachments_in_graph = args.get('include_attachments_in_graph', True)
        include_other_files_in_tree = args.get('include_other_files_in_tree', True)

        # Generate directory tree
        try:
            tree_structure = self._build_directory_tree(vault_path, directory_path, include_other_files_in_tree)
        except Exception as e:
            raise ValueError(f"Error building directory tree: {str(e)}")

        # Generate note connections graph with proper attachments parameter
        vault_path_obj = Path(vault_path)
        vault = otools.Vault(vault_path_obj).connect(attachments=include_attachments_in_graph).gather()
        graph = vault.graph
        graph_data = json_graph.node_link_data(graph)

        # Combine both outputs
        return [
            TextContent(
                type="text",
                text=f"# Vault Understanding\n\n## Vault Tree Structure:\n```\n{tree_structure}\n```\n\n## Note Connections:\n```json\n{json.dumps(graph_data, indent=2)}\n```"
            )
        ]

class OpenFilesToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_OPEN_FILES)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Open one or more files in the vault in a new leaf.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepaths": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Path to a file (relative to your vault root)",
                            "format": "path"
                        },
                        "description": "List of file paths to open"
                    },
                },
                "required": ["filepaths"]
            }
        )
    
    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        filepaths = args.get("filepaths")
        if not filepaths:
            raise ValueError("One or more filepaths are required")
        
        successful_opens = []
        failed_opens = []
        
        for file in filepaths:
            try:
                api.open_file(file)
                successful_opens.append(file)
            except Exception as e:
                failed_opens.append((file, str(e)))
        
        if failed_opens:
            error_messages = [f"Failed to open '{file}': {error}" for file, error in failed_opens]
            if successful_opens:
                return [
                    TextContent(
                        type="text",
                        text=f"Opened {len(successful_opens)} file(s) successfully. Errors: {'; '.join(error_messages)}"
                    )
                ]
            else:
                raise ValueError(f"Failed to open any files: {'; '.join(error_messages)}")
        
        return [
            TextContent(
                type="text",
                text="File(s) opened successfully!"
            )
        ]

class ListCommandsToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_LIST_COMMANDS)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="List all available commands you can run in obsidian interface. For commands used on specific notes, make sure to open a note first.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        )
    
    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        commands = api.list_commands()
        return [
            TextContent(
                type="text",
                text=json.dumps(commands, indent=2)
            )
        ]

class ExecuteCommandsToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_EXECUTE_COMMANDS)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Execute one or more commands in obsidian interface, *in order*. For commands used on specific notes, make sure to open a note first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "commands": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Command to execute"
                        },
                        "description": "List of commands to execute"
                    },
                },
                "required": ["commands"]
            }
        )
    
    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        commands = args.get("commands")
        if not commands:
            raise ValueError("One or more commands are required")
    
        results = []
        success = True
    
        for command in commands:
            try:
                api.execute_command(command)
                results.append(f"Command '{command}' executed successfully")
            except Exception as e:
                success = False
                results.append(f"Failed to execute command '{command}': {str(e)}")
    
        if success:
            return [
                TextContent(
                    type="text",
                    text="All commands executed successfully!"
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text="\n".join(results)
                )
            ]