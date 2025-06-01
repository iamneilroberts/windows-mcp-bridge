"""
Prompt viewer and manager for D1 database prompts.

This module provides functionality to view, search, and manage prompts
stored in the D1 database.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..logging import logger


@dataclass
class Prompt:
    """Represents a prompt from the D1 database."""
    name: str
    description: str
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class PromptViewer:
    """Handles viewing and managing prompts from D1 database."""
    
    def __init__(self):
        self.cached_prompts: Dict[str, Prompt] = {}
    
    def parse_db_results(self, db_results: str) -> List[Dict[str, Any]]:
        """Parse database query results."""
        try:
            # Check for database errors first
            if isinstance(db_results, str):
                # Common error patterns
                error_patterns = [
                    "connection failed",
                    "database error",
                    "query failed",
                    "server error",
                    "not found",
                    "timeout",
                    "failed to connect"
                ]
                lower_result = db_results.lower()
                for pattern in error_patterns:
                    if pattern in lower_result:
                        logger.warning(f"Database error detected: {db_results}")
                        return []
                
                # Try to parse as JSON
                try:
                    data = json.loads(db_results)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and 'results' in data:
                        return data['results']
                    elif isinstance(data, dict) and 'rows' in data:
                        return data['rows']
                    elif isinstance(data, dict) and 'error' in data:
                        logger.error(f"Database returned error: {data['error']}")
                        return []
                except json.JSONDecodeError:
                    # If not JSON, try to parse as formatted text
                    return self._parse_text_results(db_results)
            elif isinstance(db_results, list):
                return db_results
            elif isinstance(db_results, dict):
                if 'error' in db_results:
                    logger.error(f"Database returned error: {db_results['error']}")
                    return []
                if 'results' in db_results:
                    return db_results['results']
                elif 'rows' in db_results:
                    return db_results['rows']
                return [db_results]
            else:
                return []
        except Exception as e:
            logger.error(f"Error parsing database results: {e}")
            return []
    
    def _parse_text_results(self, text: str) -> List[Dict[str, Any]]:
        """Parse text-formatted database results."""
        # This is a simple parser for common text formats
        # You might need to adjust based on actual D1 output format
        rows = []
        lines = text.strip().split('\n')
        
        if not lines:
            return rows
        
        # Try to detect table format
        if '|' in lines[0]:
            # Parse table format
            header_line = None
            for i, line in enumerate(lines):
                if '|' in line and not line.strip().startswith('-'):
                    if header_line is None:
                        header_line = i
                        headers = [h.strip() for h in line.split('|') if h.strip()]
                    else:
                        values = [v.strip() for v in line.split('|') if v.strip()]
                        if len(values) == len(headers):
                            rows.append(dict(zip(headers, values)))
        
        return rows
    
    def format_prompt_list(self, prompts: List[Dict[str, Any]]) -> str:
        """Format a list of prompts for display."""
        if not prompts:
            return "No prompts found."
        
        # Group by category
        by_category = {}
        for prompt in prompts:
            category = prompt.get('category', 'Uncategorized')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(prompt)
        
        output = "# Available Prompts\n\n"
        
        for category, category_prompts in sorted(by_category.items()):
            output += f"## {category}\n\n"
            for prompt in sorted(category_prompts, key=lambda p: p.get('name', '')):
                name = prompt.get('name', 'Unnamed')
                desc = prompt.get('description', 'No description')
                output += f"- **{name}**: {desc}\n"
            output += "\n"
        
        return output
    
    def format_prompt_detail(self, prompt: Dict[str, Any]) -> str:
        """Format a single prompt for detailed display."""
        name = prompt.get('name', 'Unnamed Prompt')
        desc = prompt.get('description', 'No description')
        content = prompt.get('content', prompt.get('prompt', 'No content'))
        category = prompt.get('category', 'Uncategorized')
        tags = prompt.get('tags', [])
        
        output = f"# {name}\n\n"
        output += f"**Category:** {category}\n"
        output += f"**Description:** {desc}\n"
        
        if tags:
            if isinstance(tags, str):
                output += f"**Tags:** {tags}\n"
            else:
                output += f"**Tags:** {', '.join(tags)}\n"
        
        output += f"\n## Content\n\n```\n{content}\n```\n"
        
        # Add metadata if available
        metadata_fields = ['created_at', 'updated_at', 'version', 'author']
        metadata_output = []
        for field in metadata_fields:
            if field in prompt:
                metadata_output.append(f"{field}: {prompt[field]}")
        
        if metadata_output:
            output += f"\n## Metadata\n\n"
            output += '\n'.join(metadata_output)
        
        return output
    
    def create_prompt_editor_view(self, prompts: List[Dict[str, Any]]) -> str:
        """Create an editable view of all prompts."""
        output = "# Prompt Management Dashboard\n\n"
        output += "This view shows all prompts from the D1 database. "
        output += "You can use the slash commands to manage them:\n\n"
        output += "- `/prompts list` - List all prompts\n"
        output += "- `/prompts view <name>` - View a specific prompt\n"
        output += "- `/prompts edit <name>` - Edit a prompt\n"
        output += "- `/prompts create <name>` - Create a new prompt\n"
        output += "- `/prompts delete <name>` - Delete a prompt\n\n"
        
        output += "---\n\n"
        
        # Group by category
        by_category = {}
        for prompt in prompts:
            category = prompt.get('category', 'Uncategorized')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(prompt)
        
        # Create a table view
        output += "## All Prompts\n\n"
        output += "| Category | Name | Description | Actions |\n"
        output += "|----------|------|-------------|----------|\n"
        
        for category, category_prompts in sorted(by_category.items()):
            for prompt in sorted(category_prompts, key=lambda p: p.get('name', '')):
                name = prompt.get('name', 'Unnamed')
                desc = prompt.get('description', 'No description')[:50]
                if len(prompt.get('description', '')) > 50:
                    desc += "..."
                
                actions = f"[View](/prompts view {name}) | [Edit](/prompts edit {name})"
                output += f"| {category} | {name} | {desc} | {actions} |\n"
        
        output += "\n---\n\n"
        output += "## Quick Stats\n\n"
        output += f"- Total prompts: {len(prompts)}\n"
        output += f"- Categories: {len(by_category)}\n"
        
        for category, category_prompts in sorted(by_category.items()):
            output += f"  - {category}: {len(category_prompts)} prompts\n"
        
        return output


# Global instance
prompt_viewer = PromptViewer()