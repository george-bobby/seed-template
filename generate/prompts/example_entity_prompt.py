"""
Example prompt for generating entities with context from linked entities.

This demonstrates how to create prompts that include context from other
entities to generate realistic, interconnected data.
"""

from typing import Any

from config.settings import settings


def create_entity_prompt_with_context(
    batch_size: int,
    used_names: set,
    linked_entities: list[dict[str, Any]] | None = None,
    entity_type: str = "entity",
) -> str:
    """
    Creates a prompt for generating entities with context from linked entities.
    
    Args:
        batch_size: Number of entities to generate
        used_names: Set of already used names to avoid duplicates
        linked_entities: List of related entities to provide context
        entity_type: Type of entity being generated
    
    Returns:
        Formatted prompt string
    """
    excluded_names_text = ""
    if used_names:
        recent_names = list(used_names)[-50:] if len(used_names) > 50 else list(used_names)
        excluded_names_text = f"\nExclude these names: {', '.join(recent_names)}"
    
    context_text = ""
    if linked_entities:
        # TODO: Customize this section to match your entity relationships
        # Example: If generating contacts, include company context
        context_examples = []
        for entity in linked_entities[:10]:  # Limit to 10 examples
            entity_info = f"- {entity.get('name', 'Unknown')}"
            # Add other relevant fields from linked entities
            if entity.get('id'):
                entity_info += f" (ID: {entity.get('id')})"
            context_examples.append(entity_info)
        
        if context_examples:
            context_text = f"""
Context from linked {entity_type}s (you may reference these in your generated data):
{chr(10).join(context_examples)}
"""
    
    prompt = f"""
Generate {batch_size} {entity_type}s for a {settings.DATA_THEME_SUBJECT}.

Requirements:
- Each {entity_type} must have a unique name
- Include realistic details appropriate for the context
- If context is provided, create relationships that make sense
- Return as JSON array
{excluded_names_text}
{context_text}
Return format:
[
  {{
    "name": "{entity_type.capitalize()} Name",
    "description": "Description of the {entity_type}",
    // TODO: Add fields specific to your {entity_type} type
    // Example: "companyID": 1, "contactID": 2, etc.
  }}
]
"""
    return prompt


def create_entity_prompt_with_multiple_contexts(
    batch_size: int,
    used_names: set,
    companies: list[dict[str, Any]] | None = None,
    contacts: list[dict[str, Any]] | None = None,
    users: list[dict[str, Any]] | None = None,
) -> str:
    """
    Creates a prompt with context from multiple entity types.
    
    This is useful when generating entities that reference multiple other
    entity types (e.g., a job order that references a company, contact, and recruiter).
    
    Args:
        batch_size: Number of entities to generate
        used_names: Set of already used names
        companies: List of companies for context
        contacts: List of contacts for context
        users: List of users for context
    
    Returns:
        Formatted prompt string
    """
    excluded_names_text = ""
    if used_names:
        recent_names = list(used_names)[-50:] if len(used_names) > 50 else list(used_names)
        excluded_names_text = f"\nExclude these names: {', '.join(recent_names)}"
    
    context_sections = []
    
    if companies:
        company_examples = []
        for company in companies[:10]:
            company_examples.append(f"- {company.get('name', 'Unknown')} (ID: {company.get('id', 'N/A')})")
        if company_examples:
            context_sections.append(f"""
Available Companies (you may reference these):
{chr(10).join(company_examples)}
""")
    
    if contacts:
        contact_examples = []
        for contact in contacts[:10]:
            contact_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
            if not contact_name:
                contact_name = contact.get('name', 'Unknown')
            contact_info = f"- {contact_name}"
            if contact.get('companyID'):
                contact_info += f" (Company ID: {contact.get('companyID')})"
            contact_examples.append(contact_info)
        if contact_examples:
            context_sections.append(f"""
Available Contacts (you may reference these):
{chr(10).join(contact_examples)}
""")
    
    if users:
        user_examples = []
        for user in users[:10]:
            user_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            if not user_name:
                user_name = user.get('username', 'Unknown')
            user_examples.append(f"- {user_name} (ID: {user.get('id', 'N/A')})")
        if user_examples:
            context_sections.append(f"""
Available Users (you may reference these):
{chr(10).join(user_examples)}
""")
    
    context_text = "".join(context_sections)
    
    prompt = f"""
Generate {batch_size} entities for a {settings.DATA_THEME_SUBJECT}.

Requirements:
- Each entity must have a unique name/title
- Include realistic details
- Reference the provided context entities where appropriate
- Create realistic relationships between entities
- Return as JSON array
{excluded_names_text}
{context_text}
Return format:
[
  {{
    "name": "Entity Name",
    "description": "Entity description",
    // TODO: Add fields that reference linked entities
    // Example: "companyID": 1, "contactID": 2, "ownerID": 3
  }}
]
"""
    return prompt
