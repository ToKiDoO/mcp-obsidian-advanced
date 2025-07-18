import requests
import urllib.parse
import os
import obsidiantools.api as otools
from typing import Any
from pathlib import Path

class Obsidian():
    def __init__(
            self, 
            api_key: str = str(os.getenv('OBSIDIAN_API_KEY', '')),
            protocol: str = os.getenv('OBSIDIAN_PROTOCOL', 'https').lower(),
            host: str = str(os.getenv('OBSIDIAN_HOST', '127.0.0.1')),
            port: int = int(os.getenv('OBSIDIAN_PORT', '27124')),
            vault_path: str = os.getenv('OBSIDIAN_VAULT_PATH', ''),
            verify_ssl: bool = False,
        ):
        
        if protocol == 'http':
            self.protocol = 'http'
        else:
            self.protocol = 'https' # Default to https for any other value, including 'https'

        self.host = host
        self.port = port
        self.api_key = api_key
        self.vault_path = vault_path

        self.verify_ssl = verify_ssl
        self.timeout = (3, 6)

    def _check_credentials(self):
        if not self.vault_path:
            raise RuntimeError("OBSIDIAN_VAULT_PATH environment variable not set")
        if not self.api_key:
            raise RuntimeError("OBSIDIAN_API_KEY environment variable not set")

    def get_base_url(self) -> str:
        return f'{self.protocol}://{self.host}:{self.port}'
    
    def _get_headers(self) -> dict:
        self._check_credentials()
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        return headers

    def _safe_call(self, f) -> Any:
        try:
            return f()
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            code = error_data.get('errorCode', -1) 
            message = error_data.get('message', '<unknown>')
            raise Exception(f"Error {code}: {message}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def get_note_info (self, note_filepath: str) -> Any:
        vault = otools.Vault(Path(self.vault_path)).connect().gather() # Initialize obsidiantools vault
        note_name = os.path.splitext(os.path.basename(note_filepath))[0] # Extract note name from filepath (remove .md extension and path)
            
        # Check if note exists in vault
        if note_name not in vault.md_file_index:
            raise RuntimeError(f"Note '{note_filepath}' not found in vault")
            
        # Get note metadata
        all_metadata_df = vault.get_note_metadata()
        note_metadata = all_metadata_df.loc[note_name]
            
        # Extract metadata
        metadata = {
            "tags": vault.get_tags(note_name),
            "front_matter": vault.get_front_matter(note_name),
            "file_info": {
                "rel_filepath": str(note_metadata.get("rel_filepath")),
                "modified_time": str(note_metadata.get("modified_time"))
            },
            "counts": {
                "n_backlinks": int(note_metadata.get("n_backlinks", 0)),
                "n_wikilinks": int(note_metadata.get("n_wikilinks", 0)),
                "n_embedded_files": int(note_metadata.get("n_embedded_files", 0)),
                "n_tags": int(note_metadata.get("n_tags", 0))
            }
        }
            
        # Extract connections
        wikilinks = vault.get_wikilinks(note_name)
        embedded_files = vault.get_embedded_files(note_name)
        backlinks = vault.get_backlinks(note_name)
        # Combine direct links (wikilinks + embedded files)
        direct_links = list(set(wikilinks + embedded_files)) 

        # Get non-existent links (links that don't exist in vault)
        non_existent_links = []
        for link in wikilinks:
            if link in all_metadata_df.index:
                if not all_metadata_df.loc[link, "note_exists"]:
                    non_existent_links.append(link)
            
        connections = {
            "direct_links": direct_links,
            "backlinks": backlinks,
            "non_existent_links": non_existent_links
        }

        # Construct final response
        note_info = {
            "metadata": metadata,
            "connections": connections,
        }

        return note_info
    
    def list_files_in_dir(self, dirpath: str) -> Any:
        encoded_dirpath = urllib.parse.quote(dirpath)
        url = f"{self.get_base_url()}/vault/{encoded_dirpath}/"
        
        def call_fn():
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()['files']

        return self._safe_call(call_fn)

    def get_file_contents(self, filepath: str) -> Any:
        """Tool removed because batch content can handle one or more .md files.. This is now a helper function for get_batch_file_contents that returns the content of a single file. 
        
        Args:
            filepath: Relative path to .md note file to read. ONLY .md files are supported.
            
        Returns:
            Redable markdown content of a note.
        """
        url = f"{self.get_base_url()}/vault/{filepath}"
    
        def call_fn():
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            
            return response.text

        return self._safe_call(call_fn)
    
    def get_batch_file_contents(self, filepaths: list[str]) -> list:
        """Get contents and info of multiple files using enhanced API approach.
        
        Args:
            filepaths: List of .md note file paths to read. ONLY .md files are supported.
            
        Returns:
            List of objects containing file metadata, connections, tags, front matter, file info, and content
        """
        results = []
        
        for filepath in filepaths:
            try:
                # Get content using the existing method
                content = self.get_file_contents(filepath)
                
                # Get enhanced metadata using REST API (similar to active note approach)
                url = f"{self.get_base_url()}/vault/{filepath}"
                headers = self._get_headers() | {'Accept': 'application/vnd.olrapi.note+json'}
                
                def call_fn():
                    response = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json()
                
                file_data = self._safe_call(call_fn)
                
                # Extract data from the API response
                api_frontmatter = file_data.get('frontmatter', {})
                api_stat = file_data.get('stat', {})
                api_tags = file_data.get('tags', [])
                
                # Get additional note info using obsidiantools for connections/links
                try:
                    note_info = self.get_note_info(filepath)
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
                
                results.append({
                    "filepath": filepath,
                    "note_info": note_info,
                    "content": content
                })
            except Exception as e:
                # Add error message but continue processing other files
                results.append({
                    "filepath": filepath,
                    "error": f"Error reading file: {str(e)}"
                })
                
        return results
    
    def get_active_note(self) -> Any:
        """Get content of the currently actively edited note.

        Returns:
            Redable markdown content of the currently actively edited note.
        """
        url = f"{self.get_base_url()}/active/"
    
        def call_fn():
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            
            return response.text

        return self._safe_call(call_fn)

    def search(self, query: str, context_length: int = 300) -> Any:
        url = f"{self.get_base_url()}/search/simple/"
        params = {
            'query': query,
            'contextLength': context_length
        }
        
        def call_fn():
            response = requests.post(url, headers=self._get_headers(), params=params, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
    
    def append_content(self, filepath: str, content: str) -> Any:
        url = f"{self.get_base_url()}/vault/{filepath}"
        
        def call_fn():
            response = requests.post(
                url, 
                headers=self._get_headers() | {'Content-Type': 'text/markdown'}, 
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)
    
    def patch_content(self, filepath: str, operation: str, target_type: str, target: str, content: str) -> Any:
        url = f"{self.get_base_url()}/vault/{filepath}"
        
        headers = self._get_headers() | {
            'Content-Type': 'text/markdown',
            'Operation': operation,
            'Target-Type': target_type,
            'Target': urllib.parse.quote(target)
        }
        
        def call_fn():
            response = requests.patch(url, headers=headers, data=content, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def put_content(self, filepath: str, content: str) -> Any:
        url = f"{self.get_base_url()}/vault/{filepath}"
        
        def call_fn():
            response = requests.put(
                url, 
                headers=self._get_headers() | {'Content-Type': 'text/markdown'}, 
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)
    
    def delete_file(self, filepath: str) -> Any:
        """Delete a file or directory from the vault.
        
        Args:
            filepath: Path to the file to delete (relative to vault root)
            
        Returns:
            None on success
        """
        url = f"{self.get_base_url()}/vault/{filepath}"
        
        def call_fn():
            response = requests.delete(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return None
            
        return self._safe_call(call_fn)
    
    def search_json(self, query: dict) -> Any:
        url = f"{self.get_base_url()}/search/"
        
        headers = self._get_headers() | {
            'Content-Type': 'application/vnd.olrapi.jsonlogic+json'
        }
        
        def call_fn():
            response = requests.post(url, headers=headers, json=query, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
    
    def get_periodic_note(self, period: str, type: str = "content") -> Any:
        """Get current periodic note for the specified period.
        
        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            type: Type of the data to get ('content' or 'metadata'). 
                'content' returns just the content in Markdown format. 
                'metadata' includes note metadata (including paths, tags, etc.) and the content.. 
            
        Returns:
            Content of the periodic note
        """
        url = f"{self.get_base_url()}/periodic/{period}/"
        
        def call_fn():
            headers = self._get_headers()
            if type == "metadata":
                headers['Accept'] = 'application/vnd.olrapi.note+json'
            response = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            
            return response.text

        return self._safe_call(call_fn)
    
    def get_recent_periodic_notes(self, period: str, limit: int = 5, include_content: bool = False) -> Any:
        """Get most recent periodic notes for the specified period type.
        
        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            limit: Maximum number of notes to return (default: 5)
            include_content: Whether to include note content (default: False)
            
        Returns:
            List of recent periodic notes
        """
        url = f"{self.get_base_url()}/periodic/{period}/recent"
        params = {
            "limit": limit,
            "includeContent": include_content
        }
        
        def call_fn():
            response = requests.get(
                url, 
                headers=self._get_headers(), 
                params=params,
                verify=self.verify_ssl, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()

        return self._safe_call(call_fn)
    
    def get_recent_changes(self, limit: int = 10, days: int = 90) -> Any:
        """Get recently modified files in the vault.
        
        Args:
            limit: Maximum number of files to return (default: 10)
            days: Only include files modified within this many days (default: 90)
            
        Returns:
            List of recently modified files with metadata
        """
        # Build the DQL query
        query_lines = [
            "TABLE file.mtime",
            f"WHERE file.mtime >= date(today) - dur({days} days)",
            "SORT file.mtime DESC",
            f"LIMIT {limit}"
        ]
        
        # Join with proper DQL line breaks
        dql_query = "\n".join(query_lines)
        
        # Make the request to search endpoint
        url = f"{self.get_base_url()}/search/"
        headers = self._get_headers() | {
            'Content-Type': 'application/vnd.olrapi.dataview.dql+txt'
        }
        
        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                data=dql_query.encode('utf-8'),
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
    
    def open_file(self, filepath: str) -> Any:
        """Open a file in the vault.
        
        Args:
            filepath: Path to the file to open (relative to vault root)
            
        Returns:
            None on success. Opens the file in the default editor in a new leaf.
        """
        url = f"{self.get_base_url()}/open/{filepath}"
        
        def call_fn():
            response = requests.post(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return None
            
        return self._safe_call(call_fn)
    
    def list_commands(self) -> Any:
        """List all available commands you can run in obsidian interface. For commands on open notes, make sure to open a note first.
            
        Returns:
            List of available commands in obsidian.
        """
        url = f"{self.get_base_url()}/commands/"
        
        def call_fn():
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
    
    def execute_command(self, command: str) -> Any:
        """Execute a command in obsidian interface. For commands on open notes, make sure to open a note first.
        
        Args:
            command: Command to execute
            
        Returns:
            None on success. Executes the command in obsidian.
        """
        url = f"{self.get_base_url()}/commands/{command}"
        
        def call_fn():
            response = requests.post(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return None
        
        return self._safe_call(call_fn)
