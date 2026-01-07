import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from config.constants import DEFAULT_SITE_ID
from config.settings import settings
from utils import api_utils
from utils.database import get_connection
from utils.helpers import (
    safe_int,
    safe_strptime,
)
from common.logger import logger


def _normalize_loaded_json(data: Any, filepath: Path) -> list[dict[str, Any]]:
    """Normalizes loaded JSON data to a list of dictionaries."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    logger.warning(f"Unexpected data format in {filepath}")
    return []


def save_json_file(filepath: Path, data: list[dict[str, Any]]) -> bool:
    """Saves data to a JSON file."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    except Exception as e:
        logger.error(f"Error saving JSON file {filepath}: {e!s}")
        return False


def load_existing_data(filepath: Path) -> list[dict[str, Any]]:
    """Loads existing data from a JSON file."""
    if not filepath.exists():
        return []
    try:
        with filepath.open(encoding="utf-8") as f:
            data = json.load(f)
            return _normalize_loaded_json(data, filepath)
    except json.JSONDecodeError as e:
        if "UTF-8 BOM" not in str(e):
            logger.error(f"Error loading JSON file {filepath}: {e!s}")
            return []
        try:
            with filepath.open(encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception as bom_error:
            logger.error(f"Error loading JSON file {filepath} with utf-8-sig: {bom_error!s}")
            return []

        normalized = _normalize_loaded_json(data, filepath)
        save_json_file(filepath, normalized)
        return normalized
    except Exception as e:
        logger.error(f"Error loading JSON file {filepath}: {e!s}")
        return []


async def update_entity_dates(
    seeded_items: list[dict],
    original_data: list[dict],
    table_name: str,
    id_column: str,
    seeded_id_key: str,
    months_back: int = 36,
    name_key: str = "name",
    shuffle_dates: bool = False,
) -> None:
    """
    Updates the creation and modification dates for seeded entities directly in the database.
    This is often necessary as APIs might not expose these fields for update.
    """
    site_id = DEFAULT_SITE_ID  # TODO: Adjust site_id if your app uses multi-tenancy
    async with get_connection().cursor() as cursor:
        days_range = months_back * 30
        total_items = len(seeded_items)

        original_data_map = {}
        for orig_item in original_data:
            key_value = orig_item.get(name_key, "").strip()
            if key_value:
                original_data_map[key_value] = orig_item

        now = datetime.now()
        min_date = now - timedelta(days=days_range)

        if shuffle_dates:
            shuffled_indices = list(range(total_items))
            random.shuffle(shuffled_indices)
            index_mapping = {i: shuffled_indices[i] for i in range(total_items)}
        else:
            index_mapping = {i: i for i in range(total_items)}

        for idx, seeded in enumerate(seeded_items):
            app_id = seeded.get(seeded_id_key)
            if not app_id:
                continue

            date_idx = index_mapping[idx]

            original_item = seeded.get("original_data", {})

            if not original_item and idx < len(original_data):
                original_item = original_data[idx]

            if not original_item:
                temp_item = seeded.get("original_data", {})
                if temp_item:
                    seeded_key = temp_item.get(name_key, "").strip()
                    if seeded_key:
                        original_item = original_data_map.get(seeded_key, {})

            created_date = None
            modified_date = None

            if original_item:
                created_dt_str = original_item.get("createdDateTime", "")
                modified_dt_str = original_item.get("modifiedDateTime", "")

                if created_dt_str:
                    parsed_date = safe_strptime(created_dt_str, "%d-%m-%y %I:%M %p")
                    if parsed_date:
                        if parsed_date > now:
                            parsed_date = now - timedelta(days=1)

                        if total_items > 1:
                            linear_offset = (date_idx / (total_items - 1)) * days_range
                            variation_divisor = max(10, days_range // 10)
                            prime_variation = (date_idx * 17) % variation_divisor if variation_divisor > 0 else 0
                            days_offset = int(linear_offset + prime_variation)
                        else:
                            days_offset = days_range // 2

                        days_from_parsed = (parsed_date - min_date).days
                        days_from_parsed = max(0, min(days_from_parsed, days_range))

                        blended_days = int(0.3 * days_from_parsed + 0.7 * days_offset)
                        blended_days = max(0, min(blended_days, days_range))

                        created_date = min_date + timedelta(days=blended_days)

                        if created_date > now:
                            created_date = now - timedelta(days=1)

                        if created_date < min_date:
                            created_date = min_date

                        hours = 8 + ((date_idx * 7) % 10)
                        hours = min(17, max(8, hours))
                        minutes = (date_idx * 11) % 60
                        seconds = (date_idx * 19) % 60
                        microseconds = (date_idx * 23) % 1000000
                        created_date = created_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)

                        if created_date > now:
                            created_date = now - timedelta(days=1)
                            created_date = created_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)

                if modified_dt_str:
                    parsed_modified = safe_strptime(modified_dt_str, "%d-%m-%y %I:%M %p")
                    if parsed_modified:
                        modified_date = parsed_modified
                        if modified_date > datetime.now():
                            modified_date = datetime.now()

            if created_date is None:
                if total_items > 1:
                    linear_days = 1 + ((date_idx / (total_items - 1)) * (days_range - 1))
                    variation_divisor = max(10, days_range // 20)
                    prime_variation = (date_idx * 17) % variation_divisor if variation_divisor > 0 else 0
                    days_ago = int(linear_days + prime_variation)
                else:
                    days_ago = days_range // 2

                days_ago = max(1, min(days_ago, days_range))

                hours = 8 + ((date_idx * 7) % 10)
                hours = min(17, max(8, hours))
                minutes = (date_idx * 11) % 60
                seconds = (date_idx * 19) % 60
                microseconds = (date_idx * 23) % 1000000

                created_date = datetime.now() - timedelta(days=days_ago)
                created_date = created_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)

                if created_date > now:
                    created_date = now - timedelta(days=1)
                    created_date = created_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)

            if total_items > 1:
                linear_days = 1 + ((date_idx / (total_items - 1)) * 179)
                prime_variation = (date_idx * 13) % 7
                days_variation = int(linear_days + prime_variation)
            else:
                days_variation = 30

            days_variation = max(1, min(days_variation, 180))

            modified_date = created_date + timedelta(days=days_variation)

            mod_hours = 8 + ((created_date.hour + date_idx * 7) % 10)
            mod_hours = min(17, max(8, mod_hours))
            mod_minutes = (created_date.minute + (date_idx * 11)) % 60
            mod_seconds = (created_date.second + (date_idx * 19)) % 60
            mod_microseconds = (date_idx * 29) % 1000000
            modified_date = modified_date.replace(hour=mod_hours, minute=mod_minutes, second=mod_seconds, microsecond=mod_microseconds)

            if modified_date > now:
                max_days = (now - created_date).days
                if max_days > 0:
                    if total_items > 1:
                        linear_days = 1 + ((date_idx / (total_items - 1)) * (max_days - 1))
                        variation_divisor = max(1, min(7, max_days // 10))
                        prime_variation = (date_idx * 13) % variation_divisor if variation_divisor > 0 else 0
                        days_variation = int(linear_days + prime_variation)
                    else:
                        days_variation = max(1, max_days // 2)
                    days_variation = max(1, min(days_variation, max_days))
                    modified_date = created_date + timedelta(days=days_variation)
                    mod_hours = 8 + ((created_date.hour + date_idx * 7) % 10)
                    mod_hours = min(17, max(8, mod_hours))
                    mod_minutes = (created_date.minute + (date_idx * 11)) % 60
                    mod_seconds = (created_date.second + (date_idx * 19)) % 60
                    mod_microseconds = (date_idx * 29) % 1000000
                    if modified_date <= now:
                        modified_date = modified_date.replace(hour=mod_hours, minute=mod_minutes, second=mod_seconds, microsecond=mod_microseconds)
                    else:
                        mod_hours = min(created_date.hour + 1, 17)
                        modified_date = modified_date.replace(hour=mod_hours, minute=mod_minutes, second=mod_seconds, microsecond=mod_microseconds)
                        if modified_date > now:
                            modified_date = now
                            modified_date = modified_date.replace(second=mod_seconds, microsecond=mod_microseconds)
                else:
                    if created_date.date() == now.date():
                        hours_offset = 1 + (date_idx % 2)
                        mod_seconds = (date_idx * 19) % 60
                        mod_microseconds = (date_idx * 29) % 1000000
                        modified_date = created_date + timedelta(hours=hours_offset, seconds=mod_seconds)
                        modified_date = modified_date.replace(microsecond=mod_microseconds)
                        if modified_date > now:
                            modified_date = created_date + timedelta(seconds=mod_seconds)
                            modified_date = modified_date.replace(microsecond=mod_microseconds)
                            if modified_date > now:
                                modified_date = created_date
                    else:
                        modified_date = created_date

            if modified_date < created_date:
                modified_date = created_date + timedelta(days=1)
                modified_date = modified_date.replace(hour=mod_hours, minute=mod_minutes, second=mod_seconds, microsecond=mod_microseconds)

            if created_date > now:
                created_date = now - timedelta(days=1)
                hours = 8 + ((date_idx * 7) % 10)
                hours = min(17, max(8, hours))
                minutes = (date_idx * 11) % 60
                seconds = (date_idx * 19) % 60
                microseconds = (date_idx * 23) % 1000000
                created_date = created_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)
                if modified_date <= created_date:
                    modified_date = created_date + timedelta(days=1)
                    mod_hours = 8 + ((created_date.hour + date_idx * 7) % 10)
                    mod_hours = min(17, max(8, mod_hours))
                    mod_minutes = (created_date.minute + (date_idx * 11)) % 60
                    mod_seconds = (created_date.second + (date_idx * 19)) % 60
                    mod_microseconds = (date_idx * 29) % 1000000
                    modified_date = modified_date.replace(hour=mod_hours, minute=mod_minutes, second=mod_seconds, microsecond=mod_microseconds)
                if modified_date > now:
                    modified_date = now

            if modified_date > now:
                max_modified = min(now, created_date + timedelta(days=1))
                modified_date = max_modified
                if modified_date < created_date:
                    modified_date = created_date

            # TODO: Update your database table and columns for date_created and date_modified
            await cursor.execute(
                f"""
                    UPDATE {table_name} 
                    SET date_created = %s, date_modified = %s
                    WHERE {id_column} = %s AND site_id = %s
                """,
                (created_date, modified_date, app_id, site_id),
            )

        await get_connection().commit()


async def update_entity_owners(
    seeded_items: list[dict],
    table_name: str,
    id_column: str,
    seeded_id_key: str,
) -> None:
    """
    Updates the owner/creator for seeded entities directly in the database.
    This is often necessary as APIs might not expose these fields for update.
    """
    
    all_users = await get_all_users()  # TODO: Implement get_all_users for your app
    available_users = [u for u in all_users if u.get("userID") != 1] or all_users  # Exclude admin user if ID 1 is admin
    user_ids = [u.get("userID") for u in available_users if u.get("userID")]
    
    # TODO: Define which tables support API-based owner updates
    api_supported_tables = {"example_entity_table"}  # Example
    
    if table_name in api_supported_tables:
        updated_count = 0
        
        async with api_utils.app_session():  # Use generic app_session
            
            for idx, seeded in enumerate(seeded_items):
                app_id = seeded.get(seeded_id_key)
                if not app_id:
                    continue
                
                try:
                    app_id_int = int(app_id)
                except (ValueError, TypeError):
                    continue
                
                owner_id = user_ids[idx % len(user_ids)]
                
                # TODO: Call your specific API update function for the entity type
                # Example:
                # if table_name == "example_entity_table":
                #     try:
                #         success = await api_utils.update_example_entity_owner(app_id_int, owner_id)
                #         if success:
                #             updated_count += 1
                #     except Exception as e:
                #         logger.debug(f"Error updating owner for {table_name} {app_id_int}: {e}")
        
        logger.info(f"{table_name.capitalize()} owners updated via API: {updated_count} succeeded")
    else:
        async with get_connection().cursor() as cursor:
            site_id = DEFAULT_SITE_ID  # TODO: Adjust site_id if your app uses multi-tenancy
            len(seeded_items)
            owner_column = "created_by" if table_name == "saved_list" else "owner"  # TODO: Adjust owner column name
            
            for idx, seeded in enumerate(seeded_items):
                app_id = seeded.get(seeded_id_key)
                
                owner_id = user_ids[idx % len(user_ids)]
                
                # TODO: Update your database table and columns for owner
                await cursor.execute(
                    f"""
                        UPDATE {table_name} 
                        SET {owner_column} = %s 
                        WHERE {id_column} = %s AND site_id = %s
                    """,
                    (owner_id, app_id, site_id),
                )
                
            await get_connection().commit()


def load_user_ids_and_emails(users_data: list[dict] | None = None) -> tuple[list[int], list[str]]:
    """Loads user IDs and emails from provided user data or default settings."""
    if users_data:
        user_emails = [user.get("email", "") for user in users_data if user.get("email") and "@" in user.get("email", "")]
        user_ids = list(range(1, len(users_data) + 1))
        if not user_emails:
            user_emails = [settings.APP_ADMIN_EMAIL]
        return user_ids, user_emails
    return [1], [settings.APP_ADMIN_EMAIL]


async def get_all_users() -> list[dict[str, Any]]:
    """
    Fetches all users from the application.
    TODO: Implement this function to retrieve users from your application's API or database.
    """
    # Example: Fetching from a generic API endpoint
    # async with api_utils.app_session():
    #     all_users_data = await api_utils.get_all_items(AppDataItemType.USER)  # Assuming a USER data item type
    #     users = []
    #     for user in all_users_data:
    #         users.append({
    #             "userID": user.get("id"),
    #             "username": user.get("username"),
    #             "email": user.get("email"),
    #             "firstName": user.get("first_name"),
    #             "lastName": user.get("last_name"),
    #             "accessLevel": user.get("access_level"),
    #         })
    #     return users
    
    # Placeholder: Return a default admin user if no implementation
    logger.warning("get_all_users is not implemented. Returning default admin user.")
    return [{
        "userID": 1,
        "username": settings.APP_ADMIN_EMAIL,
        "email": settings.APP_ADMIN_EMAIL,
        "firstName": "Admin",
        "lastName": "User",
        "accessLevel": 400,
    }]


async def fetch_user_ids() -> list[int]:
    """
    Fetches user IDs from the database.
    TODO: Implement this function to retrieve user IDs from your application's database.
    """
    conn = get_connection()
    async with conn.cursor() as cursor:
        # TODO: Adjust table and column names for your user table
        await cursor.execute("SELECT user_id FROM user WHERE user_id != 1 ORDER BY user_id")
        results = await cursor.fetchall()
        return [row[0] for row in results] if results else []


def build_company_id_mapping(companies_list: list[dict]) -> dict[int, int]:
    """
    Builds a mapping from generated company IDs to actual company IDs in the application.
    TODO: Customize this function to match your application's company entity and API/DB.
    """
    generated_to_actual = {}
    # Example: Fetching companies from API and mapping by name
    # async with api_utils.app_session():
    #     api_companies = await api_utils.get_all_items(AppDataItemType.COMPANY)  # Assuming a COMPANY data item type
    #     company_name_to_id = {item.get("name").strip(): item.get("companyID") for item in api_companies if item.get("companyID") and item.get("name")}
    
    # Placeholder: Simple sequential mapping if no API/DB interaction
    company_name_to_id = {f"Company {i+1}": i+1 for i in range(len(companies_list))}  # Example
    
    if companies_list:
        for idx, gen_company in enumerate(companies_list):
            gen_company_id = idx + 1
            company_name = gen_company.get("name", "").strip()
            actual_company_id = company_name_to_id.get(company_name)
            if actual_company_id:
                generated_to_actual[gen_company_id] = actual_company_id
    
    return generated_to_actual
