"""
Example seeding function for an entity type.

This file demonstrates the pattern for creating seeding functions.
Customize this for your application's entity types.
"""

from typing import Any

from tenacity import retry, stop_after_attempt, wait_fixed
from tqdm import tqdm

from config.constants import DEFAULT_SITE_ID, DATA_ENTITIES_FILEPATH
from utils import api_utils
from utils.data_utils import load_existing_data, update_entity_dates, update_entity_owners
from utils.database import get_connection
from common.logger import logger


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def seed_example_entity() -> dict[str, Any]:
    """
    Seed example entities into the application.
    
    Returns:
        dict: Summary of seeded entities
    """
    entities_data = load_existing_data(DATA_ENTITIES_FILEPATH)
    
    # Deduplicate entities
    seen_names = set()
    unique_entities = []
    for entity in entities_data:
        entity_name = entity.get("name", "").strip()
        if not entity_name:
            continue
        entity_name_lower = entity_name.lower()
        if entity_name_lower not in seen_names:
            seen_names.add(entity_name_lower)
            unique_entities.append(entity)
    
    seeded_count = 0
    seeded_entities = []
    
    async with api_utils.app_session():
        for entity in tqdm(unique_entities, desc="Seeding entities"):
            try:
                # TODO: Build form data for your entity type
                form_data = {
                    "name": entity.get("name", ""),
                    # Add other required fields here
                }
                
                # TODO: Use your application's endpoint
                result = await api_utils.submit_form("/api/entities/add", form_data)
                
                if result and result.get("status_code") == 200:
                    entity_id = result.get("entity_id")
                    if entity_id:
                        seeded_entities.append({
                            "original_data": entity,
                            "entity_id": entity_id,
                            "status": "success"
                        })
                        seeded_count += 1
                else:
                    logger.warning(f"Failed to seed entity: {entity.get('name')}")
            except Exception as e:
                logger.error(f"Error seeding entity {entity.get('name')}: {e}")
    
    # Update entity dates and owners
    if seeded_entities:
        await update_entity_dates(
            seeded_entities,
            unique_entities,
            "entity_table",  # TODO: Replace with your table name
            "entity_id",  # TODO: Replace with your ID column name
            "entity_id",  # TODO: Replace with your seeded ID key
            name_key="name"
        )
        await update_entity_owners(
            seeded_entities,
            "entity_table",  # TODO: Replace with your table name
            "entity_id",  # TODO: Replace with your ID column name
            "entity_id"  # TODO: Replace with your seeded ID key
        )
    
    logger.info(f"Seeded {seeded_count} entities")
    return {"seeded_entities": seeded_count, "details": seeded_entities}

