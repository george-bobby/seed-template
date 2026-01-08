"""
Example data generation function.

This file demonstrates the pattern for generating seed data using AI.
Customize this for your application's data generation needs.

For prompts with context from linked entities, see generate/prompts/
"""

import random
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from config.constants import DATA_ENTITIES_FILEPATH, DEFAULT_ENTITIES_COUNT, ENTITIES_BATCH_SIZE
from config.settings import settings
from utils.api_utils import make_anthropic_request, parse_anthropic_response
from utils.data_utils import load_existing_data, save_json_file
from common.logger import logger

# TODO: Import prompt functions from generate/prompts/ when you need context from linked entities
# Example:
# from generate.prompts.example_entity_prompt import create_entity_prompt_with_context


def create_entities_prompt(used_names: set, batch_size: int, linked_entities: list[dict[str, Any]] | None = None) -> str:
    """
    Create a prompt for generating entities.
    
    For simple entities without relationships, use this function.
    For entities that need context from linked entities, use functions from generate/prompts/
    
    Args:
        used_names: Set of already used names to avoid duplicates
        batch_size: Number of entities to generate
        linked_entities: Optional list of related entities for context (not used in simple version)
    """
    excluded_names_text = ""
    if used_names:
        recent_names = list(used_names)[-50:] if len(used_names) > 50 else list(used_names)
        excluded_names_text = f"\nExclude these names: {', '.join(recent_names)}"
    
    prompt = f"""
Generate {batch_size} example entities for {settings.DATA_THEME_SUBJECT}.

Requirements:
- Each entity must have a unique name
- Include realistic details
- Return as JSON array
{excluded_names_text}

Return format:
[
  {{
    "name": "Entity Name",
    "description": "Entity description",
    // Add other fields as needed
  }}
]
"""
    return prompt


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def generate_example_entities() -> list[dict[str, Any]]:
    """
    Generate example entities using AI.
    
    Returns:
        list: Generated entity data
    """
    existing = load_existing_data(DATA_ENTITIES_FILEPATH)
    used_names = {e.get("name", "").lower() for e in existing if e.get("name")}
    
    target_count = DEFAULT_ENTITIES_COUNT
    current_count = len(existing)
    needed = max(0, target_count - current_count)
    
    if needed == 0:
        logger.info("No new entities needed")
        return existing
    
    new_entities = []
    batches = (needed + ENTITIES_BATCH_SIZE - 1) // ENTITIES_BATCH_SIZE
    
    for batch_num in tqdm(range(batches), desc="Generating entities"):
        batch_size = min(ENTITIES_BATCH_SIZE, needed - len(new_entities))
        if batch_size <= 0:
            break
        
        prompt = create_entities_prompt(used_names, batch_size)
        
        try:
            response = await make_anthropic_request(
                prompt=prompt,
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.DEFAULT_MODEL,
            )
            
            batch_entities = parse_anthropic_response(response)
            
            for entity in batch_entities:
                entity_name = entity.get("name", "").strip()
                if entity_name and entity_name.lower() not in used_names:
                    used_names.add(entity_name.lower())
                    new_entities.append(entity)
        except Exception as e:
            logger.error(f"Error generating batch {batch_num + 1}: {e}")
    
    all_entities = existing + new_entities
    save_json_file(DATA_ENTITIES_FILEPATH, all_entities)
    logger.info(f"Generated {len(new_entities)} new entities")
    return all_entities


async def example_entities() -> None:
    """Main function to generate example entities."""
    await generate_example_entities()

