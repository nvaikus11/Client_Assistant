"""Shared, reusable code across all tools in the workspace.

Import from here rather than re-implementing API, parsing, or prompt logic:
    from shared.claude_client import ClaudeClient
    from shared.doc_parsing import load_engagement, Engagement
    from shared.prompts import load_system_prompt
"""
