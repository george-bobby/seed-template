# Prompts for Data Generation

This folder contains prompt templates for generating seed data with proper context from linked entities.

## Purpose

When generating seed data, it's important to include context from related entities to ensure:
- **Realistic relationships**: Generated entities reference existing entities appropriately
- **Data consistency**: Relationships between entities make logical sense
- **Better quality**: AI-generated data is more realistic when it has context

## Structure

Each prompt file should contain functions that:
1. Accept context from linked entities
2. Format prompts with that context
3. Return prompts ready to send to the AI API

## Example Usage

```python
from generate.prompts.example_entity_prompt import create_entity_prompt_with_context

# Load existing entities for context
existing_companies = load_existing_data(COMPANIES_FILEPATH)
existing_contacts = load_existing_data(CONTACTS_FILEPATH)

# Create prompt with context
prompt = create_entity_prompt_with_context(
    batch_size=10,
    used_names=used_contact_names,
    linked_entities=existing_companies,  # Contacts belong to companies
    entity_type="contact"
)

# Use prompt for generation
response = await make_anthropic_request(prompt=prompt, ...)
```

## Creating Your Own Prompts

1. **Identify entity relationships**: Determine which entities reference others
   - Example: Contacts → Companies, Job Orders → Companies & Contacts

2. **Create prompt functions**: Write functions that accept linked entity context
   ```python
   def create_my_entity_prompt(
       batch_size: int,
       used_names: set,
       linked_entities: list[dict] | None = None
   ) -> str:
       # Build context section
       # Format prompt with context
       return prompt
   ```

3. **Include relevant context**: Only include context that's relevant to the entity being generated
   - Don't include all fields, just key identifying information
   - Limit to 10-20 examples to avoid token limits

4. **Specify relationships**: In your prompt, tell the AI how to use the context
   - Example: "Each contact should reference one of the provided companies"

## Best Practices

- **Limit context size**: Include 10-20 examples max to avoid token limits
- **Use IDs**: Include entity IDs so generated data can reference them
- **Be specific**: Tell the AI exactly how to use the context
- **Validate relationships**: After generation, validate that references are correct
- **Iterate**: Refine prompts based on generated data quality

## Template Files

- `example_entity_prompt.py`: Basic example with single entity context
- Create additional files for each entity type that needs context
