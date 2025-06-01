"""
Slash command handler for MCP Agent.

This module provides slash command support for quick actions and shortcuts.
"""

import re
from typing import Dict, Tuple, Optional, List, Callable, Any
from dataclasses import dataclass
import json

from ..logging import logger
from .prompt_viewer import prompt_viewer


@dataclass
class SlashCommand:
    """Represents a slash command definition."""
    name: str
    description: str
    handler: Callable
    usage: str
    aliases: List[str] = None


class SlashCommandHandler:
    """Handles parsing and execution of slash commands."""
    
    def __init__(self):
        self.commands: Dict[str, SlashCommand] = {}
        self.pending_format_requests: Dict[str, str] = {}  # Track commands that need formatting
        self._register_default_commands()
    
    def _register_default_commands(self):
        """Register built-in slash commands."""
        # Travel assistant initialization
        self.register_command(
            name="travel",
            description="Initialize the travel assistant",
            handler=self._handle_travel_init,
            usage="/travel or /t",
            aliases=["t", "init-travel", "travel-init", "start"]
        )
        
        # Quick travel initialization alias
        self.register_command(
            name="go",
            description="Quick start travel assistant (alias for /travel)",
            handler=self._handle_travel_init,
            usage="/go",
            aliases=["g", "init"]
        )
        
        # Prompt management
        self.register_command(
            name="prompts",
            description="View and manage D1 database prompts",
            handler=self._handle_prompts,
            usage="/prompts [list|view|dashboard|search|category|edit|create|delete|update]",
            aliases=["p", "prompt"]
        )
        
        # Servers command
        self.register_command(
            name="servers",
            description="List available MCP servers",
            handler=self._handle_servers,
            usage="/servers",
            aliases=["s", "list-servers"]
        )
        
        # Connect command
        self.register_command(
            name="connect",
            description="Connect to an MCP server",
            handler=self._handle_connect,
            usage="/connect <server-name>",
            aliases=["c"]
        )
        
        # Tools command
        self.register_command(
            name="tools",
            description="List available tools",
            handler=self._handle_tools,
            usage="/tools [server-name]",
            aliases=["tool", "list-tools"]
        )
        
        # Help command
        self.register_command(
            name="help",
            description="Show available slash commands",
            handler=self._handle_help,
            usage="/help [command]",
            aliases=["h", "?"]
        )
        
        # Quick prompt creation
        self.register_command(
            name="create-prompt",
            description="Quick create a new prompt",
            handler=self._handle_create_prompt,
            usage="/create-prompt <name>",
            aliases=["cp", "new-prompt"]
        )
    
    def register_command(self, name: str, description: str, handler: Callable, 
                        usage: str, aliases: List[str] = None):
        """Register a new slash command."""
        command = SlashCommand(name, description, handler, usage, aliases or [])
        self.commands[name] = command
        
        # Register aliases
        for alias in command.aliases or []:
            self.commands[alias] = command
    
    def parse_command(self, input_text: str) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
        """Parse input to extract slash command and arguments.
        
        Returns:
            Tuple of (command_name, subcommand, arguments) or (None, None, None) if not a command
        """
        if not input_text.startswith('/'):
            return None, None, None
        
        # Remove the leading slash
        command_text = input_text[1:].strip()
        
        # Split into parts
        parts = command_text.split()
        if not parts:
            return None, None, None
        
        command_name = parts[0].lower()
        subcommand = parts[1] if len(parts) > 1 else None
        args = parts[2:] if len(parts) > 2 else []
        
        return command_name, subcommand, args
    
    def is_slash_command(self, input_text: str) -> bool:
        """Check if input is a slash command."""
        return input_text.strip().startswith('/')
    
    async def execute_command(self, input_text: str, agent) -> Optional[str]:
        """Execute a slash command if found.
        
        Args:
            input_text: The user input
            agent: The MCPAgent instance
            
        Returns:
            Command output or None if not a slash command
        """
        command_name, subcommand, args = self.parse_command(input_text)
        
        if command_name not in self.commands:
            return f"Unknown command: /{command_name}. Use /help for available commands."
        
        command = self.commands[command_name]
        try:
            result = await command.handler(agent, subcommand, args)
            
            # Track which commands need result formatting
            if command_name == "prompts" and result.startswith("use_tool_from_server"):
                # Store the command for post-processing
                self.pending_format_requests[input_text] = f"{command_name}:{subcommand or 'list'}"
            
            return result
        except Exception as e:
            logger.error(f"Error executing command /{command_name}: {e}")
            return f"Error executing command: {str(e)}"
    
    # Command handlers
    async def _handle_travel_init(self, agent, subcommand: Optional[str], args: List[str]) -> str:
        """Initialize the travel assistant with various options."""
        
        # Check available prompts
        if subcommand == "check":
            self.pending_format_requests["/travel check"] = "prompts:list"
            return "use_tool_from_server d1-database query {\"query\": \"SELECT name, description, category FROM prompts WHERE category IN ('travel', 'system', 'travel_system', 'assistant') ORDER BY category, name\"}"
        
        # Load from D1 database
        elif subcommand == "db":
            # Try to load the main travel system prompt
            self.pending_format_requests["/travel db"] = "travel:init"
            return "use_tool_from_server d1-database query {\"query\": \"SELECT content FROM prompts WHERE name IN ('travel_assistant_system', 'travel_system_prompt', 'main_travel_prompt', 'travel_agent_instructions') ORDER BY CASE name WHEN 'travel_assistant_system' THEN 1 WHEN 'travel_system_prompt' THEN 2 WHEN 'main_travel_prompt' THEN 3 ELSE 4 END LIMIT 1\"}"
        
        # Load and combine multiple prompts
        elif subcommand == "full":
            # Load multiple prompts and combine them
            self.pending_format_requests["/travel full"] = "travel:full_init"
            return "use_tool_from_server d1-database query {\"query\": \"SELECT name, content FROM prompts WHERE category = 'travel' OR name LIKE '%travel%' ORDER BY name\"}"
        
        # Load specific prompt by name
        elif subcommand == "load":
            if not args:
                return "Please specify a prompt name. Usage: /travel load <prompt_name>"
            prompt_name = " ".join(args)
            self.pending_format_requests[f"/travel load {prompt_name}"] = "travel:load_specific"
            return f"use_tool_from_server d1-database query {{\"query\": \"SELECT content FROM prompts WHERE name = '{prompt_name}' LIMIT 1\"}}"
        
        # Setup mode - interactive setup
        elif subcommand == "setup":
            return self._travel_setup_wizard()
        
        # List available initialization methods
        elif subcommand == "help":
            return self._travel_init_help()
        
        # Custom initialization with specific components
        elif subcommand == "custom":
            return self._travel_custom_init(args)
        
        # Default: Try prompt-server, then fallback to database
        else:
            # Store for potential fallback handling
            self.pending_format_requests["/travel"] = "travel:default"
            return "use_tool_from_server prompt-server initialize_travel_assistant"
    
    def should_format_result(self, command_text: str) -> bool:
        """Check if a command's result should be formatted."""
        return command_text in self.pending_format_requests
    
    def format_command_result(self, command_text: str, result: str) -> str:
        """Format the result of a command based on its type."""
        if command_text not in self.pending_format_requests:
            return result
        
        format_info = self.pending_format_requests.pop(command_text)
        command_type, subcommand = format_info.split(":")
        
        if command_type == "prompts":
            return self._format_prompt_result(subcommand, result)
        elif command_type == "travel":
            return self._format_travel_result(subcommand, result)
        
        return result
    
    def _format_prompt_result(self, subcommand: str, result: str) -> str:
        """Format prompt-related command results."""
        try:
            # Check for common error messages first
            if isinstance(result, str):
                lower_result = result.lower()
                if any(error in lower_result for error in [
                    "failed to connect", "connection error", "database error",
                    "server error", "timeout", "not found: d1-database"
                ]):
                    return f"❌ Database Error: {result}\n\n" \
                           "Please ensure the D1 database server is running and accessible.\n" \
                           "You can check available servers with `/servers` command."
            
            # Parse the database result
            db_results = prompt_viewer.parse_db_results(result)
            
            # Check if we got empty results due to an error
            if not db_results and "error" in result.lower():
                return f"❌ Database query failed: {result}"
            
            if subcommand in ["list", "dashboard"]:
                if not db_results:
                    return "No prompts found in the database. The prompts table may be empty or there was an error connecting to the database."
                return prompt_viewer.format_prompt_list(db_results)
            elif subcommand == "view":
                if db_results:
                    return prompt_viewer.format_prompt_detail(db_results[0])
                else:
                    return "Prompt not found. Please check the prompt name and try again."
            elif subcommand == "search":
                if db_results:
                    return prompt_viewer.format_prompt_list(db_results)
                else:
                    return "No prompts found matching your search criteria."
            elif subcommand == "category":
                if db_results and len(db_results) > 0 and 'count' in str(db_results[0]):
                    # Category listing
                    output = "# Prompt Categories\n\n"
                    for row in db_results:
                        category = row.get('category', 'Unknown')
                        count = row.get('count', 0)
                        output += f"- **{category}**: {count} prompts\n"
                    return output
                elif db_results:
                    # Prompts in category
                    return prompt_viewer.format_prompt_list(db_results)
                else:
                    return "No prompts found in this category."
            elif subcommand == "edit":
                if db_results:
                    prompt = db_results[0]
                    return prompt_viewer.format_prompt_detail(prompt) + "\n\n---\n\nTo edit this prompt, provide the updated content."
                else:
                    return "Prompt not found. Please check the prompt name and try again."
            elif subcommand == "delete":
                # For delete operations, check if successful
                if "error" in result.lower():
                    return f"❌ Failed to delete prompt: {result}"
                else:
                    return "✅ Prompt deleted successfully."
            else:
                return result
        except Exception as e:
            logger.error(f"Error formatting prompt result: {e}")
            return f"❌ Error processing command result: {str(e)}\n\nRaw result: {result}"
    
    def _format_travel_result(self, subcommand: str, result: str) -> str:
        """Format travel initialization results."""
        try:
            # Handle different travel initialization scenarios
            if subcommand == "default":
                # Check if we got the pricing prompt instead of travel assistant
                if "pricing" in result.lower() or "tier" in result.lower():
                    return f"⚠️ **Unexpected Response from Prompt Server**\n\n" \
                           f"The prompt server returned a pricing system prompt instead of the travel assistant.\n\n" \
                           f"**Try these alternatives:**\n" \
                           f"1. `/travel db` - Load from database\n" \
                           f"2. `/travel check` - See available prompts\n" \
                           f"3. `/travel setup` - Use setup wizard\n" \
                           f"4. `/travel load <prompt_name>` - Load specific prompt\n\n" \
                           f"**Received:**\n{result[:200]}..."
                else:
                    # Successful initialization
                    return f"✅ **Travel Assistant Initialized**\n\n{result}"
            
            elif subcommand == "init":
                # Database initialization result
                db_results = prompt_viewer.parse_db_results(result)
                if db_results and db_results[0].get('content'):
                    content = db_results[0]['content']
                    return f"✅ **Travel Assistant Loaded from Database**\n\n{content}"
                else:
                    return "❌ No travel assistant prompt found in database.\n\n" \
                           "Please create one with:\n" \
                           "`/prompts create travel_assistant_system`"
            
            elif subcommand == "full_init":
                # Multiple prompts loaded
                db_results = prompt_viewer.parse_db_results(result)
                if db_results:
                    output = "✅ **Travel Assistant Components Loaded**\n\n"
                    for prompt in db_results:
                        output += f"**{prompt.get('name', 'Unknown')}**\n"
                        content = prompt.get('content', '')[:200]
                        output += f"{content}...\n\n"
                    return output
                else:
                    return "❌ No travel prompts found in database."
            
            elif subcommand == "load_specific":
                # Specific prompt loaded
                db_results = prompt_viewer.parse_db_results(result)
                if db_results and db_results[0].get('content'):
                    content = db_results[0]['content']
                    return f"✅ **Prompt Loaded Successfully**\n\n{content}"
                else:
                    return "❌ Prompt not found. Check the name and try again."
            
            elif subcommand == "custom_init":
                # Custom components loaded
                db_results = prompt_viewer.parse_db_results(result)
                if db_results:
                    output = "✅ **Custom Travel Assistant Initialized**\n\n"
                    output += "**Loaded Components:**\n"
                    for prompt in db_results:
                        output += f"- {prompt.get('name', 'Unknown')}\n"
                    
                    # Combine all prompts
                    combined = "\n\n---\n\n".join([p.get('content', '') for p in db_results])
                    output += f"\n**Combined Instructions:**\n{combined[:500]}..."
                    return output
                else:
                    return "❌ No matching components found in database."
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting travel result: {e}")
            return f"❌ Error processing travel initialization: {str(e)}"
    
    async def _handle_prompts(self, agent, subcommand: Optional[str], args: List[str]) -> str:
        """Handle prompt management commands."""
        if not subcommand or subcommand == "list":
            # List all prompts from D1 database with enhanced formatting
            return "use_tool_from_server d1-database query {\"query\": \"SELECT name, description, category, tags, updated_at FROM prompts ORDER BY category, name\"}"
        
        elif subcommand == "view":
            if not args:
                return "Please specify a prompt name. Usage: /prompts view <prompt_name>"
            prompt_name = " ".join(args)
            return f"use_tool_from_server d1-database query {{\"query\": \"SELECT * FROM prompts WHERE name = '{prompt_name}' LIMIT 1\"}}"
        
        elif subcommand == "dashboard":
            # Show comprehensive prompt dashboard
            return "use_tool_from_server d1-database query {\"query\": \"SELECT name, description, category, tags, created_at, updated_at FROM prompts ORDER BY category, name\"}"
        
        elif subcommand == "search":
            if not args:
                return "Please specify search terms. Usage: /prompts search <keywords>"
            search_term = " ".join(args)
            return f"use_tool_from_server d1-database query {{\"query\": \"SELECT name, description, category FROM prompts WHERE name LIKE '%{search_term}%' OR description LIKE '%{search_term}%' OR content LIKE '%{search_term}%' ORDER BY name\"}}"
        
        elif subcommand == "category":
            if not args:
                # List all categories
                return "use_tool_from_server d1-database query {\"query\": \"SELECT DISTINCT category, COUNT(*) as count FROM prompts GROUP BY category ORDER BY category\"}"
            else:
                # List prompts in specific category
                category = " ".join(args)
                return f"use_tool_from_server d1-database query {{\"query\": \"SELECT name, description FROM prompts WHERE category = '{category}' ORDER BY name\"}}"
        
        elif subcommand == "edit":
            if not args:
                return "Please specify a prompt name. Usage: /prompts edit <prompt_name>"
            prompt_name = " ".join(args)
            # Return instructions for editing
            return f"To edit the prompt '{prompt_name}', follow these steps:\n\n" \
                   f"1. First view the prompt: `/prompts view {prompt_name}`\n" \
                   f"2. Then update specific fields: `/prompts update {prompt_name} <field> <new_value>`\n\n" \
                   f"Available fields: name, description, content, category, tags\n\n" \
                   f"Example: `/prompts update {prompt_name} description New description here`"
        
        elif subcommand == "create":
            if not args:
                return "Please specify a prompt name. Usage: /prompts create <prompt_name>"
            prompt_name = " ".join(args)
            # Store the prompt name for the creation workflow
            self.pending_format_requests[f"create:{prompt_name}"] = "create_workflow"
            return f"Creating new prompt '{prompt_name}'.\n\n" \
                   f"Please provide the following details:\n" \
                   f"1. **Description**: Brief description of the prompt\n" \
                   f"2. **Category**: Category for organization (e.g., 'travel', 'general', 'technical')\n" \
                   f"3. **Content**: The actual prompt content\n" \
                   f"4. **Tags** (optional): Comma-separated tags\n\n" \
                   f"Example format:\n" \
                   f"```\n" \
                   f"Description: A helpful travel planning assistant\n" \
                   f"Category: travel\n" \
                   f"Content: You are a knowledgeable travel assistant...\n" \
                   f"Tags: travel, planning, assistant\n" \
                   f"```"
        
        elif subcommand == "update":
            if len(args) < 2:
                return "Please specify prompt name and field to update. Usage: /prompts update <prompt_name> <field> <new_value>"
            prompt_name = args[0]
            field = args[1]
            new_value = " ".join(args[2:]) if len(args) > 2 else ""
            
            # Validate field
            valid_fields = ["description", "content", "category", "tags"]
            if field not in valid_fields:
                return f"Invalid field '{field}'. Valid fields: {', '.join(valid_fields)}"
            
            if not new_value:
                return f"Please provide a new value for {field}."
            
            # Build the update query
            if field == "tags":
                # Handle tags as JSON array
                tags_list = [tag.strip() for tag in new_value.split(',')]
                tags_json = json.dumps(tags_list)
                update_query = f"UPDATE prompts SET {field} = '{tags_json}', updated_at = CURRENT_TIMESTAMP WHERE name = '{prompt_name}'"
            else:
                # Escape single quotes in the value
                escaped_value = new_value.replace("'", "''")
                update_query = f"UPDATE prompts SET {field} = '{escaped_value}', updated_at = CURRENT_TIMESTAMP WHERE name = '{prompt_name}'"
            
            return f"use_tool_from_server d1-database execute {{\"query\": \"{update_query}\"}}"
        
        elif subcommand == "delete":
            if not args:
                return "Please specify a prompt name. Usage: /prompts delete <prompt_name>"
            prompt_name = " ".join(args)
            return f"use_tool_from_server d1-database execute {{\"query\": \"DELETE FROM prompts WHERE name = '{prompt_name}'\"}}"
        
        else:
            return f"Unknown subcommand: {subcommand}. Available: list, view, dashboard, search, category, edit, create, update, delete"
    
    def _travel_setup_wizard(self) -> str:
        """Interactive travel assistant setup wizard."""
        return """# 🧙 Travel Assistant Setup Wizard

Welcome! Let's set up your travel assistant. Choose your configuration:

## 1. Quick Setup Options:

**A) Standard Travel Agent** `/travel load travel_agent_standard`
- Full-service travel planning
- Flight, hotel, and activity recommendations
- Budget optimization

**B) Luxury Travel Specialist** `/travel load luxury_travel_agent`
- High-end travel planning
- Exclusive experiences
- Premium service focus

**C) Budget Travel Expert** `/travel load budget_travel_expert`
- Cost-effective travel solutions
- Deals and savings focus
- Value optimization

**D) Adventure Travel Guide** `/travel load adventure_travel_guide`
- Outdoor and adventure focus
- Off-the-beaten-path destinations
- Activity-based planning

## 2. Custom Setup:
Use `/travel custom [components]` with any combination:
- `flights` - Flight search and booking assistance
- `hotels` - Accommodation recommendations
- `activities` - Tours and experiences
- `itinerary` - Day-by-day planning
- `budget` - Cost optimization
- `safety` - Travel advisories and safety info

Example: `/travel custom flights hotels itinerary`

## 3. Manual Setup:
- Check available prompts: `/travel check`
- Load specific prompt: `/travel load <prompt_name>`
- View prompt first: `/prompts view <prompt_name>`

What would you like to set up?"""

    def _travel_init_help(self) -> str:
        """Help text for travel initialization options."""
        return """# Travel Assistant Initialization Options

## Quick Start:
- `/t` or `/travel` - Default initialization (uses prompt-server)
- `/go` - Alias for quick start

## Initialization Methods:
- `/travel check` - List available travel prompts
- `/travel db` - Load from database (fallback)
- `/travel full` - Load all travel-related prompts
- `/travel load <name>` - Load specific prompt by name
- `/travel setup` - Interactive setup wizard
- `/travel custom [options]` - Custom initialization

## Examples:
```
/travel check                    # See what's available
/travel load travel_agent_pro    # Load specific prompt
/travel custom flights hotels    # Custom setup
/travel setup                    # Guided setup
```

## Troubleshooting:
- If default `/t` returns unexpected content, try `/travel db`
- To see all prompts: `/prompts list`
- To search prompts: `/prompts search travel`
- To view a prompt: `/prompts view <name>`

## Creating New Prompts:
```
/prompts create my_travel_assistant
/prompts update my_travel_assistant content "Your prompt here..."
/prompts update my_travel_assistant category travel
```"""

    def _travel_custom_init(self, components: List[str]) -> str:
        """Custom travel initialization with specific components."""
        if not components:
            return """Please specify components for custom initialization.
            
Available components:
- `flights` - Flight search and booking
- `hotels` - Accommodation services  
- `activities` - Tours and experiences
- `itinerary` - Trip planning
- `budget` - Cost optimization
- `safety` - Travel safety info
- `luxury` - Premium services
- `business` - Business travel

Example: `/travel custom flights hotels itinerary`"""
        
        # Build a custom initialization based on components
        component_prompts = {
            "flights": "flight_booking_assistant",
            "hotels": "hotel_booking_assistant", 
            "activities": "activity_planning_assistant",
            "itinerary": "itinerary_builder",
            "budget": "budget_optimizer",
            "safety": "travel_safety_advisor",
            "luxury": "luxury_travel_specialist",
            "business": "business_travel_assistant"
        }
        
        selected_prompts = []
        for comp in components:
            if comp.lower() in component_prompts:
                selected_prompts.append(component_prompts[comp.lower()])
        
        if not selected_prompts:
            return f"No valid components found. Available: {', '.join(component_prompts.keys())}"
        
        # Load multiple prompts
        prompt_list = "', '".join(selected_prompts)
        self.pending_format_requests[f"/travel custom {' '.join(components)}"] = "travel:custom_init"
        return f"use_tool_from_server d1-database query {{\"query\": \"SELECT name, content FROM prompts WHERE name IN ('{prompt_list}') OR (category = 'travel' AND name LIKE '%base%')\"}}"

    async def _handle_servers(self, agent, subcommand: Optional[str], args: List[str]) -> str:
        """List available MCP servers."""
        # This will be handled by the agent's server manager tools
        return "Please list the available MCP servers."
    
    async def _handle_connect(self, agent, subcommand: Optional[str], args: List[str]) -> str:
        """Connect to an MCP server."""
        if not subcommand:
            return "Please specify a server name. Usage: /connect <server-name>"
        # This will be handled by the agent's server manager tools
        return f"Please connect to the MCP server named '{subcommand}'."
    
    async def _handle_tools(self, agent, subcommand: Optional[str], args: List[str]) -> str:
        """List available tools."""
        if subcommand:
            # List tools from specific server
            return f"Please search for tools available on the '{subcommand}' server."
        else:
            # List all tools
            return "Please search for all available MCP tools."
    
    async def _handle_create_prompt(self, agent, subcommand: Optional[str], args: List[str]) -> str:
        """Quick create a new prompt."""
        if not subcommand:
            return "Please specify a prompt name. Usage: /create-prompt <name>"
        
        prompt_name = subcommand
        if args:
            prompt_name = f"{subcommand} {' '.join(args)}"
        
        return f"To create the prompt '{prompt_name}', please provide the following information:\n\n" \
               f"**Name:** {prompt_name}\n" \
               f"**Description:** (Brief description of what this prompt does)\n" \
               f"**Category:** (e.g., travel, system, utility)\n" \
               f"**Content:** (The actual prompt text)\n" \
               f"**Tags:** (Comma-separated tags, optional)\n\n" \
               f"You can create it with:\n" \
               f"`/prompts create {prompt_name}`\n\n" \
               f"Then use `/prompts update {prompt_name} <field> <value>` to set each field."
    
    async def _handle_help(self, agent, subcommand: Optional[str], args: List[str]) -> str:
        """Show help for commands."""
        if subcommand:
            # Show help for specific command
            if subcommand in self.commands:
                cmd = self.commands[subcommand]
                return f"**/{cmd.name}** - {cmd.description}\nUsage: {cmd.usage}"
            else:
                return f"Unknown command: {subcommand}"
        
        # Show all commands
        unique_commands = {}
        for name, cmd in self.commands.items():
            # Skip aliases
            if cmd.name not in unique_commands:
                unique_commands[cmd.name] = cmd
        
        help_text = "**Available slash commands:**\n\n"
        for cmd in unique_commands.values():
            aliases_text = f" (aliases: {', '.join(['/' + a for a in cmd.aliases])})" if cmd.aliases else ""
            help_text += f"• **/{cmd.name}** - {cmd.description}{aliases_text}\n"
            help_text += f"  Usage: {cmd.usage}\n\n"
        
        return help_text
    
    async def _handle_create_prompt(self, agent, subcommand: Optional[str], args: List[str]) -> str:
        """Create a new prompt with structured input."""
        if len(args) < 4:
            return "Usage: /create-prompt <name> <description> <category> <content> [tags]\n" \
                   "Example: /create-prompt travel-assistant 'Helpful travel planner' travel 'You are a travel assistant...' 'travel,planning'"
        
        name = args[0]
        description = args[1]
        category = args[2]
        content = args[3]
        tags = args[4] if len(args) > 4 else ""
        
        # Build the INSERT query
        tags_json = json.dumps([tag.strip() for tag in tags.split(',')]) if tags else "[]"
        
        # Escape single quotes
        description = description.replace("'", "''")
        content = content.replace("'", "''")
        
        insert_query = f"INSERT INTO prompts (name, description, category, content, tags, created_at, updated_at) " \
                      f"VALUES ('{name}', '{description}', '{category}', '{content}', '{tags_json}', " \
                      f"CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        
        return f"use_tool_from_server d1-database execute {{\"query\": \"{insert_query}\"}}"


# Global instance
slash_command_handler = SlashCommandHandler()