import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from config.constants import (
    DATE_PATTERNS,
)
from config.settings import settings
from common.logger import logger


def safe_int(value: Any) -> int:
    """Safely converts a value to an integer, raising ValueError if conversion fails."""
    if value is None:
        raise ValueError("Cannot convert None to int")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
            return int(stripped)
    raise ValueError(f"Cannot convert value '{value}' to int")


def safe_strptime(date_str: str, format_str: str) -> datetime | None:
    """Safely parses a date string into a datetime object, returning None on failure."""
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None


def parse_app_date(date_value: str | datetime | None) -> datetime | None:
    """
    Parses a date value (string or datetime) into a datetime object using various formats.
    TODO: Customize supported date formats for your application.
    """
    if date_value is None:
        return None
    if isinstance(date_value, datetime):
        return date_value
    if not isinstance(date_value, str):
        logger.warning(f"Cannot parse date: date_value is not a string or datetime, got {type(date_value)}")
        return None
    
    # TODO: Add/remove date formats relevant to your application
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m-%d-%y", "%m/%d/%Y", "%m-%d-%Y"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_value, fmt)
            return parsed
        except ValueError:
            continue
    logger.warning(f"Cannot parse date '{date_value}' with any of the supported formats")
    return None


def format_app_date(date_value: str | datetime | None, target_format: str = "%m-%d-%y") -> str:
    """
    Formats a date value (string or datetime) into a specified string format.
    TODO: Customize default target format if needed.
    """
    if date_value is None:
        return ""
    
    if isinstance(date_value, datetime):
        return date_value.strftime(target_format)
    
    if isinstance(date_value, str):
        parsed_date = parse_app_date(date_value)
        if parsed_date:
            return parsed_date.strftime(target_format)
        return date_value  # Return original string if parsing fails
    
    return str(date_value)


def format_phone_number(phone: str | None) -> str:
    """
    Formats a raw phone number string into a standard (XXX) XXX-XXXX format.
    TODO: Customize phone number formatting for your application's region/requirements.
    """
    if not phone:
        return ""

    phone = str(phone)
    digits = "".join(filter(str.isdigit, phone))

    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return as is if not a standard 10/11 digit US number


def format_url(url: str) -> str:
    """Ensures a URL has a scheme (http/https)."""
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def is_valid_date_format(date_str: str, format_str: str) -> bool:
    """Checks if a date string matches a specific format using regex patterns."""
    if not date_str or not isinstance(date_str, str):
        return False

    pattern = DATE_PATTERNS.get(format_str)
    if not pattern:
        return False

    return bool(re.match(pattern, date_str))


def skip_weekend(date: datetime) -> datetime:
    """Adjusts a date to skip weekends (moves to Monday)."""
    weekday = date.weekday()
    if weekday == 5:  # Saturday
        date = date + timedelta(days=2)
    elif weekday == 6:  # Sunday
        date = date + timedelta(days=1)
    return date


def calculate_activity_date(
    base_time: datetime,
    min_days: int,
    max_days: int,
    min_entity_date: datetime | None = None,
    is_recent_activity: bool = False,
    is_past_activity: bool = False,
    days_offset: int = 0,
    apply_weekend_skip: bool = False,
) -> datetime:
    """
    Calculates a random activity date within a specified range,
    considering base time, entity creation date, and weekend skips.
    """
    if is_recent_activity:
        days_ago = days_offset if is_past_activity else -days_offset
    elif min_days == 0 and max_days == 30:  # Special handling for shorter ranges
        rand = random.random()
        if rand < 0.3:
            days_ago = random.randint(0, 7)
        elif rand < 0.7:
            days_ago = random.randint(8, 20)
        else:
            days_ago = random.randint(21, 30)
    else:
        days_ago = random.randint(min_days, max_days)
    
    hours = random.randint(8, 17)
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    
    activity_date = base_time - timedelta(days=days_ago)
    activity_date = activity_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    
    if apply_weekend_skip:
        activity_date = skip_weekend(activity_date)
    
    if min_entity_date and activity_date < min_entity_date:
        # Ensure activity doesn't predate the entity it's related to
        days_after_entity = random.randint(1, 30)
        activity_date = min_entity_date + timedelta(days=days_after_entity)
        activity_date = activity_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
        
        if activity_date > base_time:  # If adjusting pushed it into the future
            days_available = (base_time - min_entity_date).days
            if days_available > 0:
                days_after_entity = random.randint(1, max(1, days_available))
                activity_date = min_entity_date + timedelta(days=days_after_entity)
                activity_date = activity_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
            else:  # If entity is very recent, place activity very recently
                minutes_ago = random.randint(1, 1440)
                seconds_ago = random.randint(0, 59)
                activity_date = base_time - timedelta(minutes=minutes_ago, seconds=seconds_ago)
                activity_date = activity_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    
    # Ensure activity is not in the future (unless it's a scheduled upcoming activity)
    if activity_date > base_time and not (is_recent_activity and not is_past_activity):
        minutes_ago = random.randint(1, 60)
        seconds_ago = random.randint(0, 59)
        activity_date = base_time - timedelta(minutes=minutes_ago, seconds=seconds_ago)
        activity_date = activity_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
        
        if activity_date > base_time:  # Double check for edge cases
            minutes_ago = random.randint(60, 1440)
            seconds_ago = random.randint(0, 59)
            activity_date = base_time - timedelta(minutes=minutes_ago, seconds=seconds_ago)
            activity_date = activity_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    
    return activity_date


def calculate_activity_date_modified(
    activity_date: datetime,
    base_time: datetime,
    is_recent_activity: bool = False,
    is_past_activity: bool = False,
    max_days_after: int = 180,
) -> datetime:
    """
    Calculates a modification date for an activity, ensuring it's after creation
    and not in the future.
    """
    if is_recent_activity and not is_past_activity:  # For upcoming activities, modified date is usually recent
        days_until_activity = (activity_date - base_time).days
        if days_until_activity > 0:
            hours_until_activity = days_until_activity * 24 + (activity_date.hour - base_time.hour)
            hours_offset = random.randint(1, min(hours_until_activity, 48))
            date_modified = base_time + timedelta(hours=hours_offset)
            if date_modified > activity_date:
                date_modified = activity_date - timedelta(hours=1)
        else:
            date_modified = base_time
    else:  # For past activities
        max_days_after_created = (base_time - activity_date).days
        
        if max_days_after_created > 0:
            max_update_days = min(max_days_after_created, max_days_after)
            if max_update_days > 0:
                days_after_created = random.randint(1, max_update_days)
                date_modified = activity_date + timedelta(days=days_after_created)
                
                mod_hour = random.randint(8, 17)
                mod_minute = random.randint(0, 59)
                mod_second = random.randint(0, 59)
                
                date_modified = date_modified.replace(hour=mod_hour, minute=mod_minute, second=mod_second, microsecond=0)
                
                if date_modified > base_time:
                    date_modified = base_time
            else:  # If activity is very recent, modify it very recently
                hours_offset = random.randint(1, 2)
                minutes_offset = random.randint(0, 59)
                date_modified = activity_date + timedelta(hours=hours_offset, minutes=minutes_offset)
                
                if date_modified > base_time:
                    date_modified = base_time
        else:  # If activity date is today
            hours_offset = random.randint(1, 2)
            minutes_offset = random.randint(0, 59)
            date_modified = activity_date + timedelta(hours=hours_offset, minutes=minutes_offset)
            
            if date_modified > base_time:
                date_modified = base_time
        
        if date_modified <= activity_date:  # Ensure modified is strictly after created
            date_modified = activity_date + timedelta(hours=1)
            if date_modified > base_time:
                date_modified = base_time
    
    return date_modified


def get_min_entity_date(
    entity_dates: dict[int, datetime],
    *entity_ids: int | None,
) -> datetime | None:
    """
    Retrieves the latest (most recent) creation date among a set of entities.
    This is useful for ensuring related activities don't predate their entities.
    """
    min_entity_date = None
    found_any = False
    
    for entity_id in entity_ids:
        if entity_id and entity_id in entity_dates:
            entity_date = entity_dates[entity_id]
            if not found_any or entity_date > min_entity_date:  # Use > for latest date
                min_entity_date = entity_date
                found_any = True
    
    if not found_any:
        # Fallback to a reasonable default if no entity dates are found
        return datetime.now() - timedelta(days=365) 
    
    return min_entity_date


def resolve_user_id(gen_user_id: int | None, generated_to_actual_user_id: dict, all_users: list[dict]) -> int:
    """
    Resolves a generated user ID to an actual user ID in the application.
    Falls back to the generated ID if not found in mapping, then checks all_users.
    Raises ValueError if the user ID cannot be resolved.
    """
    if not gen_user_id:
        raise ValueError("Cannot resolve user ID: gen_user_id is None or falsy")
    
    actual_user_id = generated_to_actual_user_id.get(gen_user_id)
    if actual_user_id:
        return actual_user_id
    
    for user in all_users:
        if user.get("userID") == gen_user_id:  # Assuming 'userID' is the key in actual user data
            return gen_user_id
    
    raise ValueError(f"Cannot resolve user ID: gen_user_id {gen_user_id} not found in mapping or user list")


def ensure_unique_datetime(
    date: datetime,
    used_dates: set,
    min_date: datetime | None = None,
    max_date: datetime | None = None,
    field_name: str = "",
    counters: dict | None = None
) -> datetime:
    """
    Ensures a datetime object is unique within a set of used dates by incrementing seconds.
    Adjusts date to be within min_date and max_date if provided.
    """
    if counters is None:
        counters = {}
    date = date.replace(microsecond=0)  # Normalize to seconds
    
    if max_date and date > max_date:
        date = max_date
    if min_date and date < min_date:
        date = min_date
    
    timestamp_str = date.isoformat()
    
    if timestamp_str not in used_dates:
        used_dates.add(timestamp_str)
        return date
    
    # If not unique, try to find a unique second
    if field_name and field_name in counters:
        counters[field_name] = counters.get(field_name, 0) + 1
    
    original_date = date
    max_attempts = 86400  # Max seconds in a day
    
    for attempt in range(1, max_attempts + 1):
        date = original_date + timedelta(seconds=attempt)
        
        if max_date and date > max_date:
            # If incrementing goes past max_date, try decrementing
            date = original_date - timedelta(seconds=attempt)
            if min_date and date < min_date:
                logger.warning(f"Cannot find unique timestamp for {field_name} in range")
                break
        
        timestamp_str = date.isoformat()
        
        if timestamp_str not in used_dates:
            used_dates.add(timestamp_str)
            return date
    
    # Fallback: if still not unique after many attempts, just add and log
    logger.warning(f"Could not find unique datetime for {field_name} after {max_attempts} attempts. Using potentially non-unique date.")
    used_dates.add(timestamp_str)
    return date
