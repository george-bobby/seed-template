from enum import Enum

from config.settings import settings


# Example: Default entity counts for data generation
DEFAULT_ENTITIES_COUNT = 50
DEFAULT_BATCH_SIZE = 5

# Example: API endpoint enum pattern
class AppEndpoint(Enum):
    """Example enum for API endpoints. Customize for your application."""
    LOGIN = "/api/login"
    ENTITY_ADD = "/api/entities/add"
    ENTITY_EDIT = "/api/entities/edit"
    ENTITY_LIST = "/api/entities/list"


# Example: Data item type enum pattern
class DataItemType(Enum):
    """Example enum for data item types. Customize for your application."""
    ENTITY_TYPE_1 = 100
    ENTITY_TYPE_2 = 200
    ENTITY_TYPE_3 = 300


# Example: Custom field type enum pattern
class CustomFieldType(Enum):
    """Example enum for custom field types. Customize for your application."""
    CHECKBOX = 1
    DATE = 2
    DROPDOWN = 3
    RADIO = 4


# Example: File paths for data files
DATA_ENTITIES_FILENAME = "entities.json"
DATA_ENTITIES_FILEPATH = settings.DATA_PATH / DATA_ENTITIES_FILENAME

# Example: Date patterns for parsing
DATE_PATTERNS = {
    "%Y-%m-%d %H:%M:%S": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
    "%Y-%m-%d": r"^\d{4}-\d{2}-\d{2}$",
}

# Example: Batch sizes for processing
ENTITIES_BATCH_SIZE = 5

# Example: Site/tenant configuration
DEFAULT_SITE_ID = 1
